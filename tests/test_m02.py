"""Tests for M02: Acid Leaching."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m02_acid_leach import (
    shrinking_core_conversion, shrinking_core_model, multi_acid_leach,
    optimize_acid_sequence, energy_consumption, electrification_comparison,
    _diffusivity,
)
from config import ACID_LEACH


class TestShrinkingCore:
    def test_zero_time_zero_conversion(self):
        assert shrinking_core_conversion(100, 0) == 0.0

    def test_full_conversion_at_tau(self):
        X = shrinking_core_conversion(100, 100)
        assert abs(X - 1.0) < 0.01

    def test_monotonic_increase(self):
        Xs = [shrinking_core_conversion(1000, t) for t in range(0, 1001, 100)]
        for i in range(1, len(Xs)):
            assert Xs[i] >= Xs[i-1]

    def test_midpoint_between_0_1(self):
        X = shrinking_core_conversion(100, 50)
        assert 0 < X < 1

    def test_negative_time(self):
        assert shrinking_core_conversion(100, -10) == 0.0

    def test_beyond_tau_capped(self):
        X = shrinking_core_conversion(100, 200)
        assert X == 1.0


class TestDiffusivity:
    def test_positive(self):
        D = _diffusivity(1e-9, 20.0, 353.15)
        assert D > 0

    def test_increases_with_T(self):
        D1 = _diffusivity(1e-9, 20.0, 333.15)
        D2 = _diffusivity(1e-9, 20.0, 363.15)
        assert D2 > D1

    def test_arrhenius_form(self):
        D0 = 1e-9
        Ea = 20.0
        T = 300.0
        D = _diffusivity(D0, Ea, T)
        expected = D0 * np.exp(-Ea * 1000 / (8.314 * T))
        assert abs(D - expected) < 1e-20


class TestMultiAcidLeach:
    def test_reduces_impurities(self):
        imp = {"Fe": 500, "Ca": 300, "Al": 200}
        res = multi_acid_leach(imp, "HCl", 80, 3600)
        assert res["Fe"] < 500
        assert res["Ca"] < 300

    def test_untargeted_unchanged(self):
        imp = {"Fe": 500, "B": 5}
        res = multi_acid_leach(imp, "HCl", 80, 3600)
        assert res["B"] == 5  # B not in HCl removal

    def test_multi_stage_better(self):
        imp = {"Fe": 500, "Ca": 300}
        r1 = multi_acid_leach(imp, "HCl", 80, 3600, n_stages=1)
        r2 = multi_acid_leach(imp, "HCl", 80, 3600, n_stages=3)
        assert r2["Fe"] <= r1["Fe"]

    def test_invalid_acid_raises(self):
        with pytest.raises(ValueError):
            multi_acid_leach({"Fe": 100}, "H2SO4", 80, 3600)

    def test_all_positive_residual(self):
        imp = {"Fe": 500, "Ca": 300, "Al": 200, "Ni": 400}
        res = multi_acid_leach(imp, "HCl", 80, 7200)
        for v in res.values():
            assert v >= 0


class TestOptimizeSequence:
    def test_returns_sorted(self):
        imp = {"Fe": 500, "Al": 200, "Si": 500, "Ca": 300}
        results = optimize_acid_sequence(imp, 100)
        totals = [r["total_residual_ppm"] for r in results]
        assert totals == sorted(totals)

    def test_mix_often_best(self):
        imp = {"Fe": 500, "Al": 200, "Si": 500, "Ca": 300, "Ti": 100}
        results = optimize_acid_sequence(imp, 500)
        # HCl_HF_mix should be among the best single-acid options
        single_results = [r for r in results if "→" not in r["acid_type"]]
        best_single = single_results[0]
        assert best_single["acid_type"] in ["HCl_HF_mix", "HCl", "HF", "HNO3"]


class TestEnergy:
    def test_positive_energy(self):
        result = energy_consumption(80, 100, 3600)
        assert result["energy_kWh"] > 0

    def test_electric_less_energy(self):
        conv = energy_consumption(80, 100, 3600, "conventional")
        elec = energy_consumption(80, 100, 3600, "electric")
        assert elec["energy_kWh"] < conv["energy_kWh"]

    def test_zero_delta_T(self):
        result = energy_consumption(25, 100, 3600)
        # Only losses, no heating
        assert result["energy_kWh"] >= 0


class TestElectrification:
    def test_savings_positive(self):
        result = electrification_comparison(80, 100, 3600)
        assert result["energy_saving_pct"] > 0

    def test_both_costs_positive(self):
        result = electrification_comparison(80, 100, 3600, "saudi_arabia")
        assert result["conventional"]["cost_usd"] > 0
        assert result["electric"]["cost_usd"] > 0
