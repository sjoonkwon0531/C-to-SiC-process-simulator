"""Tests for M04: Thermal Treatment."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m04_thermal import (
    pyrolysis_rate, pyrolysis_kinetics, generate_T_profile,
    crystallinity_evolution, heat_conduction_1d, thermal_treatment,
    microwave_vs_conventional,
)


class TestPyrolysisRate:
    def test_positive_rate(self):
        r = pyrolysis_rate(800, 0.0)
        assert r > 0

    def test_zero_at_full_conversion(self):
        r = pyrolysis_rate(800, 1.0)
        assert r == 0.0

    def test_increases_with_T(self):
        r1 = pyrolysis_rate(500, 0.0)
        r2 = pyrolysis_rate(800, 0.0)
        assert r2 > r1

    def test_decreases_with_alpha(self):
        r1 = pyrolysis_rate(800, 0.1)
        r2 = pyrolysis_rate(800, 0.9)
        assert r1 > r2


class TestPyrolysisKinetics:
    def test_alpha_monotonic(self):
        profile = [25 + i * 5 for i in range(200)]  # ramp to 1020°C
        result = pyrolysis_kinetics(profile, dt_s=60.0)
        for i in range(1, len(result["alpha"])):
            assert result["alpha"][i] >= result["alpha"][i-1]

    def test_alpha_bounded(self):
        profile = [1000] * 500
        result = pyrolysis_kinetics(profile, dt_s=60.0)
        assert all(0 <= a <= 1 for a in result["alpha"])

    def test_output_shapes(self):
        profile = [500] * 100
        result = pyrolysis_kinetics(profile, dt_s=1.0)
        assert len(result["time_s"]) == 100
        assert len(result["alpha"]) == 100


class TestGenerateProfile:
    def test_starts_at_T_start(self):
        profile = generate_T_profile(1000, 10, 3600, T_start_C=25)
        assert profile[0] == 25.0

    def test_reaches_T_max(self):
        profile = generate_T_profile(1000, 10, 3600)
        assert max(profile) >= 999.0  # approximately T_max

    def test_hold_phase(self):
        profile = generate_T_profile(500, 10, 7200, dt_s=60)
        # Last points should all be at T_max
        assert profile[-1] == pytest.approx(500, abs=1)


class TestCrystallinity:
    def test_zero_at_zero_time(self):
        assert crystallinity_evolution(1000, 0) == 0.0

    def test_bounded_0_1(self):
        X = crystallinity_evolution(1200, 36000)
        assert 0 <= X <= 1

    def test_increases_with_time(self):
        X1 = crystallinity_evolution(1200, 1000)
        X2 = crystallinity_evolution(1200, 10000)
        assert X2 >= X1

    def test_increases_with_T(self):
        X1 = crystallinity_evolution(800, 3600)
        X2 = crystallinity_evolution(1200, 3600)
        assert X2 >= X1

    def test_zero_T_returns_zero(self):
        assert crystallinity_evolution(0, 3600) == 0.0


class TestHeatConduction:
    def test_center_approaches_surface(self):
        result = heat_conduction_1d(25, 1000, 0.01, 1000.0)
        assert result["T_center_C"] > 25
        assert result["T_center_C"] <= 1000

    def test_surface_maintained(self):
        result = heat_conduction_1d(25, 500, 0.005, 100.0)
        assert result["T_final_C"][-1] == pytest.approx(500, abs=5)


class TestThermalTreatment:
    def test_volatile_reduces(self):
        result = thermal_treatment(10, 1200, 5.0, 3600, volatile_pct=10.0)
        assert result["final_volatile_pct"] <= 10.0

    def test_mass_loss_positive(self):
        result = thermal_treatment(10, 1200, 5.0, 3600, volatile_pct=10.0)
        assert result["mass_loss_kg"] >= 0

    def test_energy_positive(self):
        result = thermal_treatment(10, 1200)
        assert result["energy_kWh"] > 0

    def test_higher_T_more_removal(self):
        r1 = thermal_treatment(10, 800, 5.0, 3600, 10.0)
        r2 = thermal_treatment(10, 1200, 5.0, 3600, 10.0)
        assert r2["final_volatile_pct"] <= r1["final_volatile_pct"]


class TestMicrowaveComparison:
    def test_microwave_saves_energy(self):
        result = microwave_vs_conventional(10, 1200)
        assert result["microwave"]["energy_kWh"] < result["conventional"]["energy_kWh"]

    def test_saving_pct_positive(self):
        result = microwave_vs_conventional(10, 1200)
        assert result["energy_saving_pct"] > 0
