"""M04: Thermal Treatment — Carbonization and heat treatment.

Governing equations:
  Pyrolysis kinetics (nth order): dα/dt = A·exp(-Ea/(R·T))·(1-α)^n
  Heat conduction (Fourier): ρ·Cp·∂T/∂t = ∇·(k·∇T) + Q_reaction
  Crystallinity (Avrami): X(t) = 1 - exp(-k·t^n)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import THERMAL, R_GAS, ELECTRIFICATION_OPTIONS, ENERGY_COSTS


def pyrolysis_rate(T_C: float, alpha: float) -> float:
    """Compute pyrolysis rate dα/dt [1/s].

    dα/dt = A·exp(-Ea/(R·T))·(1-α)^n

    Parameters
    ----------
    T_C : float
        Temperature [°C].
    alpha : float
        Conversion fraction [0-1].

    Returns
    -------
    float
        Rate [1/s].
    """
    if alpha >= 1.0:
        return 0.0
    T_K = T_C + 273.15
    A = THERMAL["pyrolysis_A_s"]
    Ea = THERMAL["pyrolysis_Ea_kJ_mol"] * 1000.0
    n = THERMAL["pyrolysis_n"]
    return A * np.exp(-Ea / (R_GAS * T_K)) * (1.0 - alpha) ** n


def pyrolysis_kinetics(
    T_profile_C: List[float],
    dt_s: float = 1.0,
) -> Dict:
    """Simulate volatile removal during programmed temperature profile.

    Parameters
    ----------
    T_profile_C : list of float
        Temperature at each time step [°C].
    dt_s : float
        Time step [s].

    Returns
    -------
    dict
        {"time_s": array, "T_C": array, "alpha": array, "rate": array}
    """
    n_steps = len(T_profile_C)
    alpha = np.zeros(n_steps)
    rate = np.zeros(n_steps)

    for i in range(1, n_steps):
        r = pyrolysis_rate(T_profile_C[i - 1], alpha[i - 1])
        rate[i - 1] = r
        alpha[i] = min(alpha[i - 1] + r * dt_s, 1.0)

    rate[-1] = pyrolysis_rate(T_profile_C[-1], alpha[-1])
    time_s = np.arange(n_steps) * dt_s

    return {
        "time_s": time_s,
        "T_C": np.array(T_profile_C),
        "alpha": alpha,
        "rate": rate,
    }


def generate_T_profile(
    T_max_C: float,
    heating_rate_C_min: float,
    hold_time_s: float,
    T_start_C: float = 25.0,
    dt_s: float = 60.0,
) -> List[float]:
    """Generate a ramp-hold temperature profile.

    Parameters
    ----------
    T_max_C : float
        Maximum temperature [°C].
    heating_rate_C_min : float
        Heating rate [°C/min].
    hold_time_s : float
        Hold time at T_max [s].
    T_start_C : float
        Starting temperature [°C].
    dt_s : float
        Time step [s].

    Returns
    -------
    list of float
        Temperature at each time step.
    """
    heating_rate_C_s = heating_rate_C_min / 60.0
    ramp_time_s = (T_max_C - T_start_C) / heating_rate_C_s if heating_rate_C_s > 0 else 0
    total_time_s = ramp_time_s + hold_time_s

    profile = []
    t = 0.0
    while t <= total_time_s:
        if t <= ramp_time_s:
            T = T_start_C + heating_rate_C_s * t
        else:
            T = T_max_C
        profile.append(T)
        t += dt_s

    return profile


def crystallinity_evolution(T_C: float, t_s: float) -> float:
    """Compute carbon crystallinity via Avrami equation.

    X(t) = 1 - exp(-k(T)·t^n)
    k(T) = k0·exp(-Ea/(R·T))

    Parameters
    ----------
    T_C : float
        Temperature [°C].
    t_s : float
        Time [s].

    Returns
    -------
    float
        Crystallinity fraction X ∈ [0, 1].
    """
    if t_s <= 0 or T_C <= 0:
        return 0.0
    T_K = T_C + 273.15
    k0 = THERMAL["avrami_k0_s"]
    Ea = THERMAL["avrami_Ea_kJ_mol"] * 1000.0
    n = THERMAL["avrami_n"]

    k = k0 * np.exp(-Ea / (R_GAS * T_K))
    # Guard against overflow
    exponent = k * t_s ** n
    if exponent > 700:
        return 1.0
    return 1.0 - np.exp(-exponent)


def heat_conduction_1d(
    T_init_C: float,
    T_surface_C: float,
    radius_m: float,
    duration_s: float,
    n_nodes: int = 50,
    dt_s: float = 0.1,
) -> Dict:
    """1D radial heat conduction in a spherical carbon particle (Fourier).

    Parameters
    ----------
    T_init_C : float
        Initial uniform temperature [°C].
    T_surface_C : float
        Surface temperature (boundary) [°C].
    radius_m : float
        Particle radius [m].
    duration_s : float
        Simulation time [s].
    n_nodes : int
        Number of radial nodes.
    dt_s : float
        Time step [s].

    Returns
    -------
    dict
        {"r_m": array, "T_final_C": array, "T_center_C": float}
    """
    rho = THERMAL["carbon_density_kg_m3"]
    Cp = THERMAL["carbon_Cp_J_kgK"]
    k = THERMAL["carbon_k_W_mK"]
    alpha_diff = k / (rho * Cp)  # thermal diffusivity [m²/s]

    dr = radius_m / n_nodes
    # Stability: dt <= dr²/(2·α)
    dt_stable = 0.4 * dr ** 2 / alpha_diff
    dt_s = min(dt_s, dt_stable)

    r = np.linspace(0, radius_m, n_nodes + 1)
    T = np.full(n_nodes + 1, T_init_C, dtype=float)
    T[-1] = T_surface_C  # boundary

    n_steps = int(duration_s / dt_s)
    for _ in range(n_steps):
        T_new = T.copy()
        for j in range(1, n_nodes):
            if r[j] > 0:
                laplacian = (
                    (T[j + 1] - 2 * T[j] + T[j - 1]) / dr ** 2
                    + (2.0 / r[j]) * (T[j + 1] - T[j - 1]) / (2.0 * dr)
                )
            else:
                # Center: symmetry, use L'Hôpital
                laplacian = 6.0 * (T[1] - T[0]) / dr ** 2
            T_new[j] = T[j] + alpha_diff * dt_s * laplacian
        # Center BC (symmetry): dT/dr = 0
        T_new[0] = T_new[1]
        T_new[-1] = T_surface_C
        T = T_new

    return {"r_m": r, "T_final_C": T, "T_center_C": float(T[0])}


def thermal_treatment(
    mass_kg: float,
    T_max_C: float,
    heating_rate_C_min: float = 5.0,
    hold_time_s: float = 3600.0,
    volatile_pct: float = 10.0,
) -> Dict:
    """Full thermal treatment simulation.

    Parameters
    ----------
    mass_kg : float
        Carbon mass [kg].
    T_max_C : float
        Maximum temperature [°C].
    heating_rate_C_min : float
        Heating rate [°C/min].
    hold_time_s : float
        Hold time at T_max [s].
    volatile_pct : float
        Initial volatile content [%].

    Returns
    -------
    dict
        {"final_volatile_pct": float, "crystallinity": float,
         "mass_loss_kg": float, "energy_kWh": float}
    """
    profile = generate_T_profile(T_max_C, heating_rate_C_min, hold_time_s, dt_s=60.0)
    kinetics = pyrolysis_kinetics(profile, dt_s=60.0)
    final_alpha = float(kinetics["alpha"][-1])

    # Volatile removal
    volatile_removed_pct = volatile_pct * final_alpha
    final_volatile_pct = volatile_pct - volatile_removed_pct
    mass_loss = mass_kg * volatile_removed_pct / 100.0

    # Crystallinity at hold conditions
    crystallinity = crystallinity_evolution(T_max_C, hold_time_s)

    # Energy: heating + holding
    Cp = THERMAL["carbon_Cp_J_kgK"]
    Q_heat = mass_kg * Cp * (T_max_C - 25.0)  # J
    # Hold energy (losses): ~5% of heating energy per hour
    total_time_h = (len(profile) * 60.0) / 3600.0
    Q_hold = Q_heat * 0.05 * total_time_h
    energy_kWh = (Q_heat + Q_hold) / 3.6e6

    return {
        "final_volatile_pct": final_volatile_pct,
        "volatile_removed_pct": volatile_removed_pct,
        "crystallinity": crystallinity,
        "mass_loss_kg": mass_loss,
        "energy_kWh": energy_kWh,
        "total_time_h": total_time_h,
        "final_alpha": final_alpha,
    }


def microwave_vs_conventional(
    mass_kg: float,
    T_target_C: float,
    region: str = "saudi_arabia",
) -> Dict:
    """Compare microwave (electric) vs conventional (gas) thermal treatment.

    Parameters
    ----------
    mass_kg : float
        Mass [kg].
    T_target_C : float
        Target temperature [°C].
    region : str
        Energy cost region.

    Returns
    -------
    dict
        Comparison of energy and cost.
    """
    conv = thermal_treatment(mass_kg, T_target_C)
    ratio = ELECTRIFICATION_OPTIONS["thermal_treatment"]["energy_ratio"]
    elec_energy = conv["energy_kWh"] * ratio

    cost_kwh = ENERGY_COSTS.get(region, 0.048)

    return {
        "conventional": {
            "energy_kWh": conv["energy_kWh"],
            "cost_usd": conv["energy_kWh"] * cost_kwh,
            "method": "gas_fired",
        },
        "microwave": {
            "energy_kWh": elec_energy,
            "cost_usd": elec_energy * cost_kwh,
            "method": "microwave",
        },
        "energy_saving_pct": (1 - ratio) * 100,
        "region": region,
    }
