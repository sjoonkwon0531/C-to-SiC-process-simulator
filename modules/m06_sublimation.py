"""M06: Sublimation Purification — 5N+ purity via vacuum sublimation.

Governing equations:
  Hertz-Knudsen: J = α·(P_eq - P) / sqrt(2π·m·k·T)
  SiC vapor species: Si(g), Si₂C(g), SiC₂(g) with T-dependent partial pressures
  Burton-Prim-Slichter: k_eff = k₀ / (k₀ + (1-k₀)·exp(-v·δ/D))
  Mass loss vs purity trade-off via multi-pass sublimation
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SUBLIMATION, R_GAS, BOLTZMANN


def hertz_knudsen_rate(T_C: float, P_eq: float, P_actual: float,
                       molar_mass: float) -> float:
    """Sublimation flux via Hertz-Knudsen equation [mol/(m²·s)].

    J = α·(P_eq - P_actual) / sqrt(2π·M·R·T)

    Parameters
    ----------
    T_C : float
        Temperature [°C].
    P_eq : float
        Equilibrium vapor pressure [Pa].
    P_actual : float
        Actual pressure above surface [Pa].
    molar_mass : float
        Molar mass [g/mol].

    Returns
    -------
    float
        Sublimation flux [mol/(m²·s)].
    """
    if P_eq <= P_actual:
        return 0.0
    T_K = T_C + 273.15
    alpha = SUBLIMATION["alpha_evap"]
    M_kg = molar_mass / 1000.0  # kg/mol
    denom = np.sqrt(2 * np.pi * M_kg * R_GAS * T_K)
    return alpha * (P_eq - P_actual) / denom


def sic_vapor_species(T_C: float) -> Dict[str, float]:
    """Partial pressures of SiC vapor species [Pa].

    ln(P/Pa) = A - B/T(K) for each species.

    Parameters
    ----------
    T_C : float
        Temperature [°C].

    Returns
    -------
    dict
        {"Si": P_Pa, "Si2C": P_Pa, "SiC2": P_Pa, "total": P_Pa}
    """
    T_K = T_C + 273.15
    result = {}
    total = 0.0
    for species, data in SUBLIMATION["vapor_species"].items():
        lnP = data["A"] - data["B"] / T_K
        P = np.exp(lnP)
        result[species] = P
        total += P
    result["total"] = total
    return result


def impurity_partition(impurity: str, T_C: float, growth_rate_mm_h: float) -> float:
    """Effective partition coefficient via Burton-Prim-Slichter.

    k_eff = k₀ / (k₀ + (1 - k₀)·exp(-v·δ/D))

    Parameters
    ----------
    impurity : str
        Impurity element symbol.
    T_C : float
        Temperature [°C].
    growth_rate_mm_h : float
        Growth/sublimation rate [mm/h].

    Returns
    -------
    float
        Effective partition coefficient k_eff.
    """
    k0 = SUBLIMATION["impurity_k0"].get(impurity, 0.01)
    v = growth_rate_mm_h / 1000.0 / 3600.0  # m/s
    delta = SUBLIMATION["delta_BPS_m"]
    D = SUBLIMATION["D_liquid_m2_s"]

    # BPS equation
    exponent = -v * delta / D
    k_eff = k0 / (k0 + (1 - k0) * np.exp(exponent))
    return k_eff


def sublimation_purify(impurities: Dict[str, float], T_C: float = 2200,
                       duration_h: float = 10.0, n_passes: int = 3) -> Dict:
    """Multi-pass sublimation purification.

    Parameters
    ----------
    impurities : dict
        {element: ppm} initial impurity concentrations.
    T_C : float
        Sublimation temperature [°C].
    duration_h : float
        Duration per pass [hours].
    n_passes : int
        Number of sublimation passes.

    Returns
    -------
    dict
        {"initial_ppm": dict, "final_ppm": dict, "total_initial_ppm": float,
         "total_final_ppm": float, "purity_grade": str, "mass_loss_fraction": float,
         "n_passes": int}
    """
    # Estimate growth rate from vapor pressure
    vapor = sic_vapor_species(T_C)
    # Approximate growth rate: ~0.2 mm/h at 2200°C
    growth_rate = 0.1 + 0.1 * (T_C - 2000) / 200.0  # rough linear

    current = dict(impurities)
    for _ in range(n_passes):
        new = {}
        for elem, conc in current.items():
            k_eff = impurity_partition(elem, T_C, growth_rate)
            new[elem] = conc * k_eff
        current = new

    total_initial = sum(impurities.values())
    total_final = sum(current.values())

    # Purity grade
    if total_final < 1:
        grade = "6N"
    elif total_final < 10:
        grade = "5N"
    elif total_final < 100:
        grade = "4N"
    elif total_final < 1000:
        grade = "3N"
    else:
        grade = "2N"

    # Mass loss: each pass loses ~5-15% depending on T
    loss_per_pass = 0.05 + 0.05 * (T_C - 2000) / 400.0
    mass_loss = 1 - (1 - loss_per_pass) ** n_passes

    return {
        "initial_ppm": dict(impurities),
        "final_ppm": current,
        "total_initial_ppm": total_initial,
        "total_final_ppm": total_final,
        "purity_grade": grade,
        "mass_loss_fraction": mass_loss,
        "n_passes": n_passes,
    }


def purity_vs_mass_loss(impurities: Dict[str, float],
                        T_range: Tuple[float, float] = (2000, 2400),
                        duration_range: Tuple[float, float] = (5, 20)) -> Dict:
    """Pareto analysis of purity vs mass loss.

    Parameters
    ----------
    impurities : dict
        Initial impurity levels {element: ppm}.
    T_range : tuple
        (T_min, T_max) in °C.
    duration_range : tuple
        (dur_min, dur_max) in hours.

    Returns
    -------
    dict
        {"temperatures": list, "durations": list, "purities_ppm": list,
         "mass_losses": list, "pareto_front": list of indices}
    """
    temps = np.linspace(T_range[0], T_range[1], 8)
    durs = np.linspace(duration_range[0], duration_range[1], 6)

    results_T, results_d, results_p, results_m = [], [], [], []

    for T in temps:
        for d in durs:
            res = sublimation_purify(impurities, T, d, n_passes=3)
            results_T.append(float(T))
            results_d.append(float(d))
            results_p.append(res["total_final_ppm"])
            results_m.append(res["mass_loss_fraction"])

    # Simple Pareto front: non-dominated points (min purity, min loss)
    pareto = []
    for i in range(len(results_p)):
        dominated = False
        for j in range(len(results_p)):
            if i != j and results_p[j] <= results_p[i] and results_m[j] <= results_m[i]:
                if results_p[j] < results_p[i] or results_m[j] < results_m[i]:
                    dominated = True
                    break
        if not dominated:
            pareto.append(i)

    return {
        "temperatures": results_T,
        "durations": results_d,
        "purities_ppm": results_p,
        "mass_losses": results_m,
        "pareto_front": pareto,
    }


def energy_consumption(T_C: float, mass_kg: float, duration_h: float) -> float:
    """Energy consumption for sublimation [kWh].

    Parameters
    ----------
    T_C : float
        Temperature [°C].
    mass_kg : float
        Charge mass [kg].
    duration_h : float
        Duration [hours].

    Returns
    -------
    float
        Energy [kWh].
    """
    base = SUBLIMATION["energy_kWh_per_kg_h"]
    # Scale with T⁴ (radiation-dominated) relative to 2200°C baseline
    T_ratio = ((T_C + 273.15) / (2200 + 273.15)) ** 4
    return base * T_ratio * mass_kg * duration_h
