"""Tests for M09: SiC Power Device."""
import pytest
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.m09_device import (
    baliga_fom, mosfet_losses, aidc_power_savings,
    thermal_advantage, device_cost_projection,
)


class TestBaligaFOM:
    def test_all_materials(self):
        r = baliga_fom()
        assert "Si" in r
        assert "4H-SiC" in r
        assert "GaN" in r

    def test_sic_better_than_si(self):
        r = baliga_fom()
        assert r["4H-SiC"]["FOM_normalized"] > r["Si"]["FOM_normalized"]

    def test_si_normalized_one(self):
        r = baliga_fom()
        assert abs(r["Si"]["FOM_normalized"] - 1.0) < 0.01

    def test_single_material(self):
        r = baliga_fom("4H-SiC")
        assert "4H-SiC" in r
        assert len(r) == 1


class TestMOSFETLosses:
    def test_positive_losses(self):
        r = mosfet_losses(800, 50, 0.01, 100000)
        assert r["P_cond_W"] > 0
        assert r["P_sw_W"] > 0

    def test_efficiency_bounded(self):
        r = mosfet_losses(800, 50, 0.01, 100000)
        assert 0 < r["efficiency"] < 1

    def test_higher_freq_more_switching_loss(self):
        r1 = mosfet_losses(800, 50, 0.01, 50000)
        r2 = mosfet_losses(800, 50, 0.01, 200000)
        assert r2["P_sw_W"] > r1["P_sw_W"]

    def test_lower_Ron_less_conduction_loss(self):
        r1 = mosfet_losses(800, 50, 0.02, 100000)
        r2 = mosfet_losses(800, 50, 0.005, 100000)
        assert r2["P_cond_W"] < r1["P_cond_W"]


class TestAIDCPowerSavings:
    def test_positive_savings(self):
        r = aidc_power_savings(40, 1000, 0.94, 0.98)
        assert r["annual_kWh_saved"] > 0

    def test_cost_savings_positive(self):
        r = aidc_power_savings(40, 1000, 0.94, 0.98)
        assert r["annual_cost_saved_usd"] > 0

    def test_sic_lower_input(self):
        r = aidc_power_savings(40, 1000, 0.94, 0.98)
        assert r["sic_total_kW"] < r["si_total_kW"]


class TestThermalAdvantage:
    def test_sic_cooler(self):
        r = thermal_advantage(100, 25.0)
        assert r["4H-SiC"]["T_junction_C"] < r["Si"]["T_junction_C"]

    def test_all_materials_present(self):
        r = thermal_advantage(100, 25.0)
        assert len(r) == 3


class TestDeviceCostProjection:
    def test_positive_cost(self):
        r = device_cost_projection(2025, 800)
        assert r["cost_per_device_usd"] > 0

    def test_future_cheaper(self):
        r1 = device_cost_projection(2024, 800)
        r2 = device_cost_projection(2030, 800)
        assert r2["cost_per_device_usd"] < r1["cost_per_device_usd"]

    def test_dies_positive(self):
        r = device_cost_projection(2025, 800)
        assert r["dies_per_wafer"] > 0
        assert r["good_dies"] > 0
