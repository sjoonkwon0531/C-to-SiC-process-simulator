"""Tests for M10: Energy/LCA & Economics."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m10_lca_econ import (
    energy_waterfall, co2_emissions, cogs_breakdown,
    electrification_scenarios, regional_comparison, npv_irr,
)


class TestEnergyWaterfall:
    def test_cumulative_correct(self):
        stages = {"sublimation": 250, "pvt": 500, "wafering": 50, "cmp": 20}
        r = energy_waterfall(stages)
        assert r["total_kWh"] == 820
        assert r["cumulative_kWh"][-1] == 820

    def test_pct_sum_100(self):
        stages = {"a": 100, "b": 200, "c": 300}
        r = energy_waterfall(stages)
        assert abs(sum(r["pct_by_stage"].values()) - 100) < 0.01

    def test_stages_order(self):
        stages = {"first": 10, "second": 20}
        r = energy_waterfall(stages)
        assert r["stages"] == ["first", "second"]


class TestCO2Emissions:
    def test_positive(self):
        co2 = co2_emissions(500, "saudi_arabia")
        assert co2 > 0

    def test_solar_less_than_current(self):
        c1 = co2_emissions(500, "saudi_arabia", "current")
        c2 = co2_emissions(500, "saudi_arabia", "solar_electric")
        assert c2 < c1

    def test_scales_with_energy(self):
        c1 = co2_emissions(100, "saudi_arabia")
        c2 = co2_emissions(200, "saudi_arabia")
        assert abs(c2 / c1 - 2.0) < 0.01

    def test_regions_differ(self):
        c1 = co2_emissions(500, "saudi_arabia")
        c2 = co2_emissions(500, "eu_average")
        assert c1 != c2


class TestCOGSBreakdown:
    def test_default_positive(self):
        r = cogs_breakdown()
        assert r["total_usd"] > 0

    def test_custom_costs(self):
        r = cogs_breakdown({"a": 100, "b": 200})
        assert r["total_usd"] == 300

    def test_pct_sum(self):
        r = cogs_breakdown()
        assert abs(sum(r["pct_by_category"].values()) - 100) < 0.1


class TestElectrificationScenarios:
    def test_three_scenarios(self):
        r = electrification_scenarios(500, "saudi_arabia")
        assert len(r) == 3
        assert "current" in r
        assert "solar_electric" in r

    def test_solar_cheapest(self):
        r = electrification_scenarios(500, "saudi_arabia")
        assert r["solar_electric"]["energy_cost_usd"] < r["current"]["energy_cost_usd"]

    def test_solar_lowest_co2(self):
        r = electrification_scenarios(500, "saudi_arabia")
        assert r["solar_electric"]["co2_kg"] < r["current"]["co2_kg"]


class TestRegionalComparison:
    def test_all_regions(self):
        r = regional_comparison()
        assert len(r) == 4

    def test_saudi_cheapest_energy(self):
        r = regional_comparison()
        assert r["saudi_arabia"]["energy_cost_usd"] <= r["usa"]["energy_cost_usd"]


class TestNPVIRR:
    def test_positive_npv(self):
        r = npv_irr(100e6, 30e6, 10e6, 15, 0.10)
        assert r["NPV"] > 0

    def test_irr_positive(self):
        r = npv_irr(100e6, 30e6, 10e6, 15, 0.10)
        assert r["IRR"] > 0

    def test_payback_reasonable(self):
        r = npv_irr(100e6, 30e6, 10e6, 15, 0.10)
        assert r["payback_years"] == 5.0

    def test_negative_npv_high_discount(self):
        r = npv_irr(1000e6, 30e6, 10e6, 5, 0.10)
        assert r["NPV"] < 0
