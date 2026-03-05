"""M02: Acid Leaching — Shrinking Core Model based purification.

Governing equations:
  Shrinking Core (diffusion control): t/τ = 1 - 3(1-X)^(2/3) + 2(1-X)
  Arrhenius diffusivity: D(T) = D0·exp(-Ea/(R·T))
  Multi-component: dCi/dt = -ki(T)·Ci·(1-Xi)^(2/3)·[H+]^ni
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import ACID_LEACH, R_GAS, ELECTRIFICATION_OPTIONS, ENERGY_COSTS


def _diffusivity(D0: float, Ea_kJ_mol: float, T_K: float) -> float:
    """Effective diffusivity via Arrhenius [m²/s].

    Parameters
    ----------
    D0 : float
        Pre-exponential diffusivity [m²/s].
    Ea_kJ_mol : float
        Activation energy [kJ/mol].
    T_K : float
        Temperature [K].

    Returns
    -------
    float
        D(T) [m²/s].
    """
    return D0 * np.exp(-Ea_kJ_mol * 1000.0 / (R_GAS * T_K))


def shrinking_core_conversion(tau: float, t: float) -> float:
    """Solve shrinking core model (diffusion control) for conversion X at time t.

    t/τ = 1 - 3(1-X)^(2/3) + 2(1-X)

    Uses bisection since the equation is implicit in X.

    Parameters
    ----------
    tau : float
        Complete conversion time [s].
    t : float
        Elapsed time [s].

    Returns
    -------
    float
        Conversion X ∈ [0, 1].
    """
    if t <= 0 or tau <= 0:
        return 0.0
    if t >= tau:
        return 1.0

    ratio = t / tau

    # f(X) = 1 - 3(1-X)^(2/3) + 2(1-X) - ratio = 0
    # Bisection
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        val = 1.0 - 3.0 * (1.0 - mid) ** (2.0 / 3.0) + 2.0 * (1.0 - mid)
        if val < ratio:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def shrinking_core_model(
    particle_size_m: float,
    D_eff: float,
    C_acid_mol_L: float,
    T_C: float,
    t_s: float,
) -> float:
    """Compute conversion X(t) for shrinking core model (diffusion control).

    τ = ρ_s · R² / (6 · D_eff · C_acid)  (simplified)

    Parameters
    ----------
    particle_size_m : float
        Particle diameter [m].
    D_eff : float
        Effective diffusivity [m²/s].
    C_acid_mol_L : float
        Acid concentration [mol/L].
    T_C : float
        Temperature [°C] (used for info, D_eff should already be T-adjusted).
    t_s : float
        Time [s].

    Returns
    -------
    float
        Conversion X ∈ [0, 1].
    """
    if particle_size_m <= 0 or D_eff <= 0 or C_acid_mol_L <= 0:
        return 0.0
    R = particle_size_m / 2.0
    rho_s = 1600.0  # carbon density kg/m³ (approximate)
    # τ = ρ_s · R² / (6 · D_eff · C_acid * 1000)  [C_acid in mol/m³]
    C_acid_mol_m3 = C_acid_mol_L * 1000.0
    tau = rho_s * R ** 2 / (6.0 * D_eff * C_acid_mol_m3)
    return shrinking_core_conversion(tau, t_s)


def multi_acid_leach(
    impurities: Dict[str, float],
    acid_type: str,
    T_C: float,
    duration_s: float,
    n_stages: int = 1,
    particle_size_m: float = 1e-3,
) -> Dict[str, float]:
    """Simulate multi-component acid leaching.

    Parameters
    ----------
    impurities : dict
        {element: ppm} input concentrations.
    acid_type : str
        Key in ACID_LEACH config.
    T_C : float
        Temperature [°C].
    duration_s : float
        Leaching duration per stage [s].
    n_stages : int
        Number of sequential leaching stages.
    particle_size_m : float
        Particle size [m].

    Returns
    -------
    dict
        {element: ppm} residual impurities after leaching.
    """
    if acid_type not in ACID_LEACH:
        raise ValueError(f"Unknown acid type '{acid_type}'. Available: {list(ACID_LEACH.keys())}")

    acid = ACID_LEACH[acid_type]
    removal_eff = acid["removal_eff"]
    T_K = T_C + 273.15
    D0 = acid.get("D0_m2_s", 1e-9)
    Ea = acid.get("Ea_diffusion_kJ_mol", 20.0)
    D_eff = _diffusivity(D0, Ea, T_K)
    conc = acid["conc_mol_L"]
    if isinstance(conc, tuple):
        conc = conc[0]  # use primary acid concentration

    residual = dict(impurities)
    for _stage in range(n_stages):
        for element, ppm in list(residual.items()):
            if element in removal_eff:
                # Shrinking core gives kinetic conversion
                X_kinetic = shrinking_core_model(particle_size_m, D_eff, conc, T_C, duration_s)
                # Cap at thermodynamic removal efficiency
                X_eff = min(X_kinetic, removal_eff[element])
                residual[element] = ppm * (1.0 - X_eff)
            # Elements not targeted by this acid remain unchanged

    return residual


def optimize_acid_sequence(
    impurities: Dict[str, float],
    target_total_ppm: float,
    T_C: float = 80.0,
    duration_s: float = 7200.0,
    particle_size_m: float = 1e-3,
) -> List[Dict]:
    """Find optimal acid sequence to minimize residual impurities.

    Tries all single acids and the mix, returns ranked results.

    Parameters
    ----------
    impurities : dict
        {element: ppm} initial.
    target_total_ppm : float
        Target total impurity level.
    T_C : float
        Temperature [°C].
    duration_s : float
        Duration per stage [s].
    particle_size_m : float
        Particle diameter [m].

    Returns
    -------
    list of dict
        Sorted by residual total ppm, each with acid_type, residual, total_ppm.
    """
    results = []
    for acid_type in ACID_LEACH:
        residual = multi_acid_leach(impurities, acid_type, T_C, duration_s, 1, particle_size_m)
        total = sum(residual.values())
        results.append({
            "acid_type": acid_type,
            "residual_impurities": residual,
            "total_residual_ppm": total,
            "meets_target": total <= target_total_ppm,
        })
    results.sort(key=lambda x: x["total_residual_ppm"])

    # Try 2-stage combinations
    best_single = results[0]
    if not best_single["meets_target"]:
        for acid2 in ACID_LEACH:
            residual2 = multi_acid_leach(
                best_single["residual_impurities"], acid2, T_C, duration_s, 1, particle_size_m
            )
            total2 = sum(residual2.values())
            results.append({
                "acid_type": f"{best_single['acid_type']} → {acid2}",
                "residual_impurities": residual2,
                "total_residual_ppm": total2,
                "meets_target": total2 <= target_total_ppm,
            })
        results.sort(key=lambda x: x["total_residual_ppm"])

    return results


def energy_consumption(
    T_C: float,
    volume_L: float,
    duration_s: float,
    mode: str = "conventional",
) -> Dict[str, float]:
    """Estimate energy consumption for acid leaching heating.

    Parameters
    ----------
    T_C : float
        Target temperature [°C].
    volume_L : float
        Acid solution volume [L].
    duration_s : float
        Duration [s].
    mode : str
        'conventional' (steam) or 'electric'.

    Returns
    -------
    dict
        {"energy_kWh": float, "mode": str}
    """
    # Heat to raise water-based acid from 25°C
    mass_kg = volume_L  # ~1 kg/L for dilute acid
    Cp = 4186.0  # J/(kg·K) water
    delta_T = max(0, T_C - 25.0)
    Q_heat = mass_kg * Cp * delta_T  # J
    # Heat loss during operation (~10% of heating per hour)
    Q_loss = Q_heat * 0.10 * (duration_s / 3600.0)
    Q_total = Q_heat + Q_loss

    opts = ELECTRIFICATION_OPTIONS["acid_leach_heating"]
    if mode == "electric":
        Q_total *= opts["energy_ratio"]

    energy_kWh = Q_total / 3.6e6
    return {"energy_kWh": energy_kWh, "mode": mode}


def electrification_comparison(
    T_C: float,
    volume_L: float,
    duration_s: float,
    region: str = "saudi_arabia",
) -> Dict:
    """Compare conventional vs electric heating for acid leaching.

    Parameters
    ----------
    T_C, volume_L, duration_s : float
        Process parameters.
    region : str
        Key in ENERGY_COSTS.

    Returns
    -------
    dict
        Comparison with energy and cost for both modes.
    """
    conv = energy_consumption(T_C, volume_L, duration_s, "conventional")
    elec = energy_consumption(T_C, volume_L, duration_s, "electric")
    cost_per_kwh = ENERGY_COSTS.get(region, 0.048)

    return {
        "conventional": {**conv, "cost_usd": conv["energy_kWh"] * cost_per_kwh},
        "electric": {**elec, "cost_usd": elec["energy_kWh"] * cost_per_kwh},
        "energy_saving_pct": (1 - elec["energy_kWh"] / conv["energy_kWh"]) * 100 if conv["energy_kWh"] > 0 else 0,
        "region": region,
    }
