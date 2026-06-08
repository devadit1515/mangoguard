"""Tests for the mango hopper CROPSAP x local-T model."""

from __future__ import annotations

import pytest

from mangoguard.risk.hopper import (
    T_LOWER_LIMIT_C,
    T_OPTIMUM_C,
    T_UPPER_LIMIT_C,
    hopper_risk,
)


def test_returns_value_in_0_1():
    assert 0.0 <= hopper_risk(50.0, 27.0) <= 1.0
    assert 0.0 <= hopper_risk(0.0, 27.0) <= 1.0
    assert 0.0 <= hopper_risk(100.0, 50.0) <= 1.0


def test_high_cropsap_at_optimal_t_yields_high_risk():
    """100% CROPSAP pressure at exactly 27 degC -> risk == 1.0."""
    assert hopper_risk(100.0, 27.0) == pytest.approx(1.0)


def test_zero_cropsap_yields_zero_risk():
    """No regional inoculum -> no hopper risk regardless of T."""
    assert hopper_risk(0.0, 27.0) == 0.0
    assert hopper_risk(0.0, 20.0) == 0.0
    assert hopper_risk(0.0, 35.0) == 0.0


def test_extreme_cold_dampens_risk_to_zero():
    """T at or below 18 degC kills the multiplier even with high pressure."""
    assert hopper_risk(100.0, 18.0) == 0.0
    assert hopper_risk(100.0, 10.0) == 0.0


def test_extreme_heat_dampens_risk_to_zero():
    """T at or above 36 degC kills the multiplier even with high pressure."""
    assert hopper_risk(100.0, 36.0) == 0.0
    assert hopper_risk(100.0, 40.0) == 0.0


def test_triangular_rising_limb_is_linear():
    """T 18 -> 27 should rise linearly from 0 to 1 with pressure=100%."""
    assert hopper_risk(100.0, 18.0) == 0.0
    assert hopper_risk(100.0, 22.5) == pytest.approx(0.5)
    assert hopper_risk(100.0, 27.0) == pytest.approx(1.0)


def test_triangular_falling_limb_is_linear():
    """T 27 -> 36 should fall linearly from 1 to 0 with pressure=100%."""
    assert hopper_risk(100.0, 27.0) == pytest.approx(1.0)
    assert hopper_risk(100.0, 31.5) == pytest.approx(0.5)
    assert hopper_risk(100.0, 36.0) == 0.0


def test_cropsap_pressure_scales_linearly():
    """At fixed optimal T, doubling pressure doubles risk."""
    assert hopper_risk(25.0, 27.0) == pytest.approx(0.25)
    assert hopper_risk(50.0, 27.0) == pytest.approx(0.50)
    assert hopper_risk(75.0, 27.0) == pytest.approx(0.75)


def test_cropsap_pressure_clamped_above_100():
    """Caller passing 150% (impossible but defensive) is clamped to 1.0."""
    assert hopper_risk(150.0, 27.0) == pytest.approx(1.0)


def test_cropsap_pressure_clamped_below_zero():
    """Caller passing -10 (bad data) is clamped to 0."""
    assert hopper_risk(-10.0, 27.0) == 0.0


def test_pure_function_no_state():
    assert hopper_risk(50.0, 27.0) == hopper_risk(50.0, 27.0)


def test_published_thermal_constants_match_icar_cish():
    """Guard against accidental drift of the literature-pinned T-band."""
    assert T_OPTIMUM_C == 27.0
    assert T_LOWER_LIMIT_C == 18.0
    assert T_UPPER_LIMIT_C == 36.0
