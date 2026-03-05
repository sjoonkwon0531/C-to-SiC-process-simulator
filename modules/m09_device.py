"""M09: SiC Power Device for AIDC — MOSFET loss modeling and AIDC savings.

Governing equations:
  Baliga FOM: BF = ε·μ·E_c³
  R_drift = 4·V_BR² / (ε·μ·E_c³)
  P_cond = I²·R_on
  P_sw = 0.5·V·I·(t_on + t_off)·f_sw
  η = P_out / (P_out + P_cond + P_sw)
  R_th = t / (k·A)
"""

import numpy as np
from typing import Dict, List, Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SIC_DEVICE


def baliga_fom(material: str = None) -> Dict:
    """Baliga Figure of Merit comparison.

    BF = ε_r · ε_0 · μ · E_c³

    Parameters
    ----------
    material : str, optional
        If given, return FOM for that material only.

    Returns
    -------
    dict
        {material: {"FOM": float, "FOM_normalized": float, ...}}
    """
    eps0 = SIC_DEVICE["epsilon_0_F_m"]
    results = {}
    fom_values = {}

    materials = SIC_DEVICE["materials"]
    if material and material in materials:
        materials = {material: materials[material]}

    for mat, props in materials.items():
        eps = props["epsilon_r"] * eps0
        mu = props["mu_cm2_Vs"] * 1e-4  # m²/(V·s)
        Ec = props["E_c_MV_cm"] * 1e8   # V/m
        fom = eps * mu * Ec ** 3
        fom_values[mat] = fom
        results[mat] = {
            "FOM": fom,
            "bandgap_eV": props["bandgap_eV"],
            "E_c_MV_cm": props["E_c_MV_cm"],
            "mu_cm2_Vs": props["mu_cm2_Vs"],
            "k_thermal_W_mK": props["k_thermal_W_mK"],
        }

    # Normalize to Si
    si_fom = fom_values.get("Si", 1.0)
    for mat in results:
        results[mat]["FOM_normalized"] = fom_values[mat] / si_fom if si_fom > 0 else 0

    return results


def mosfet_losses(V_ds: float, I_d: float, R_on: float,
                  f_sw: float, t_on: float = None,
                  t_off: float = None) -> Dict:
    """MOSFET power losses and efficiency.

    Parameters
    ----------
    V_ds : float
        Drain-source voltage [V].
    I_d : float
        Drain current [A].
    R_on : float
        On-state resistance [Ω].
    f_sw : float
        Switching frequency [Hz].
    t_on : float
        Turn-on time [s]. Default from config (ns→s).
    t_off : float
        Turn-off time [s].

    Returns
    -------
    dict
        {"P_cond": float, "P_sw": float, "P_total": float, "efficiency": float}
    """
    if t_on is None:
        t_on = SIC_DEVICE["t_on_ns"] * 1e-9
    if t_off is None:
        t_off = SIC_DEVICE["t_off_ns"] * 1e-9

    P_cond = I_d ** 2 * R_on
    P_sw = 0.5 * V_ds * I_d * (t_on + t_off) * f_sw
    P_total = P_cond + P_sw
    P_out = V_ds * I_d  # Simplified output power
    efficiency = P_out / (P_out + P_total) if (P_out + P_total) > 0 else 0

    return {
        "P_cond_W": P_cond,
        "P_sw_W": P_sw,
        "P_total_W": P_total,
        "efficiency": efficiency,
    }


def aidc_power_savings(rack_power_kW: float = None, n_racks: int = None,
                       si_eff: float = 0.94, sic_eff: float = 0.98) -> Dict:
    """Annual power savings from Si→SiC in AIDC power delivery.

    Parameters
    ----------
    rack_power_kW : float
        Power per rack [kW].
    n_racks : int
        Number of racks.
    si_eff : float
        Si-based PSU efficiency.
    sic_eff : float
        SiC-based PSU efficiency.

    Returns
    -------
    dict
        {"annual_kWh_saved": float, "annual_cost_saved_usd": float,
         "si_total_kW": float, "sic_total_kW": float}
    """
    rack_kW = rack_power_kW or SIC_DEVICE["aidc_rack_power_kW"]
    n = n_racks or SIC_DEVICE["aidc_n_racks"]
    hours = SIC_DEVICE["hours_per_year"]

    si_input = rack_kW / si_eff
    sic_input = rack_kW / sic_eff
    delta_kW = (si_input - sic_input) * n
    annual_kWh = delta_kW * hours

    # Use US industrial rate for AIDC
    from config import ENERGY_COSTS
    rate = ENERGY_COSTS["usa_industrial"]

    return {
        "annual_kWh_saved": annual_kWh,
        "annual_cost_saved_usd": annual_kWh * rate,
        "si_total_kW": si_input * n,
        "sic_total_kW": sic_input * n,
        "delta_kW": delta_kW,
    }


def thermal_advantage(power_density_W_cm2: float, die_size_mm2: float,
                      material: str = "4H-SiC") -> Dict:
    """Junction temperature comparison between materials.

    R_th = t / (k·A), T_j = T_ambient + P·R_th

    Parameters
    ----------
    power_density_W_cm2 : float
        Power dissipation density [W/cm²].
    die_size_mm2 : float
        Die area [mm²].
    material : str
        Material key.

    Returns
    -------
    dict
        {material: {"T_junction_C": float, "R_th_K_W": float}} for all materials.
    """
    A_m2 = die_size_mm2 * 1e-6  # mm² → m²
    A_cm2 = die_size_mm2 * 1e-2  # mm² → cm²
    P_W = power_density_W_cm2 * A_cm2
    t_die = 0.35e-3  # 350μm die thickness
    T_amb = 25.0

    results = {}
    for mat, props in SIC_DEVICE["materials"].items():
        k = props["k_thermal_W_mK"]
        R_th = t_die / (k * A_m2)
        T_j = T_amb + P_W * R_th
        results[mat] = {
            "T_junction_C": T_j,
            "R_th_K_W": R_th,
            "k_thermal_W_mK": k,
        }

    return results


def device_cost_projection(year: int, wafer_cost_usd: float,
                           die_yield: float = None) -> Dict:
    """Device cost projection.

    Parameters
    ----------
    year : int
        Target year.
    wafer_cost_usd : float
        Wafer cost [$/wafer].
    die_yield : float
        Die yield fraction.

    Returns
    -------
    dict
        {"cost_per_device_usd": float, "dies_per_wafer": int,
         "good_dies": float, "yield": float}
    """
    die_area = SIC_DEVICE["die_area_mm2"]
    if die_yield is None:
        die_yield = SIC_DEVICE["die_yield_150mm"]

    # 150mm wafer area
    wafer_area = np.pi * (75.0) ** 2  # mm²
    dies_per_wafer = int(wafer_area / die_area * 0.85)  # 85% utilization
    good_dies = dies_per_wafer * die_yield

    # Learning curve: cost decreases ~10% per year from base
    years_from_2024 = max(year - 2024, 0)
    learning = 0.90 ** years_from_2024  # 10% annual reduction

    die_cost = wafer_cost_usd / good_dies if good_dies > 0 else float("inf")
    device_cost = (die_cost + SIC_DEVICE["device_packaging_cost"]) * learning

    return {
        "cost_per_device_usd": device_cost,
        "dies_per_wafer": dies_per_wafer,
        "good_dies": good_dies,
        "yield": die_yield,
        "learning_factor": learning,
        "year": year,
    }
