"""Tests for M08: Wafering & CMP."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m08_wafering import (
    wire_saw_yield, preston_mrr, cmp_process, wafer_cost, kerf_loss_optimization,
)


class TestWireSawYield:
    def test_positive_wafers(self):
        r = wire_saw_yield(25.0)
        assert r["n_wafers"] > 0

    def test_yield_bounded(self):
        r = wire_saw_yield(25.0)
        assert 0 < r["yield_pct"] < 100

    def test_longer_boule_more_wafers(self):
        r1 = wire_saw_yield(20.0)
        r2 = wire_saw_yield(40.0)
        assert r2["n_wafers"] >= r1["n_wafers"]

    def test_thinner_kerf_more_wafers(self):
        r1 = wire_saw_yield(25.0, kerf_width_mm=0.20)
        r2 = wire_saw_yield(25.0, kerf_width_mm=0.10)
        assert r2["n_wafers"] >= r1["n_wafers"]


class TestPrestonMRR:
    def test_positive_mrr(self):
        mrr = preston_mrr(1e-13, 30.0, 1.5)
        assert mrr > 0

    def test_proportional_to_pressure(self):
        m1 = preston_mrr(1e-13, 15.0, 1.5)
        m2 = preston_mrr(1e-13, 30.0, 1.5)
        assert abs(m2 / m1 - 2.0) < 0.01

    def test_proportional_to_velocity(self):
        m1 = preston_mrr(1e-13, 30.0, 1.0)
        m2 = preston_mrr(1e-13, 30.0, 2.0)
        assert abs(m2 / m1 - 2.0) < 0.01


class TestCMPProcess:
    def test_roughness_decreases(self):
        r = cmp_process(200, 0.5, "colloidal_silica", 120)
        assert r["final_Ra_nm"] < 200

    def test_cost_positive(self):
        r = cmp_process(200, 0.5, "colloidal_silica", 60)
        assert r["cost_usd"] > 0

    def test_longer_time_smoother(self):
        r1 = cmp_process(200, 0.5, "colloidal_silica", 30)
        r2 = cmp_process(200, 0.5, "colloidal_silica", 120)
        assert r2["final_Ra_nm"] <= r1["final_Ra_nm"]


class TestWaferCost:
    def test_positive_cost(self):
        c = wafer_cost(150, 5000)
        assert c > 0

    def test_higher_boule_cost_higher_wafer_cost(self):
        c1 = wafer_cost(150, 3000)
        c2 = wafer_cost(150, 6000)
        assert c2 > c1


class TestKerfOptimization:
    def test_returns_optimal(self):
        r = kerf_loss_optimization()
        assert "optimal_wire_mm" in r
        assert r["max_wafers"] > 0

    def test_thinner_wire_better(self):
        r = kerf_loss_optimization((0.06, 0.20))
        # Optimal should be on the thinner side
        assert r["optimal_wire_mm"] <= 0.12
