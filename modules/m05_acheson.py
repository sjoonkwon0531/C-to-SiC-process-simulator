"""M05: Acheson SiC Synthesis — Electric resistance heating + carbothermal reduction.

Governing equations:
  SiO₂ + 3C → SiC + 2CO,  ΔH = +618.5 kJ/mol
  Reaction rate: r = k₀·exp(-Ea/(R·T))·a_SiO2·a_C³
  Joule heating: Q = I²·R(T)
  1D radial temperature: ρCp·∂T/∂t = (1/r)·∂/∂r(r·k·∂T/∂r) + Q_joule - ΔH·r
  Energy efficiency: η = (m_SiC·ΔH_f) / (∫P dt)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import ACHESON, R_GAS, ENERGY_COSTS


def sic_formation_rate(T_C: float, x_SiO2: float = 1.0, x_C: float = 1.0) -> float:
    """SiC formation rate [mol/(m³·s)].

    r = k₀·exp(-Ea/(R·T))·a_SiO2·a_C³

    Parameters
    ----------
    T_C : float
        Temperature [°C].
    x_SiO2 : float
        SiO₂ activity (mole fraction proxy) [0-1].
    x_C : float
        Carbon activity [0-1].

    Returns
    -------
    float
        Rate [mol/(m³·s)].
    """
    if T_C < 1500:  # Below meaningful reaction temperature
        return 0.0
    T_K = T_C + 273.15
    k0 = ACHESON["pre_exponential_s"]
    Ea = ACHESON["activation_energy_kJ_mol"] * 1000.0
    k = k0 * np.exp(-Ea / (R_GAS * T_K))
    return k * x_SiO2 * x_C ** 3


def graphite_resistivity(T_C: float) -> float:
    """Temperature-dependent graphite resistivity [Ω·m].

    ρ(T) = ρ₀·(1 + α·(T - 25))

    Parameters
    ----------
    T_C : float
        Temperature [°C].

    Returns
    -------
    float
        Resistivity [Ω·m].
    """
    rho0 = ACHESON["graphite_rho0_ohm_m"]
    alpha = ACHESON["graphite_alpha_K"]
    return rho0 * (1.0 + alpha * (T_C - 25.0))


def joule_heating_power(current_A: float, T_C: float, length_m: float, area_m2: float) -> float:
    """Compute Joule heating power [W].

    P = I²·R,  R = ρ(T)·L/A

    Parameters
    ----------
    current_A : float
        Current [A].
    T_C : float
        Core temperature [°C].
    length_m : float
        Core length [m].
    area_m2 : float
        Core cross-section area [m²].

    Returns
    -------
    float
        Power [W].
    """
    rho = graphite_resistivity(T_C)
    R = rho * length_m / area_m2
    return current_A ** 2 * R


def acheson_temperature_field(
    power_W: float,
    R_furnace_m: float = None,
    R_core_m: float = None,
    length_m: float = None,
    duration_s: float = None,
    n_radial: int = 50,
    dt_s: float = 10.0,
) -> Dict:
    """Compute 1D radial temperature field in Acheson furnace.

    ρCp·∂T/∂t = (1/r)·∂/∂r(r·k·∂T/∂r) + Q_source

    Q_source is concentrated at core (r < R_core).

    Parameters
    ----------
    power_W : float
        Total electrical power input [W].
    R_furnace_m : float
        Furnace outer radius [m].
    R_core_m : float
        Graphite core radius [m].
    length_m : float
        Furnace length [m].
    duration_s : float
        Simulation duration [s].
    n_radial : int
        Number of radial nodes.
    dt_s : float
        Time step [s].

    Returns
    -------
    dict
        {"r_m": array, "T_C": array, "T_core_C": float, "T_shell_C": float,
         "sic_zone_r_range_m": tuple}
    """
    R_f = R_furnace_m or ACHESON["default_radius_m"]
    R_c = R_core_m or ACHESON["default_core_radius_m"]
    L = length_m or ACHESON["default_length_m"]
    dur = duration_s or ACHESON["cycle_time_hours"] * 3600.0

    rho = ACHESON["charge_density_kg_m3"]
    Cp = ACHESON["charge_Cp_J_kgK"]
    k_th = ACHESON["charge_k_W_mK"]
    alpha_diff = k_th / (rho * Cp)

    dr = R_f / n_radial
    dt_stable = 0.4 * dr ** 2 / alpha_diff
    dt_s = min(dt_s, dt_stable)

    r = np.linspace(0, R_f, n_radial + 1)
    T = np.full(n_radial + 1, 25.0)  # initial 25°C

    # Volumetric heat source in core [W/m³]
    V_core = np.pi * R_c ** 2 * L
    Q_vol = power_W / V_core if V_core > 0 else 0.0

    n_steps = int(dur / dt_s)
    # Limit steps for computational feasibility
    n_steps = min(n_steps, 500000)

    for _ in range(n_steps):
        T_new = T.copy()
        for j in range(1, n_radial):
            laplacian = (
                (T[j + 1] - 2 * T[j] + T[j - 1]) / dr ** 2
                + (1.0 / r[j]) * (T[j + 1] - T[j - 1]) / (2.0 * dr)
            )
            source = Q_vol / (rho * Cp) if r[j] <= R_c else 0.0
            T_new[j] = T[j] + dt_s * (alpha_diff * laplacian + source)
        # Center symmetry
        T_new[0] = T_new[1]
        # Outer boundary: convective (approximate)
        h_out = 20.0  # W/(m²·K)
        T_new[-1] = T[-1] + dt_s * (
            alpha_diff * 2 * (T[-2] - T[-1]) / dr ** 2
            - h_out * (T[-1] - 25.0) / (rho * Cp * dr)
        )
        T = T_new

    # Identify SiC formation zone (1800-2700°C)
    sic_mask = (T >= 1800) & (T <= 2700)
    sic_indices = np.where(sic_mask)[0]
    if len(sic_indices) > 0:
        sic_range = (float(r[sic_indices[0]]), float(r[sic_indices[-1]]))
    else:
        sic_range = (0.0, 0.0)

    return {
        "r_m": r,
        "T_C": T,
        "T_core_C": float(T[0]),
        "T_shell_C": float(T[-1]),
        "sic_zone_r_range_m": sic_range,
    }


def acheson_full_cycle(
    charge_mass_kg: float,
    SiO2_fraction: float = 0.5,
    C_fraction: float = 0.5,
    power_kW: float = 500.0,
    cycle_time_h: float = None,
) -> Dict:
    """Simulate a full Acheson furnace cycle.

    Parameters
    ----------
    charge_mass_kg : float
        Total charge mass [kg].
    SiO2_fraction : float
        Mass fraction of SiO₂ in charge.
    C_fraction : float
        Mass fraction of carbon in charge.
    power_kW : float
        Electrical power [kW].
    cycle_time_h : float
        Cycle duration [hours].

    Returns
    -------
    dict
        {"sic_yield_kg": float, "energy_kWh": float, "energy_per_kg_SiC": float,
         "co_produced_kg": float, "efficiency": float, "yield_fraction": float}
    """
    cycle_h = cycle_time_h or ACHESON["cycle_time_hours"]

    # Moles of reactants
    M_SiO2 = ACHESON["M_SiO2"]  # g/mol
    M_C = ACHESON["M_C"]
    M_SiC = ACHESON["M_SiC"]
    M_CO = ACHESON["M_CO"]

    mass_SiO2 = charge_mass_kg * SiO2_fraction * 1000  # g
    mass_C = charge_mass_kg * C_fraction * 1000  # g

    mol_SiO2 = mass_SiO2 / M_SiO2
    mol_C = mass_C / M_C

    # Stoichiometry: SiO₂ + 3C → SiC + 2CO
    # Limiting reagent
    mol_SiC_from_SiO2 = mol_SiO2
    mol_SiC_from_C = mol_C / 3.0
    mol_SiC_theoretical = min(mol_SiC_from_SiO2, mol_SiC_from_C)

    # Apply yield fraction (not all charge reaches reaction temperature)
    yield_frac = ACHESON["yield_fraction"]
    mol_SiC_actual = mol_SiC_theoretical * yield_frac
    mol_CO = mol_SiC_actual * ACHESON["CO_generation_mol_per_mol_SiC"]

    sic_mass_kg = mol_SiC_actual * M_SiC / 1000.0
    co_mass_kg = mol_CO * M_CO / 1000.0

    # Energy
    energy_kWh = power_kW * cycle_h
    energy_per_kg = energy_kWh / sic_mass_kg if sic_mass_kg > 0 else float("inf")

    # Thermodynamic efficiency
    delta_H = ACHESON["delta_H_kJ_mol"]  # kJ/mol
    Q_reaction = mol_SiC_actual * delta_H  # kJ
    Q_input = energy_kWh * 3600.0  # kJ
    efficiency = Q_reaction / Q_input if Q_input > 0 else 0.0

    return {
        "sic_yield_kg": sic_mass_kg,
        "co_produced_kg": co_mass_kg,
        "energy_kWh": energy_kWh,
        "energy_per_kg_SiC": energy_per_kg,
        "efficiency": efficiency,
        "yield_fraction": yield_frac,
        "mol_SiC": mol_SiC_actual,
        "cycle_time_h": cycle_h,
    }


def optimize_power_profile(
    charge_mass_kg: float,
    target_yield_kg: float,
    max_energy_kWh: float,
    SiO2_fraction: float = 0.5,
    C_fraction: float = 0.5,
) -> Dict:
    """Optimize power and cycle time to meet yield target within energy budget.

    Parameters
    ----------
    charge_mass_kg : float
    target_yield_kg : float
    max_energy_kWh : float
    SiO2_fraction : float
    C_fraction : float

    Returns
    -------
    dict
        {"optimal_power_kW": float, "optimal_cycle_h": float, "predicted_yield_kg": float,
         "energy_kWh": float, "feasible": bool}
    """
    # Scan power levels
    best = None
    for power_kW in np.linspace(100, 2000, 50):
        for cycle_h in np.linspace(12, 72, 30):
            result = acheson_full_cycle(charge_mass_kg, SiO2_fraction, C_fraction, power_kW, cycle_h)
            if result["energy_kWh"] <= max_energy_kWh and result["sic_yield_kg"] >= target_yield_kg:
                if best is None or result["energy_per_kg_SiC"] < best["energy_per_kg_SiC"]:
                    best = {
                        "optimal_power_kW": float(power_kW),
                        "optimal_cycle_h": float(cycle_h),
                        "predicted_yield_kg": result["sic_yield_kg"],
                        "energy_kWh": result["energy_kWh"],
                        "energy_per_kg_SiC": result["energy_per_kg_SiC"],
                        "feasible": True,
                    }

    if best is None:
        # Not feasible: return closest
        result = acheson_full_cycle(charge_mass_kg, SiO2_fraction, C_fraction, 1000, 36)
        return {
            "optimal_power_kW": 1000.0,
            "optimal_cycle_h": 36.0,
            "predicted_yield_kg": result["sic_yield_kg"],
            "energy_kWh": result["energy_kWh"],
            "energy_per_kg_SiC": result["energy_per_kg_SiC"],
            "feasible": False,
        }
    return best


def scale_up_analysis(
    current_mass_kg: float,
    target_mass_kg: float,
    current_power_kW: float = 500.0,
) -> Dict:
    """Predict scale-up requirements.

    Assumes power scales ~linearly with mass, cycle time ~log.

    Parameters
    ----------
    current_mass_kg : float
    target_mass_kg : float
    current_power_kW : float

    Returns
    -------
    dict
        Scale-up predictions.
    """
    scale_factor = target_mass_kg / current_mass_kg if current_mass_kg > 0 else 1.0
    # Power scales linearly
    target_power = current_power_kW * scale_factor
    # Cycle time scales as ~log (better heat penetration needs more time)
    base_cycle = ACHESON["cycle_time_hours"]
    target_cycle = base_cycle * (1 + 0.2 * np.log(scale_factor)) if scale_factor > 1 else base_cycle

    current = acheson_full_cycle(current_mass_kg, power_kW=current_power_kW)
    scaled = acheson_full_cycle(target_mass_kg, power_kW=target_power, cycle_time_h=target_cycle)

    return {
        "scale_factor": scale_factor,
        "current": {
            "mass_kg": current_mass_kg,
            "power_kW": current_power_kW,
            "sic_yield_kg": current["sic_yield_kg"],
            "energy_per_kg_SiC": current["energy_per_kg_SiC"],
        },
        "scaled": {
            "mass_kg": target_mass_kg,
            "power_kW": target_power,
            "cycle_time_h": target_cycle,
            "sic_yield_kg": scaled["sic_yield_kg"],
            "energy_per_kg_SiC": scaled["energy_per_kg_SiC"],
        },
    }


def electrification_solar_scenario(
    power_kW: float,
    cycle_time_h: float = 36.0,
    solar_capacity_factor: float = 0.25,
    storage_kWh: float = 0.0,
    region: str = "saudi_arabia",
) -> Dict:
    """Evaluate solar-powered Acheson scenario.

    Parameters
    ----------
    power_kW : float
        Required furnace power [kW].
    cycle_time_h : float
        Cycle duration [h].
    solar_capacity_factor : float
        Solar CF (Saudi ~0.25).
    storage_kWh : float
        Battery storage capacity [kWh].
    region : str
        Cost region.

    Returns
    -------
    dict
        Solar sizing, costs, comparison with grid.
    """
    energy_needed = power_kW * cycle_time_h  # kWh
    # Solar panel sizing: need to generate energy_needed in cycle_time_h
    solar_peak_kW = power_kW / solar_capacity_factor if solar_capacity_factor > 0 else float("inf")

    # Grid cost
    grid_cost_kwh = ENERGY_COSTS.get(region, 0.048)
    grid_cost = energy_needed * grid_cost_kwh

    # Solar PPA cost
    solar_cost_kwh = ENERGY_COSTS.get("saudi_solar_ppa", 0.015)
    solar_cost = energy_needed * solar_cost_kwh

    # Without storage: only ~CF fraction can be direct solar
    direct_solar_frac = min(solar_capacity_factor * 24 / cycle_time_h, 1.0) if cycle_time_h > 0 else 0
    if storage_kWh > 0:
        # Storage covers nighttime
        storage_hours = storage_kWh / power_kW if power_kW > 0 else 0
        direct_solar_frac = min((solar_capacity_factor * 24 + storage_hours) / cycle_time_h, 1.0)

    return {
        "energy_needed_kWh": energy_needed,
        "solar_peak_kW": solar_peak_kW,
        "direct_solar_fraction": direct_solar_frac,
        "grid_cost_usd": grid_cost,
        "solar_ppa_cost_usd": solar_cost,
        "savings_usd": grid_cost - solar_cost,
        "savings_pct": (1 - solar_cost / grid_cost) * 100 if grid_cost > 0 else 0,
        "region": region,
    }
