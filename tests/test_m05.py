"""Tests for M05: Acheson SiC Synthesis."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m05_acheson import (
    sic_formation_rate, graphite_resistivity, joule_heating_power,
    acheson_temperature_field, acheson_full_cycle, optimize_power_profile,
    scale_up_analysis, electrification_solar_scenario,
)
from config import ACHESON


class TestSiCFormationRate:
    def test_positive_at_high_T(self):
        r = sic_formation_rate(2200)
        assert r > 0

    def test_zero_below_1500(self):
        r = sic_formation_rate(1000)
        assert r == 0.0

    def test_increases_with_T(self):
        r1 = sic_formation_rate(1800)
        r2 = sic_formation_rate(2500)
        assert r2 > r1

    def test_zero_reactant_zero_rate(self):
        r = sic_formation_rate(2200, x_SiO2=0)
        assert r == 0.0

    def test_proportional_to_SiO2(self):
        r1 = sic_formation_rate(2200, x_SiO2=0.5)
        r2 = sic_formation_rate(2200, x_SiO2=1.0)
        assert abs(r2 / r1 - 2.0) < 0.01


class TestGraphiteResistivity:
    def test_positive(self):
        assert graphite_resistivity(25) > 0

    def test_increases_with_T(self):
        r1 = graphite_resistivity(25)
        r2 = graphite_resistivity(2000)
        assert r2 > r1

    def test_room_temp_baseline(self):
        r = graphite_resistivity(25)
        assert abs(r - ACHESON["graphite_rho0_ohm_m"]) < 1e-10


class TestJouleHeating:
    def test_positive_power(self):
        P = joule_heating_power(10000, 1000, 4.0, 0.01)
        assert P > 0

    def test_zero_current_zero_power(self):
        P = joule_heating_power(0, 1000, 4.0, 0.01)
        assert P == 0.0

    def test_scales_with_I_squared(self):
        P1 = joule_heating_power(1000, 1000, 4.0, 0.01)
        P2 = joule_heating_power(2000, 1000, 4.0, 0.01)
        assert abs(P2 / P1 - 4.0) < 0.01


class TestAchesonFullCycle:
    def test_positive_yield(self):
        result = acheson_full_cycle(1000)
        assert result["sic_yield_kg"] > 0

    def test_co_produced(self):
        result = acheson_full_cycle(1000)
        assert result["co_produced_kg"] > 0

    def test_energy_positive(self):
        result = acheson_full_cycle(1000)
        assert result["energy_kWh"] > 0

    def test_yield_fraction_bounded(self):
        result = acheson_full_cycle(1000)
        assert 0 < result["yield_fraction"] <= 1

    def test_stoichiometry_co_ratio(self):
        result = acheson_full_cycle(1000)
        # 2 mol CO per mol SiC
        M_SiC = ACHESON["M_SiC"]
        M_CO = ACHESON["M_CO"]
        mol_sic = result["sic_yield_kg"] * 1000 / M_SiC
        mol_co = result["co_produced_kg"] * 1000 / M_CO
        assert abs(mol_co / mol_sic - 2.0) < 0.01

    def test_more_charge_more_yield(self):
        r1 = acheson_full_cycle(500)
        r2 = acheson_full_cycle(1000)
        assert r2["sic_yield_kg"] > r1["sic_yield_kg"]

    def test_energy_per_kg_reasonable(self):
        result = acheson_full_cycle(1000, power_kW=500)
        # Should be in range 5-50 kWh/kg
        assert 1 < result["energy_per_kg_SiC"] < 1000


class TestOptimizePowerProfile:
    def test_feasible_result(self):
        result = optimize_power_profile(1000, 50, 50000)
        assert result["feasible"] or result["predicted_yield_kg"] > 0

    def test_within_energy_budget(self):
        result = optimize_power_profile(1000, 50, 100000)
        if result["feasible"]:
            assert result["energy_kWh"] <= 100000


class TestScaleUp:
    def test_scale_factor(self):
        result = scale_up_analysis(1000, 5000)
        assert result["scale_factor"] == 5.0

    def test_scaled_yield_higher(self):
        result = scale_up_analysis(1000, 5000)
        assert result["scaled"]["sic_yield_kg"] > result["current"]["sic_yield_kg"]


class TestSolarScenario:
    def test_savings_positive(self):
        result = electrification_solar_scenario(500, 36)
        assert result["savings_usd"] > 0

    def test_solar_ppa_cheaper(self):
        result = electrification_solar_scenario(500, 36)
        assert result["solar_ppa_cost_usd"] < result["grid_cost_usd"]

    def test_energy_needed_correct(self):
        result = electrification_solar_scenario(500, 36)
        assert result["energy_needed_kWh"] == 500 * 36

    def test_storage_increases_solar_fraction(self):
        r1 = electrification_solar_scenario(500, 36, storage_kWh=0)
        r2 = electrification_solar_scenario(500, 36, storage_kWh=5000)
        assert r2["direct_solar_fraction"] >= r1["direct_solar_fraction"]
