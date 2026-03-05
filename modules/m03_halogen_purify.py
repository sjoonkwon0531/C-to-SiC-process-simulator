"""M03: Halogen Purification — High-temperature gas-solid reaction purification.

Governing equations:
  Chloride formation:  M(s) + n/2 Cl₂(g) → MCl_n(g),  ΔG(T) = ΔH - T·ΔS
  Reaction rate:  r_i = A_i·exp(-Ea_i/(R·T))·P_Cl2^α·(1-X_i)^β
  Mass transfer:  1/k_overall = 1/k_ext + 1/k_pore
  Energy balance: ρ·Cp·dT/dt = Q_elec - Σ(r_i·ΔH_i) - h·A·(T-T_amb)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import HALOGEN_PURIFY, METAL_CHLORIDE_THERMO, R_GAS, ENERGY_COSTS


def gibbs_free_energy(metal: str, T_C: float) -> float:
    """Compute ΔG(T) for metal chloride formation [kJ/mol].

    ΔG = ΔH - T·ΔS (linear approximation).

    Parameters
    ----------
    metal : str
        Element symbol (e.g., 'Fe', 'Al').
    T_C : float
        Temperature [°C].

    Returns
    -------
    float
        ΔG [kJ/mol]. Negative means spontaneous.

    Raises
    ------
    ValueError
        If metal not in thermodynamic database.
    """
    if metal not in METAL_CHLORIDE_THERMO:
        raise ValueError(f"No thermodynamic data for '{metal}'.")
    data = METAL_CHLORIDE_THERMO[metal]
    T_K = T_C + 273.15
    return data["delta_H_kJ"] - T_K * data["delta_S_kJ_K"]


def reaction_rate(
    impurity: str,
    T_C: float,
    P_Cl2_atm: float,
    X: float,
) -> float:
    """Compute reaction rate for impurity removal [1/s].

    r = A·exp(-Ea/(R·T))·P_Cl2^α·(1-X)^β

    Parameters
    ----------
    impurity : str
        Element symbol.
    T_C : float
        Temperature [°C].
    P_Cl2_atm : float
        Chlorine partial pressure [atm].
    X : float
        Fractional conversion [0-1].

    Returns
    -------
    float
        Reaction rate [1/s].
    """
    if impurity not in METAL_CHLORIDE_THERMO:
        return 0.0
    data = METAL_CHLORIDE_THERMO[impurity]
    T_K = T_C + 273.15
    A = data["A_s"]
    Ea = data["Ea_kJ_mol"] * 1000.0  # to J/mol
    alpha = data["alpha"]
    beta = data["beta"]

    k = A * np.exp(-Ea / (R_GAS * T_K))
    r = k * (P_Cl2_atm ** alpha) * ((1.0 - X) ** beta)
    return float(r)


def _integrate_conversion(
    impurity: str,
    T_C: float,
    P_Cl2_atm: float,
    duration_s: float,
    dt: float = 1.0,
) -> float:
    """Integrate conversion X over time using Euler method.

    dX/dt = r(T, P_Cl2, X)

    Returns final conversion X.
    """
    X = 0.0
    t = 0.0
    while t < duration_s:
        step = min(dt, duration_s - t)
        r = reaction_rate(impurity, T_C, P_Cl2_atm, X)
        X += r * step
        X = min(X, 1.0)
        t += step
        if X >= 0.9999:
            break
    return X


def purify_halogen(
    impurities: Dict[str, float],
    T_C: float,
    P_Cl2_atm: float = 1.0,
    flow_rate_L_min: float = 2.0,
    duration_s: float = 3600.0,
    gas_type: str = "Cl2",
) -> Dict:
    """Simulate halogen purification of impurities.

    Parameters
    ----------
    impurities : dict
        {element: ppm} input concentrations.
    T_C : float
        Temperature [°C].
    P_Cl2_atm : float
        Halogen partial pressure [atm].
    flow_rate_L_min : float
        Gas flow rate [L/min].
    duration_s : float
        Treatment duration [s].
    gas_type : str
        'Cl2' or 'HCl_gas'.

    Returns
    -------
    dict
        {"residual_impurities": dict, "total_residual_ppm": float,
         "conversions": dict, "thermodynamic_feasibility": dict}
    """
    if gas_type not in HALOGEN_PURIFY:
        raise ValueError(f"Unknown gas type '{gas_type}'.")

    residual = {}
    conversions = {}
    feasibility = {}

    for element, ppm in impurities.items():
        if element in METAL_CHLORIDE_THERMO:
            dG = gibbs_free_energy(element, T_C)
            feasibility[element] = {"delta_G_kJ_mol": dG, "spontaneous": dG < 0}

            if dG < 0:  # thermodynamically favorable
                X = _integrate_conversion(element, T_C, P_Cl2_atm, duration_s)
                # Cap at config removal efficiency
                cfg = HALOGEN_PURIFY[gas_type]
                eff_key = [k for k in cfg if k.startswith("removal_eff")]
                if eff_key:
                    max_eff = cfg[eff_key[0]].get(element, 1.0)
                    X = min(X, max_eff)
                conversions[element] = X
                residual[element] = ppm * (1.0 - X)
            else:
                conversions[element] = 0.0
                residual[element] = ppm
        else:
            residual[element] = ppm
            conversions[element] = 0.0

    return {
        "residual_impurities": residual,
        "total_residual_ppm": sum(residual.values()),
        "conversions": conversions,
        "thermodynamic_feasibility": feasibility,
    }


def energy_balance(
    T_target_C: float,
    mass_kg: float,
    insulation_factor: float = 0.5,
    duration_s: float = 3600.0,
) -> Dict[str, float]:
    """Compute energy requirement for halogen purification furnace.

    Q = m·Cp·ΔT + Q_loss
    Q_loss = h·A·(T - T_amb)·t · insulation_factor

    Parameters
    ----------
    T_target_C : float
        Target temperature [°C].
    mass_kg : float
        Charge mass [kg].
    insulation_factor : float
        0=perfect insulation, 1=no insulation.
    duration_s : float
        Duration [s].

    Returns
    -------
    dict
        {"Q_heating_kWh": float, "Q_loss_kWh": float, "Q_total_kWh": float}
    """
    Cp = 1200.0  # J/(kg·K) for carbon material
    T_amb = 25.0
    delta_T = T_target_C - T_amb

    Q_heat = mass_kg * Cp * delta_T  # J
    # Loss: assume surface area ~0.5 m² per kg^(2/3), h=10 W/(m²·K)
    A_surface = 0.5 * mass_kg ** (2.0 / 3.0)  # m²
    h_conv = 10.0  # W/(m²·K)
    Q_loss = h_conv * A_surface * delta_T * duration_s * insulation_factor  # J

    Q_total = Q_heat + Q_loss
    return {
        "Q_heating_kWh": Q_heat / 3.6e6,
        "Q_loss_kWh": Q_loss / 3.6e6,
        "Q_total_kWh": Q_total / 3.6e6,
    }


def optimize_T_profile(
    impurities: Dict[str, float],
    target_total_ppm: float,
    P_Cl2_atm: float = 1.0,
    duration_s: float = 3600.0,
    T_range_C: Tuple[float, float] = (1500, 2000),
    n_points: int = 11,
) -> Dict:
    """Find optimal temperature for halogen purification.

    Scans temperature range and returns results at each point.

    Parameters
    ----------
    impurities : dict
    target_total_ppm : float
    P_Cl2_atm : float
    duration_s : float
    T_range_C : tuple
    n_points : int

    Returns
    -------
    dict
        {"optimal_T_C": float, "min_residual_ppm": float,
         "profile": list of {T_C, total_residual_ppm, energy_kWh}}
    """
    temps = np.linspace(T_range_C[0], T_range_C[1], n_points)
    profile = []
    best_T = temps[0]
    best_residual = float("inf")

    for T in temps:
        result = purify_halogen(impurities, float(T), P_Cl2_atm, 2.0, duration_s)
        energy = energy_balance(float(T), 1.0, 0.5, duration_s)
        total = result["total_residual_ppm"]
        profile.append({
            "T_C": float(T),
            "total_residual_ppm": total,
            "energy_kWh": energy["Q_total_kWh"],
        })
        if total < best_residual:
            best_residual = total
            best_T = float(T)

    return {
        "optimal_T_C": best_T,
        "min_residual_ppm": best_residual,
        "meets_target": best_residual <= target_total_ppm,
        "profile": profile,
    }
