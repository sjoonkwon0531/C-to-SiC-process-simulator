"""M07: PVT Crystal Growth — Physical Vapor Transport for 4H-SiC boules.

Governing equations:
  Stefan-Maxwell diffusion: ∂y_i/∂z = Σ_j (y_i·N_j - y_j·N_i)/(c·D_ij)
  Radiation heat transfer: Q_rad = ε·σ·(T_source⁴ - T_seed⁴)
  Growth rate: v ∝ ΔT, inversely affected by P_Ar
  Thermal stress: σ = E·α·ΔT/(1-ν)
  Defect density: BPD ∝ v^1.5 · σ^2
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PVT_GROWTH, SUBLIMATION, R_GAS, ENERGY_COSTS


def stefan_maxwell_flux(T_source: float, T_seed: float,
                        P_total: float, distance_m: float) -> Dict[str, float]:
    """Vapor species flux via simplified Stefan-Maxwell diffusion [mol/(m²·s)].

    Parameters
    ----------
    T_source : float
        Source temperature [°C].
    T_seed : float
        Seed temperature [°C].
    P_total : float
        Total pressure [mbar].
    distance_m : float
        Source-seed distance [m].

    Returns
    -------
    dict
        {"Si": flux, "Si2C": flux, "SiC2": flux, "total": flux} [mol/(m²·s)]
    """
    T_s_K = T_source + 273.15
    T_d_K = T_seed + 273.15
    T_avg_K = (T_s_K + T_d_K) / 2.0
    P_Pa = P_total * 100.0  # mbar → Pa

    # Vapor pressures at source and seed
    from modules.m06_sublimation import sic_vapor_species
    P_source = sic_vapor_species(T_source)
    P_seed = sic_vapor_species(T_seed)

    result = {}
    total = 0.0
    for species in ["Si", "Si2C", "SiC2"]:
        D_key = f"{species}_Ar"
        D = PVT_GROWTH["D_binary_m2_s"].get(D_key, 3e-4)
        # Scale D with T^1.75 / P
        D_scaled = D * (T_avg_K / (2200 + 273.15)) ** 1.75 * (20.0 * 100.0 / P_Pa)
        M = SUBLIMATION["vapor_species"][species]["molar_mass"] / 1000.0  # kg/mol
        dP = P_source[species] - P_seed[species]
        # Fick-type approximation from Stefan-Maxwell
        flux = D_scaled * dP / (R_GAS * T_avg_K * distance_m)
        result[species] = max(flux, 0.0)
        total += result[species]
    result["total"] = total
    return result


def growth_rate(T_source: float, T_seed: float,
                P_Ar: float = 20.0, distance_m: float = 0.03) -> float:
    """Crystal growth rate [mm/h].

    Parameters
    ----------
    T_source : float
        Source temperature [°C].
    T_seed : float
        Seed crystal temperature [°C].
    P_Ar : float
        Argon pressure [mbar].
    distance_m : float
        Source-to-seed distance [m].

    Returns
    -------
    float
        Growth rate [mm/h].
    """
    delta_T = T_source - T_seed
    if delta_T <= 0:
        return 0.0

    # Base: v = prefactor * ΔT + P_factor * (P - 20)
    v = (PVT_GROWTH["growth_rate_prefactor"] * delta_T
         + PVT_GROWTH["growth_rate_P_factor"] * (P_Ar - 20.0))

    # Distance correction (shorter = faster transport)
    v *= (0.03 / distance_m) if distance_m > 0 else 1.0

    return max(v, 0.0)


def thermal_stress(T_profile: Tuple[float, float], crystal_diameter_mm: float,
                   thickness_mm: float) -> float:
    """Thermal stress in crystal [MPa].

    σ = E·α·ΔT / (1 - ν)

    Parameters
    ----------
    T_profile : tuple
        (T_center_C, T_edge_C) radial temperature profile.
    crystal_diameter_mm : float
        Crystal diameter [mm].
    thickness_mm : float
        Crystal thickness [mm].

    Returns
    -------
    float
        Thermal stress [MPa].
    """
    delta_T = abs(T_profile[0] - T_profile[1])
    E = PVT_GROWTH["E_Young_GPa"] * 1e3  # MPa
    alpha = PVT_GROWTH["CTE_K"]
    nu = PVT_GROWTH["poisson_ratio"]
    sigma = E * alpha * delta_T / (1 - nu)
    return sigma


def defect_density(growth_rate_mm_h: float, thermal_stress_MPa: float,
                   T_gradient_K_cm: float = 10.0) -> Dict[str, float]:
    """Defect density estimation [/cm²].

    BPD = BPD_base · (v/0.2)^1.5 · (σ/10)^2
    TSD = TSD_ratio · BPD

    Parameters
    ----------
    growth_rate_mm_h : float
        Growth rate [mm/h].
    thermal_stress_MPa : float
        Thermal stress [MPa].
    T_gradient_K_cm : float
        Temperature gradient [K/cm].

    Returns
    -------
    dict
        {"BPD_cm2": float, "TSD_cm2": float, "total_cm2": float}
    """
    base = PVT_GROWTH["BPD_base_cm2"]
    v_ref = 0.2
    s_ref = 10.0

    v_ratio = (growth_rate_mm_h / v_ref) if v_ref > 0 else 1.0
    s_ratio = (thermal_stress_MPa / s_ref) if s_ref > 0 else 1.0

    bpd = base * abs(v_ratio) ** PVT_GROWTH["BPD_growth_rate_exp"] * abs(s_ratio) ** PVT_GROWTH["BPD_stress_exp"]
    tsd = bpd * PVT_GROWTH["TSD_to_BPD_ratio"]

    return {"BPD_cm2": bpd, "TSD_cm2": tsd, "total_cm2": bpd + tsd}


def pvt_simulation(T_source: float, T_seed: float, P_Ar: float,
                   growth_time_h: float, diameter_mm: float = 150) -> Dict:
    """Full PVT growth simulation.

    Parameters
    ----------
    T_source : float
        Source temperature [°C].
    T_seed : float
        Seed temperature [°C].
    P_Ar : float
        Argon pressure [mbar].
    growth_time_h : float
        Growth time [hours].
    diameter_mm : float
        Crystal diameter [mm].

    Returns
    -------
    dict
        {"thickness_mm": float, "growth_rate_mm_h": float,
         "defects": dict, "energy_kWh": float, "quality_grade": str}
    """
    v = growth_rate(T_source, T_seed, P_Ar)
    thickness = v * growth_time_h

    # Thermal stress estimate (assume ΔT ~ 5-20 K radial)
    delta_T_radial = 5.0 + 0.05 * (T_source - T_seed)
    T_prof = (T_seed + delta_T_radial / 2, T_seed - delta_T_radial / 2)
    stress = thermal_stress(T_prof, diameter_mm, thickness)

    T_grad = (T_source - T_seed) / (0.03 * 100)  # K/cm assuming 3cm distance
    defects = defect_density(v, stress, T_grad)

    # Energy
    if diameter_mm <= 150:
        energy = PVT_GROWTH["energy_kWh_per_h_150mm"] * growth_time_h
    else:
        energy = PVT_GROWTH["energy_kWh_per_h_200mm"] * growth_time_h

    # Quality grade
    bpd = defects["BPD_cm2"]
    if bpd < 500:
        quality = "prime"
    elif bpd < 2000:
        quality = "standard"
    elif bpd < 5000:
        quality = "mechanical"
    else:
        quality = "research"

    return {
        "thickness_mm": thickness,
        "growth_rate_mm_h": v,
        "defects": defects,
        "thermal_stress_MPa": stress,
        "energy_kWh": energy,
        "quality_grade": quality,
    }


def scale_up_150_to_200(current_conditions: Dict) -> Dict:
    """Predict conditions for 150mm → 200mm scale-up.

    Parameters
    ----------
    current_conditions : dict
        {"T_source": float, "T_seed": float, "P_Ar": float,
         "growth_time_h": float}

    Returns
    -------
    dict
        {"current_150mm": dict, "predicted_200mm": dict,
         "challenges": list}
    """
    T_s = current_conditions["T_source"]
    T_d = current_conditions["T_seed"]
    P = current_conditions["P_Ar"]
    t = current_conditions["growth_time_h"]

    sim_150 = pvt_simulation(T_s, T_d, P, t, 150)

    # 200mm: need lower growth rate, tighter thermal control
    # Reduce ΔT by 20% to manage stress on larger diameter
    delta_T = T_s - T_d
    new_delta_T = delta_T * 0.8
    new_T_s = T_d + new_delta_T
    # Increase time to compensate
    new_t = t * (delta_T / new_delta_T) if new_delta_T > 0 else t * 1.5

    sim_200 = pvt_simulation(new_T_s, T_d, P, new_t, 200)

    challenges = []
    if sim_200["defects"]["BPD_cm2"] > 1000:
        challenges.append("BPD density may exceed prime grade threshold")
    if sim_200["thermal_stress_MPa"] > 50:
        challenges.append("Thermal stress risk for cracking")
    challenges.append("Seed crystal availability at 200mm is limited")
    challenges.append("Longer growth time increases energy cost")

    return {
        "current_150mm": sim_150,
        "predicted_200mm": sim_200,
        "adjusted_conditions": {
            "T_source": new_T_s, "T_seed": T_d,
            "P_Ar": P, "growth_time_h": new_t,
        },
        "challenges": challenges,
    }


def energy_per_wafer(diameter_mm: float, thickness_mm: float,
                     growth_rate_mm_h: float) -> float:
    """Energy per wafer from boule growth [kWh/wafer].

    Parameters
    ----------
    diameter_mm : float
        Wafer diameter [mm].
    thickness_mm : float
        Wafer thickness [mm] (typically 0.35mm).
    growth_rate_mm_h : float
        Growth rate [mm/h].

    Returns
    -------
    float
        Energy per wafer [kWh].
    """
    if growth_rate_mm_h <= 0:
        return float("inf")

    time_per_mm = 1.0 / growth_rate_mm_h  # h/mm
    time_per_wafer = time_per_mm * thickness_mm  # h

    if diameter_mm <= 150:
        power = PVT_GROWTH["energy_kWh_per_h_150mm"]
    else:
        power = PVT_GROWTH["energy_kWh_per_h_200mm"]

    return power * time_per_wafer
