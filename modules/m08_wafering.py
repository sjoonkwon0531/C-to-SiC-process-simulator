"""M08: Wafering & CMP — Diamond wire sawing and chemical-mechanical planarization.

Governing equations:
  Kerf loss: kerf = wire_diameter + 2·abrasive_size
  Preston MRR: MRR = k_p · P · V
  Surface roughness: Ra(t) = Ra_0·exp(-k·t) + Ra_final
  CMP chemistry (simplified): SiC + 2H₂O → SiO₂ + CH₄
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import WAFERING


def wire_saw_yield(boule_length_mm: float, wafer_thickness_mm: float = None,
                   kerf_width_mm: float = None) -> Dict:
    """Calculate wafer yield from boule slicing.

    Parameters
    ----------
    boule_length_mm : float
        Boule usable length [mm].
    wafer_thickness_mm : float
        Wafer thickness [mm].
    kerf_width_mm : float
        Kerf (cutting) loss [mm].

    Returns
    -------
    dict
        {"n_wafers": int, "yield_pct": float, "kerf_loss_mm": float,
         "material_used_mm": float}
    """
    t = wafer_thickness_mm or WAFERING["wafer_thickness_mm"]
    if kerf_width_mm is None:
        kerf_width_mm = WAFERING["wire_diameter_mm"] + 2 * WAFERING["abrasive_size_mm"]

    pitch = t + kerf_width_mm
    n_wafers = int(boule_length_mm / pitch)
    material_used = n_wafers * pitch
    yield_pct = (n_wafers * t / boule_length_mm * 100) if boule_length_mm > 0 else 0

    return {
        "n_wafers": n_wafers,
        "yield_pct": yield_pct,
        "kerf_loss_mm": kerf_width_mm,
        "material_used_mm": material_used,
        "wasted_mm": boule_length_mm - material_used,
    }


def preston_mrr(k_p: float, pressure_kPa: float, velocity_m_s: float) -> float:
    """Material removal rate via Preston equation [μm/min].

    MRR = k_p · P · V

    Parameters
    ----------
    k_p : float
        Preston coefficient [m²/N].
    pressure_kPa : float
        Applied pressure [kPa].
    velocity_m_s : float
        Relative velocity [m/s].

    Returns
    -------
    float
        Material removal rate [μm/min].
    """
    P_Pa = pressure_kPa * 1000.0  # Pa = N/m²
    mrr_m_s = k_p * P_Pa * velocity_m_s  # m/s
    mrr_um_min = mrr_m_s * 1e6 * 60.0  # μm/min
    return mrr_um_min


def cmp_process(initial_Ra_nm: float = None, target_Ra_nm: float = None,
                slurry_type: str = "colloidal_silica",
                time_min: float = 60.0) -> Dict:
    """CMP process simulation.

    Ra(t) = (Ra_0 - Ra_final)·exp(-k·t) + Ra_final

    Parameters
    ----------
    initial_Ra_nm : float
        Initial surface roughness [nm].
    target_Ra_nm : float
        Target roughness [nm].
    slurry_type : str
        Slurry type key.
    time_min : float
        Process time [minutes].

    Returns
    -------
    dict
        {"final_Ra_nm": float, "MRR_um_min": float, "material_removed_um": float,
         "cost_usd": float, "target_reached": bool}
    """
    Ra_0 = initial_Ra_nm or WAFERING["initial_Ra_nm"]
    Ra_target = target_Ra_nm or WAFERING["target_Ra_nm"]

    k = WAFERING["roughness_k_per_min"].get(slurry_type, 0.03)
    kp = WAFERING["preston_kp"].get(slurry_type, 3e-14)

    # Roughness evolution
    Ra_final_asymptote = Ra_target * 0.8  # Asymptotic limit below target
    Ra_t = (Ra_0 - Ra_final_asymptote) * np.exp(-k * time_min) + Ra_final_asymptote

    # MRR
    P = WAFERING["cmp_pressure_kPa"]
    V = WAFERING["cmp_velocity_m_s"]
    mrr = preston_mrr(kp, P, V)
    removed = mrr * time_min  # μm

    # Cost
    process_cost = WAFERING["cmp_cost_per_min"] * time_min
    slurry_cost = (WAFERING["slurry_cost_per_L"].get(slurry_type, 50)
                   * WAFERING["slurry_consumption_L_per_min"] * time_min)
    total_cost = process_cost + slurry_cost

    return {
        "final_Ra_nm": Ra_t,
        "MRR_um_min": mrr,
        "material_removed_um": removed,
        "cost_usd": total_cost,
        "target_reached": Ra_t <= Ra_target,
        "time_min": time_min,
    }


def wafer_cost(diameter_mm: float, boule_cost_usd: float,
               processing_cost_usd: float = None) -> float:
    """Cost per wafer [$/wafer].

    Parameters
    ----------
    diameter_mm : float
        Wafer diameter [mm].
    boule_cost_usd : float
        Total boule cost [$].
    processing_cost_usd : float
        Per-wafer processing cost [$].

    Returns
    -------
    float
        Cost per wafer [$/wafer].
    """
    # Assume typical boule: 20-30mm usable length
    boule_length = 25.0  # mm typical
    saw_result = wire_saw_yield(boule_length)
    n_wafers = max(saw_result["n_wafers"], 1)

    proc = processing_cost_usd
    if proc is None:
        proc = (WAFERING["wire_saw_cost_per_wafer"]
                + WAFERING["grinding_cost_per_wafer"]
                + WAFERING["cmp_cost_per_min"] * 60)  # ~1h CMP

    return boule_cost_usd / n_wafers + proc


def kerf_loss_optimization(wire_diameter_range: Tuple[float, float] = (0.06, 0.20)) -> Dict:
    """Optimize wire diameter for maximum yield.

    Parameters
    ----------
    wire_diameter_range : tuple
        (min_diameter_mm, max_diameter_mm).

    Returns
    -------
    dict
        {"wire_diameters": list, "kerf_losses": list, "n_wafers": list,
         "yields_pct": list, "optimal_wire_mm": float}
    """
    diameters = np.linspace(wire_diameter_range[0], wire_diameter_range[1], 20)
    boule_length = 25.0  # mm

    kerfs, wafers, yields = [], [], []
    for d in diameters:
        kerf = d + 2 * WAFERING["abrasive_size_mm"]
        res = wire_saw_yield(boule_length, kerf_width_mm=kerf)
        kerfs.append(kerf)
        wafers.append(res["n_wafers"])
        yields.append(res["yield_pct"])

    best_idx = int(np.argmax(wafers))

    return {
        "wire_diameters": diameters.tolist(),
        "kerf_losses": kerfs,
        "n_wafers": wafers,
        "yields_pct": yields,
        "optimal_wire_mm": float(diameters[best_idx]),
        "optimal_kerf_mm": kerfs[best_idx],
        "max_wafers": wafers[best_idx],
    }
