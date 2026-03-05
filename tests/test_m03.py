"""Tests for M03: Halogen Purification."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m03_halogen_purify import (
    gibbs_free_energy, reaction_rate, purify_halogen,
    energy_balance, optimize_T_profile,
)
from config import METAL_CHLORIDE_THERMO


class TestGibbsFreeEnergy:
    def test_known_metals(self):
        for metal in METAL_CHLORIDE_THERMO:
            dG = gibbs_free_energy(metal, 1800)
            assert isinstance(dG, float)

    def test_invalid_metal_raises(self):
        with pytest.raises(ValueError):
            gibbs_free_energy("Unobtanium", 1800)

    def test_fe_spontaneous_at_high_T(self):
        dG = gibbs_free_energy("Fe", 1800)
        assert dG < 0  # should be spontaneous

    def test_temperature_dependence(self):
        dG1 = gibbs_free_energy("Fe", 1000)
        dG2 = gibbs_free_energy("Fe", 2000)
        # ΔG = ΔH - T·ΔS, with negative ΔS, higher T → less negative
        assert dG2 != dG1

    def test_units_kJ_mol(self):
        dG = gibbs_free_energy("Al", 1800)
        # Should be in range of hundreds of kJ/mol
        assert abs(dG) < 2000


class TestReactionRate:
    def test_positive_rate(self):
        r = reaction_rate("Fe", 1800, 1.0, 0.0)
        assert r > 0

    def test_zero_at_full_conversion(self):
        r = reaction_rate("Fe", 1800, 1.0, 1.0)
        assert r == 0.0

    def test_increases_with_T(self):
        r1 = reaction_rate("Fe", 1500, 1.0, 0.0)
        r2 = reaction_rate("Fe", 1800, 1.0, 0.0)
        assert r2 > r1

    def test_increases_with_pressure(self):
        r1 = reaction_rate("Fe", 1800, 0.5, 0.0)
        r2 = reaction_rate("Fe", 1800, 1.0, 0.0)
        assert r2 > r1

    def test_unknown_element_zero(self):
        r = reaction_rate("Unobtanium", 1800, 1.0, 0.0)
        assert r == 0.0


class TestPurifyHalogen:
    def test_reduces_impurities(self):
        imp = {"Fe": 200, "Al": 100, "Ti": 50}
        result = purify_halogen(imp, 1800, 1.0, 2.0, 3600)
        for el in imp:
            assert result["residual_impurities"][el] <= imp[el]

    def test_total_decreases(self):
        imp = {"Fe": 200, "Al": 100, "Ca": 150}
        result = purify_halogen(imp, 1800)
        assert result["total_residual_ppm"] < sum(imp.values())

    def test_higher_T_better(self):
        imp = {"Fe": 200, "Al": 100}
        r1 = purify_halogen(imp, 1500, duration_s=3600)
        r2 = purify_halogen(imp, 1900, duration_s=3600)
        assert r2["total_residual_ppm"] <= r1["total_residual_ppm"]

    def test_invalid_gas_raises(self):
        with pytest.raises(ValueError):
            purify_halogen({"Fe": 100}, 1800, gas_type="Ar")

    def test_thermodynamic_feasibility_present(self):
        result = purify_halogen({"Fe": 100}, 1800)
        assert "Fe" in result["thermodynamic_feasibility"]
        assert "spontaneous" in result["thermodynamic_feasibility"]["Fe"]


class TestEnergyBalance:
    def test_positive_energy(self):
        result = energy_balance(1800, 10)
        assert result["Q_total_kWh"] > 0

    def test_higher_T_more_energy(self):
        e1 = energy_balance(1500, 10)
        e2 = energy_balance(2000, 10)
        assert e2["Q_total_kWh"] > e1["Q_total_kWh"]

    def test_heating_dominates(self):
        result = energy_balance(1800, 10, duration_s=60)
        assert result["Q_heating_kWh"] > 0

    def test_insulation_reduces_loss(self):
        e1 = energy_balance(1800, 10, insulation_factor=1.0)
        e2 = energy_balance(1800, 10, insulation_factor=0.1)
        assert e2["Q_loss_kWh"] < e1["Q_loss_kWh"]


class TestOptimizeTProfile:
    def test_returns_optimal(self):
        imp = {"Fe": 200, "Al": 100}
        result = optimize_T_profile(imp, 10.0, n_points=5)
        assert "optimal_T_C" in result
        assert result["optimal_T_C"] >= 1500

    def test_profile_length(self):
        result = optimize_T_profile({"Fe": 100}, 10.0, n_points=5)
        assert len(result["profile"]) == 5
