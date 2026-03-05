"""Tests for M07: PVT Crystal Growth."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m07_pvt_growth import (
    stefan_maxwell_flux, growth_rate, thermal_stress,
    defect_density, pvt_simulation, scale_up_150_to_200, energy_per_wafer,
)


class TestStefanMaxwellFlux:
    def test_positive_flux(self):
        result = stefan_maxwell_flux(2200, 2100, 20, 0.03)
        assert result["total"] > 0

    def test_all_species(self):
        result = stefan_maxwell_flux(2200, 2100, 20, 0.03)
        for s in ["Si", "Si2C", "SiC2"]:
            assert s in result

    def test_higher_dT_higher_flux(self):
        r1 = stefan_maxwell_flux(2150, 2100, 20, 0.03)
        r2 = stefan_maxwell_flux(2250, 2100, 20, 0.03)
        assert r2["total"] > r1["total"]

    def test_zero_when_no_gradient(self):
        result = stefan_maxwell_flux(2100, 2100, 20, 0.03)
        assert result["total"] == 0.0 or result["total"] < 1e-10


class TestGrowthRate:
    def test_positive_rate(self):
        v = growth_rate(2200, 2100, 20)
        assert v > 0

    def test_zero_no_gradient(self):
        v = growth_rate(2100, 2100, 20)
        assert v == 0.0

    def test_typical_range(self):
        v = growth_rate(2200, 2100, 20)
        assert 0.05 < v < 5.0  # mm/h

    def test_higher_P_slower(self):
        v1 = growth_rate(2200, 2100, 10)
        v2 = growth_rate(2200, 2100, 40)
        assert v1 > v2

    def test_negative_gradient_zero(self):
        v = growth_rate(2000, 2100, 20)
        assert v == 0.0


class TestThermalStress:
    def test_positive_stress(self):
        s = thermal_stress((2100, 2090), 150, 20)
        assert s > 0

    def test_larger_dT_larger_stress(self):
        s1 = thermal_stress((2100, 2095), 150, 20)
        s2 = thermal_stress((2100, 2080), 150, 20)
        assert s2 > s1

    def test_zero_when_uniform(self):
        s = thermal_stress((2100, 2100), 150, 20)
        assert s == 0.0


class TestDefectDensity:
    def test_positive_defects(self):
        d = defect_density(0.3, 20.0)
        assert d["BPD_cm2"] > 0
        assert d["TSD_cm2"] > 0

    def test_tsd_less_than_bpd(self):
        d = defect_density(0.3, 20.0)
        assert d["TSD_cm2"] < d["BPD_cm2"]

    def test_faster_growth_more_defects(self):
        d1 = defect_density(0.1, 10.0)
        d2 = defect_density(0.5, 10.0)
        assert d2["BPD_cm2"] > d1["BPD_cm2"]


class TestPVTSimulation:
    def test_returns_all_keys(self):
        r = pvt_simulation(2200, 2100, 20, 100, 150)
        assert "thickness_mm" in r
        assert "growth_rate_mm_h" in r
        assert "defects" in r
        assert "energy_kWh" in r
        assert "quality_grade" in r

    def test_thickness_positive(self):
        r = pvt_simulation(2200, 2100, 20, 100, 150)
        assert r["thickness_mm"] > 0

    def test_energy_positive(self):
        r = pvt_simulation(2200, 2100, 20, 100, 150)
        assert r["energy_kWh"] > 0

    def test_quality_grade_valid(self):
        r = pvt_simulation(2200, 2100, 20, 100, 150)
        assert r["quality_grade"] in ["prime", "standard", "mechanical", "research"]


class TestScaleUp:
    def test_returns_both_sizes(self):
        cond = {"T_source": 2200, "T_seed": 2100, "P_Ar": 20, "growth_time_h": 100}
        r = scale_up_150_to_200(cond)
        assert "current_150mm" in r
        assert "predicted_200mm" in r
        assert "challenges" in r

    def test_challenges_non_empty(self):
        cond = {"T_source": 2200, "T_seed": 2100, "P_Ar": 20, "growth_time_h": 100}
        r = scale_up_150_to_200(cond)
        assert len(r["challenges"]) > 0


class TestEnergyPerWafer:
    def test_positive(self):
        E = energy_per_wafer(150, 0.35, 0.2)
        assert E > 0

    def test_faster_growth_less_energy(self):
        E1 = energy_per_wafer(150, 0.35, 0.1)
        E2 = energy_per_wafer(150, 0.35, 0.5)
        assert E2 < E1
