"""Tests for M01: Feedstock Characterization."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m01_feedstock import (
    select_feedstock, total_impurity_ppm, calculate_purification_path,
    estimate_purification_stages, feedstock_cost, compare_feedstocks,
)
from config import PETRO_COKE_GRADES, PURITY_GRADES


class TestSelectFeedstock:
    def test_valid_grades(self):
        for grade in PETRO_COKE_GRADES:
            props = select_feedstock(grade)
            assert "impurities_ppm" in props
            assert props["carbon_pct"] > 0

    def test_invalid_grade_raises(self):
        with pytest.raises(ValueError):
            select_feedstock("nonexistent")

    def test_returns_deep_copy(self):
        a = select_feedstock("green_coke")
        b = select_feedstock("green_coke")
        a["impurities_ppm"]["Fe"] = 0
        assert b["impurities_ppm"]["Fe"] == 500

    def test_carbon_pct_range(self):
        for grade in PETRO_COKE_GRADES:
            props = select_feedstock(grade)
            assert 0 < props["carbon_pct"] <= 1.0


class TestTotalImpurity:
    def test_known_sum(self):
        assert total_impurity_ppm({"Fe": 100, "Al": 200}) == 300

    def test_empty(self):
        assert total_impurity_ppm({}) == 0

    def test_positive(self):
        for grade in PETRO_COKE_GRADES:
            total = total_impurity_ppm(PETRO_COKE_GRADES[grade]["impurities_ppm"])
            assert total > 0


class TestPurificationPath:
    def test_already_meets_target(self):
        path = calculate_purification_path({"Fe": 1}, "metallurgical")
        assert all(v["required_removal_frac"] == 0 for v in path.values())

    def test_needs_reduction(self):
        imp = PETRO_COKE_GRADES["green_coke"]["impurities_ppm"]
        path = calculate_purification_path(imp, "semiconductor")
        for v in path.values():
            assert 0 <= v["required_removal_frac"] <= 1

    def test_invalid_target(self):
        with pytest.raises(ValueError):
            calculate_purification_path({"Fe": 100}, "nonexistent")

    def test_proportional_allocation(self):
        imp = {"Fe": 500, "Al": 500}
        path = calculate_purification_path(imp, "metallurgical")
        # total is 1000, target 10000 → already meets
        assert all(v["required_removal_frac"] == 0 for v in path.values())


class TestEstimateStages:
    def test_zero_stages_when_met(self):
        result = estimate_purification_stages({"Fe": 1}, "metallurgical")
        assert result["n_stages"] == 0

    def test_positive_stages(self):
        imp = PETRO_COKE_GRADES["green_coke"]["impurities_ppm"]
        result = estimate_purification_stages(imp, "semiconductor")
        assert result["n_stages"] > 0

    def test_residual_below_target(self):
        imp = PETRO_COKE_GRADES["green_coke"]["impurities_ppm"]
        result = estimate_purification_stages(imp, "chemical")
        assert result["predicted_residual_ppm"] <= result["target_total_ppm"]

    def test_invalid_removal_rate(self):
        with pytest.raises(ValueError):
            estimate_purification_stages({"Fe": 100}, "chemical", per_stage_removal=1.5)


class TestFeedstockCost:
    def test_positive_cost(self):
        result = feedstock_cost("green_coke", 1000)
        assert result["total_cost_usd"] > 0

    def test_zero_quantity(self):
        result = feedstock_cost("needle_coke", 0)
        assert result["total_cost_usd"] == 0

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            feedstock_cost("green_coke", -1)

    def test_needle_most_expensive(self):
        costs = {g: feedstock_cost(g, 1000)["total_cost_usd"] for g in PETRO_COKE_GRADES}
        assert costs["needle_coke"] > costs["green_coke"]


class TestCompareFeedstocks:
    def test_returns_all_grades(self):
        results = compare_feedstocks()
        assert len(results) == len(PETRO_COKE_GRADES)

    def test_needle_purest(self):
        results = compare_feedstocks()
        by_impurity = sorted(results, key=lambda x: x["total_impurity_ppm"])
        assert by_impurity[0]["grade"] == "needle_coke"
