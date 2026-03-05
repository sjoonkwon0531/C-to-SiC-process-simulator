"""M10: Energy/LCA & Economics — Full pipeline energy, carbon, and cost analysis.

Covers:
  - Stage-wise energy waterfall (kWh/wafer)
  - CO₂ emissions by region and electrification scenario
  - COGS breakdown
  - Electrification scenarios (current / grid / solar)
  - Regional cost comparison (Saudi / USA / EU / China)
  - NPV and IRR analysis
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import LCA_ECON, ENERGY_COSTS

# Region alias mapping for emission_factors
_REGION_ALIAS = {
    'saudi_arabia': 'saudi_arabia',
    'usa': 'usa_average',
    'eu': 'eu_average',
    'china': 'china_industrial',
}

def _resolve_ef_region(region: str) -> str:
    """Resolve region name to emission_factors key."""
    if region in LCA_ECON["emission_factors"]:
        return region
    return _REGION_ALIAS.get(region, region)


def energy_waterfall(stages_energy: Dict[str, float]) -> Dict:
    """Cumulative energy waterfall by process stage.

    Parameters
    ----------
    stages_energy : dict
        {stage_name: kWh_per_wafer}.

    Returns
    -------
    dict
        {"stages": list, "individual_kWh": list, "cumulative_kWh": list,
         "total_kWh": float, "pct_by_stage": dict}
    """
    stages = list(stages_energy.keys())
    individual = list(stages_energy.values())
    cumulative = list(np.cumsum(individual))
    total = cumulative[-1] if cumulative else 0

    pct = {s: (v / total * 100 if total > 0 else 0)
           for s, v in stages_energy.items()}

    return {
        "stages": stages,
        "individual_kWh": individual,
        "cumulative_kWh": cumulative,
        "total_kWh": total,
        "pct_by_stage": pct,
    }


def co2_emissions(energy_kWh: float, region: str = "saudi_arabia",
                  electrification_scenario: str = "current") -> float:
    """CO₂ emissions [kg CO₂].

    Parameters
    ----------
    energy_kWh : float
        Energy consumed [kWh].
    region : str
        Region key.
    electrification_scenario : str
        "current", "grid_electric", or "solar_electric".

    Returns
    -------
    float
        CO₂ emissions [kg].
    """
    ef = LCA_ECON["emission_factors"].get(_resolve_ef_region(region), 0.5)
    scenario_mult = LCA_ECON["electrification_scenarios"].get(
        electrification_scenario, 1.0)
    return energy_kWh * ef * scenario_mult


def cogs_breakdown(stage_costs: Dict[str, float] = None) -> Dict:
    """COGS breakdown by category [$/wafer].

    Parameters
    ----------
    stage_costs : dict, optional
        {category: $/wafer}. Uses defaults if not provided.

    Returns
    -------
    dict
        {"categories": dict, "total_usd": float, "pct_by_category": dict}
    """
    costs = stage_costs or dict(LCA_ECON["cogs_default"])
    total = sum(costs.values())
    pct = {k: (v / total * 100 if total > 0 else 0) for k, v in costs.items()}

    return {
        "categories": costs,
        "total_usd": total,
        "pct_by_category": pct,
    }


def electrification_scenarios(base_energy_kWh: float,
                              region: str = "saudi_arabia") -> Dict:
    """Compare 3 electrification scenarios.

    Parameters
    ----------
    base_energy_kWh : float
        Base energy per wafer [kWh].
    region : str
        Region key.

    Returns
    -------
    dict
        {scenario: {"co2_kg": float, "cost_usd": float}}
    """
    grid_rate = ENERGY_COSTS.get(region, 0.048)
    solar_rate = ENERGY_COSTS.get("saudi_solar_ppa", 0.015)

    results = {}
    for scenario in ["current", "grid_electric", "solar_electric"]:
        co2 = co2_emissions(base_energy_kWh, region, scenario)
        if scenario == "solar_electric":
            cost = base_energy_kWh * solar_rate
        else:
            cost = base_energy_kWh * grid_rate
        results[scenario] = {
            "co2_kg": co2,
            "energy_cost_usd": cost,
            "energy_kWh": base_energy_kWh,
        }

    return results


def regional_comparison(wafer_params: Dict = None) -> Dict:
    """Regional cost comparison for wafer production.

    Parameters
    ----------
    wafer_params : dict, optional
        {"base_cost_usd": float, "energy_kWh": float}.

    Returns
    -------
    dict
        {region: {"total_cost_usd": float, "energy_cost": float,
                  "labor_cost": float, "co2_kg": float}}
    """
    params = wafer_params or {"base_cost_usd": 290.0, "energy_kWh": 500.0}
    base = params["base_cost_usd"]
    energy_kWh = params["energy_kWh"]

    cogs = LCA_ECON["cogs_default"]
    results = {}

    for region, mult in LCA_ECON["regional_multipliers"].items():
        energy_cost = cogs["energy"] * mult["energy"]
        labor_cost = cogs["labor"] * mult["labor"]
        capex_cost = cogs["equipment_depreciation"] * mult["capex"]
        other = cogs["raw_materials"] + cogs["consumables"] + cogs["overhead"]
        total = energy_cost + labor_cost + capex_cost + other

        region_emission_key = _resolve_ef_region(region)
        co2 = co2_emissions(energy_kWh, region_emission_key)

        results[region] = {
            "total_cost_usd": total,
            "energy_cost_usd": energy_cost,
            "labor_cost_usd": labor_cost,
            "capex_cost_usd": capex_cost,
            "co2_kg": co2,
        }

    return results


def npv_irr(capex: float, annual_revenue: float, annual_opex: float,
            years: int = None, discount_rate: float = None) -> Dict:
    """Net Present Value and Internal Rate of Return.

    Parameters
    ----------
    capex : float
        Initial investment [$].
    annual_revenue : float
        Annual revenue [$].
    annual_opex : float
        Annual operating cost [$].
    years : int
        Project lifetime [years].
    discount_rate : float
        Discount rate (e.g. 0.10 for 10%).

    Returns
    -------
    dict
        {"NPV": float, "IRR": float, "payback_years": float,
         "annual_cashflow": float}
    """
    yrs = years or LCA_ECON["project_years"]
    r = discount_rate or LCA_ECON["discount_rate"]

    annual_cf = annual_revenue - annual_opex
    cashflows = [-capex] + [annual_cf] * yrs

    # NPV
    npv = -capex
    for t in range(1, yrs + 1):
        npv += annual_cf / (1 + r) ** t

    # IRR via bisection
    irr = _compute_irr(cashflows)

    # Simple payback
    payback = capex / annual_cf if annual_cf > 0 else float("inf")

    return {
        "NPV": npv,
        "IRR": irr,
        "payback_years": payback,
        "annual_cashflow": annual_cf,
        "total_revenue": annual_revenue * yrs,
        "total_opex": annual_opex * yrs,
    }


def _compute_irr(cashflows: List[float], tol: float = 1e-6,
                 max_iter: int = 1000) -> float:
    """Compute IRR via bisection method."""
    def npv_at_rate(r):
        return sum(cf / (1 + r) ** t for t, cf in enumerate(cashflows))

    lo, hi = -0.5, 5.0
    if npv_at_rate(lo) < 0:
        return float("nan")

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        val = npv_at_rate(mid)
        if abs(val) < tol:
            return mid
        if val > 0:
            lo = mid
        else:
            hi = mid

    return (lo + hi) / 2
