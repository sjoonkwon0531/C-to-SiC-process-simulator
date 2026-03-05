"""Tests for M06: Sublimation Purification."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m06_sublimation import (
    hertz_knudsen_rate, sic_vapor_species, impurity_partition,
    sublimation_purify, purity_vs_mass_loss, energy_consumption,
)


class TestHertzKnudsen:
    def test_positive_flux(self):
        J = hertz_knudsen_rate(2200, 100.0, 10.0, 40.10)
        assert J > 0

    def test_zero_when_eq(self):
        J = hertz_knudsen_rate(2200, 100.0, 100.0, 40.10)
        assert J == 0.0

    def test_zero_when_P_exceeds_Peq(self):
        J = hertz_knudsen_rate(2200, 50.0, 100.0, 40.10)
        assert J == 0.0

    def test_increases_with_driving_force(self):
        J1 = hertz_knudsen_rate(2200, 100.0, 50.0, 40.10)
        J2 = hertz_knudsen_rate(2200, 100.0, 10.0, 40.10)
        assert J2 > J1


class TestVaporSpecies:
    def test_all_species_present(self):
        result = sic_vapor_species(2200)
        assert "Si" in result
        assert "Si2C" in result
        assert "SiC2" in result
        assert "total" in result

    def test_positive_pressures(self):
        result = sic_vapor_species(2200)
        for species in ["Si", "Si2C", "SiC2"]:
            assert result[species] > 0

    def test_increases_with_T(self):
        r1 = sic_vapor_species(2000)
        r2 = sic_vapor_species(2300)
        assert r2["total"] > r1["total"]


class TestImpurityPartition:
    def test_k_eff_bounded(self):
        k = impurity_partition("Fe", 2200, 0.2)
        assert 0 < k < 1

    def test_B_high_partition(self):
        """Boron has k0~0.8, should have high k_eff."""
        k = impurity_partition("B", 2200, 0.2)
        assert k > 0.5

    def test_Fe_low_partition(self):
        """Fe has k0~1e-5, should be well rejected."""
        k = impurity_partition("Fe", 2200, 0.2)
        assert k < 0.01


class TestSublimationPurify:
    def test_purity_improves(self):
        imp = {"Fe": 100, "Al": 50, "B": 5}
        result = sublimation_purify(imp, 2200, 10, 3)
        assert result["total_final_ppm"] < result["total_initial_ppm"]

    def test_mass_loss_positive(self):
        imp = {"Fe": 100}
        result = sublimation_purify(imp, 2200, 10, 3)
        assert result["mass_loss_fraction"] > 0

    def test_more_passes_purer(self):
        imp = {"Fe": 100, "Al": 50}
        r1 = sublimation_purify(imp, 2200, 10, 1)
        r2 = sublimation_purify(imp, 2200, 10, 5)
        assert r2["total_final_ppm"] <= r1["total_final_ppm"]

    def test_grade_assignment(self):
        imp = {"Fe": 100, "Al": 50}
        result = sublimation_purify(imp, 2200, 10, 3)
        assert result["purity_grade"] in ["2N", "3N", "4N", "5N", "6N"]


class TestPareto:
    def test_pareto_has_results(self):
        imp = {"Fe": 100, "Al": 50}
        result = purity_vs_mass_loss(imp)
        assert len(result["temperatures"]) > 0
        assert len(result["pareto_front"]) > 0

    def test_pareto_front_non_empty(self):
        imp = {"Fe": 200, "Al": 100, "Ti": 30}
        result = purity_vs_mass_loss(imp)
        assert len(result["pareto_front"]) >= 1


class TestEnergy:
    def test_positive_energy(self):
        E = energy_consumption(2200, 1.0, 10.0)
        assert E > 0

    def test_higher_T_more_energy(self):
        E1 = energy_consumption(2000, 1.0, 10.0)
        E2 = energy_consumption(2400, 1.0, 10.0)
        assert E2 > E1

    def test_scales_with_mass(self):
        E1 = energy_consumption(2200, 1.0, 10.0)
        E2 = energy_consumption(2200, 2.0, 10.0)
        assert abs(E2 / E1 - 2.0) < 0.01
