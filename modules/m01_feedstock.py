"""M01: Petroleum Coke Feedstock Characterization & Selection.

Provides feedstock property lookup, purification path calculation,
and stage estimation for reaching target purity grades.
"""

import copy
from typing import Dict, Optional, Tuple, List
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PETRO_COKE_GRADES, PURITY_GRADES


def select_feedstock(grade: str) -> Dict:
    """Select a petroleum coke grade and return its full property profile.

    Parameters
    ----------
    grade : str
        One of 'green_coke', 'calcined_coke', 'needle_coke'.

    Returns
    -------
    dict
        Deep copy of grade properties including impurities_ppm (dict),
        carbon_pct, sulfur_ppm, ash_pct, volatile_pct, HHV_MJ_kg.

    Raises
    ------
    ValueError
        If grade not found.
    """
    if grade not in PETRO_COKE_GRADES:
        raise ValueError(f"Unknown grade '{grade}'. Available: {list(PETRO_COKE_GRADES.keys())}")
    return copy.deepcopy(PETRO_COKE_GRADES[grade])


def total_impurity_ppm(impurities: Dict[str, float]) -> float:
    """Sum all impurity concentrations in ppm.

    Parameters
    ----------
    impurities : dict
        {element: ppm} mapping.

    Returns
    -------
    float
        Total impurity in ppm.
    """
    return sum(impurities.values())


def calculate_purification_path(
    current_impurities: Dict[str, float],
    target_grade: str,
) -> Dict[str, Dict[str, float]]:
    """Calculate required removal fraction for each impurity to reach target grade.

    Parameters
    ----------
    current_impurities : dict
        {element: ppm} current levels.
    target_grade : str
        Key in PURITY_GRADES.

    Returns
    -------
    dict
        {element: {"current_ppm": float, "max_allowed_ppm": float,
                    "required_removal_frac": float}}
        Elements already below threshold have required_removal_frac = 0.
    """
    if target_grade not in PURITY_GRADES:
        raise ValueError(f"Unknown target grade '{target_grade}'. Available: {list(PURITY_GRADES.keys())}")

    target_total = PURITY_GRADES[target_grade]["total_impurity_ppm"]
    current_total = total_impurity_ppm(current_impurities)

    if current_total <= target_total:
        # Already meets target
        return {
            el: {"current_ppm": v, "max_allowed_ppm": v, "required_removal_frac": 0.0}
            for el, v in current_impurities.items()
        }

    # Proportional allocation: each element must be reduced by the same fraction
    overall_reduction = 1.0 - target_total / current_total
    result = {}
    for el, ppm in current_impurities.items():
        max_allowed = ppm * (1.0 - overall_reduction)
        removal_frac = overall_reduction if ppm > 0 else 0.0
        result[el] = {
            "current_ppm": ppm,
            "max_allowed_ppm": max_allowed,
            "required_removal_frac": removal_frac,
        }
    return result


def estimate_purification_stages(
    current_impurities: Dict[str, float],
    target_grade: str,
    per_stage_removal: float = 0.80,
) -> Dict:
    """Estimate number of purification stages needed.

    Uses geometric decay model: after n stages, residual = (1 - per_stage_removal)^n.

    Parameters
    ----------
    current_impurities : dict
        {element: ppm}.
    target_grade : str
        Key in PURITY_GRADES.
    per_stage_removal : float
        Fraction removed per stage (default 0.80 = 80%).

    Returns
    -------
    dict
        {"n_stages": int, "current_total_ppm": float, "target_total_ppm": float,
         "predicted_residual_ppm": float}
    """
    import math

    if target_grade not in PURITY_GRADES:
        raise ValueError(f"Unknown target grade '{target_grade}'.")
    if not (0 < per_stage_removal < 1):
        raise ValueError("per_stage_removal must be in (0, 1).")

    target_total = PURITY_GRADES[target_grade]["total_impurity_ppm"]
    current_total = total_impurity_ppm(current_impurities)

    if current_total <= target_total:
        return {
            "n_stages": 0,
            "current_total_ppm": current_total,
            "target_total_ppm": target_total,
            "predicted_residual_ppm": current_total,
        }

    # (1 - r)^n <= target/current  =>  n >= log(target/current) / log(1-r)
    n = math.ceil(math.log(target_total / current_total) / math.log(1.0 - per_stage_removal))
    residual = current_total * (1.0 - per_stage_removal) ** n

    return {
        "n_stages": n,
        "current_total_ppm": current_total,
        "target_total_ppm": target_total,
        "predicted_residual_ppm": residual,
    }


def feedstock_cost(grade: str, quantity_kg: float) -> Dict[str, float]:
    """Estimate feedstock cost.

    Parameters
    ----------
    grade : str
        Coke grade key.
    quantity_kg : float
        Amount in kg.

    Returns
    -------
    dict
        {"price_usd_per_ton": float, "quantity_kg": float, "total_cost_usd": float}
    """
    if quantity_kg < 0:
        raise ValueError("quantity_kg must be non-negative.")
    props = select_feedstock(grade)
    price_per_ton = props.get("price_usd_per_ton", 200.0)
    total = price_per_ton * quantity_kg / 1000.0
    return {
        "price_usd_per_ton": price_per_ton,
        "quantity_kg": quantity_kg,
        "total_cost_usd": total,
    }


def compare_feedstocks() -> List[Dict]:
    """Compare all available feedstock grades side by side.

    Returns
    -------
    list of dict
        Each dict has grade name and key properties.
    """
    results = []
    for grade, props in PETRO_COKE_GRADES.items():
        results.append({
            "grade": grade,
            "carbon_pct": props["carbon_pct"],
            "total_impurity_ppm": total_impurity_ppm(props["impurities_ppm"]),
            "sulfur_ppm": props["sulfur_ppm"],
            "price_usd_per_ton": props.get("price_usd_per_ton", 0),
        })
    return results
