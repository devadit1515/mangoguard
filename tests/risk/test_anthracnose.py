"""Tests for the anthracnose HTR logistic-regression model (Akem 2006)."""

from __future__ import annotations

import math

import pytest

from mangoguard.risk.anthracnose import (
    DEFAULT_COEFFS,
    AnthracnoseInputs,
    anthracnose_risk,
)


def _ideal_konkan_monsoon() -> AnthracnoseInputs:
    """High-risk Konkan-monsoon-night scenario.

    Saturated morning RH, narrow diurnal range, long overnight leaf
    wetness, no sun, low wind -- the textbook anthracnose-conducive
    profile.
    """
    return AnthracnoseInputs(
        t_max_c=29.5,
        t_min_c=23.8,
        rh_morning_pct=95.0,
        leaf_wetness_hr=18.0,
        sunshine_hr=0.5,
        wind_speed_ms=1.0,
    )


def _hot_dry_summer() -> AnthracnoseInputs:
    """Low-risk pre-monsoon Konkan summer day."""
    return AnthracnoseInputs(
        t_max_c=38.0,
        t_min_c=22.0,
        rh_morning_pct=45.0,
        leaf_wetness_hr=0.0,
        sunshine_hr=10.0,
        wind_speed_ms=4.0,
    )


def test_returns_value_in_0_1():
    assert 0.0 <= anthracnose_risk(_ideal_konkan_monsoon()) <= 1.0
    assert 0.0 <= anthracnose_risk(_hot_dry_summer()) <= 1.0


def test_high_htr_long_wetness_yields_risk_above_0_7():
    p = anthracnose_risk(_ideal_konkan_monsoon())
    assert p > 0.7, f"expected high anthracnose risk, got {p:.3f}"


def test_low_htr_short_wetness_yields_risk_below_0_2():
    p = anthracnose_risk(_hot_dry_summer())
    assert p < 0.2, f"expected low anthracnose risk, got {p:.3f}"


def test_div_by_zero_edge_handled_when_tmax_equals_tmin():
    """Saturated overcast (Tmax == Tmin) must not raise."""
    inp = AnthracnoseInputs(
        t_max_c=26.0,
        t_min_c=26.0,
        rh_morning_pct=98.0,
        leaf_wetness_hr=20.0,
        sunshine_hr=0.0,
        wind_speed_ms=0.5,
    )
    p = anthracnose_risk(inp)
    assert 0.0 <= p <= 1.0
    assert p > 0.9, f"expected near-1.0 risk for saturated profile, got {p:.3f}"


def test_div_by_zero_edge_handled_when_tmax_below_tmin():
    inp = AnthracnoseInputs(
        t_max_c=25.5,
        t_min_c=25.7,
        rh_morning_pct=92.0,
        leaf_wetness_hr=10.0,
        sunshine_hr=0.0,
        wind_speed_ms=1.0,
    )
    p = anthracnose_risk(inp)
    assert 0.0 <= p <= 1.0


def test_pure_function_no_state():
    inp = _ideal_konkan_monsoon()
    a = anthracnose_risk(inp)
    b = anthracnose_risk(inp)
    c = anthracnose_risk(inp)
    assert a == b == c


def test_inputs_dataclass_is_frozen():
    inp = _ideal_konkan_monsoon()
    with pytest.raises((AttributeError, Exception)):
        inp.t_max_c = 99.0  # type: ignore[misc]


def test_coeffs_kwarg_overrides_defaults():
    inp = _ideal_konkan_monsoon()
    p_default = anthracnose_risk(inp)
    pushed_low = anthracnose_risk(
        inp,
        coeffs={
            "beta_0": -50.0,
            "beta_htr": 0.0,
            "beta_lw": 0.0,
            "beta_sun": 0.0,
            "beta_wind": 0.0,
        },
    )
    assert pushed_low < 0.01
    assert pushed_low != pytest.approx(p_default, abs=0.01)


def test_default_coeffs_match_akem_2006_published_values():
    """Guard against accidental coefficient drift."""
    assert DEFAULT_COEFFS == {
        "beta_0": -4.2,
        "beta_htr": 0.085,
        "beta_lw": 0.32,
        "beta_sun": -0.18,
        "beta_wind": -0.12,
    }


def test_logistic_squashes_extreme_z_without_overflow():
    extreme_high = AnthracnoseInputs(
        t_max_c=26.0,
        t_min_c=25.9,
        rh_morning_pct=99.0,
        leaf_wetness_hr=24.0,
        sunshine_hr=0.0,
        wind_speed_ms=0.0,
    )
    assert math.isclose(anthracnose_risk(extreme_high), 1.0, abs_tol=1e-3)

    extreme_low_coeffs = {
        "beta_0": -100.0,
        "beta_htr": 0.0,
        "beta_lw": 0.0,
        "beta_sun": 0.0,
        "beta_wind": 0.0,
    }
    assert math.isclose(
        anthracnose_risk(extreme_high, coeffs=extreme_low_coeffs), 0.0, abs_tol=1e-3
    )


def test_monotone_increasing_in_leaf_wetness():
    base = _ideal_konkan_monsoon()
    p_short = anthracnose_risk(
        AnthracnoseInputs(
            t_max_c=base.t_max_c,
            t_min_c=base.t_min_c,
            rh_morning_pct=base.rh_morning_pct,
            leaf_wetness_hr=2.0,
            sunshine_hr=base.sunshine_hr,
            wind_speed_ms=base.wind_speed_ms,
        )
    )
    p_long = anthracnose_risk(
        AnthracnoseInputs(
            t_max_c=base.t_max_c,
            t_min_c=base.t_min_c,
            rh_morning_pct=base.rh_morning_pct,
            leaf_wetness_hr=20.0,
            sunshine_hr=base.sunshine_hr,
            wind_speed_ms=base.wind_speed_ms,
        )
    )
    assert p_long >= p_short


def test_monotone_decreasing_in_sunshine():
    base = _ideal_konkan_monsoon()
    p_overcast = anthracnose_risk(
        AnthracnoseInputs(
            t_max_c=base.t_max_c,
            t_min_c=base.t_min_c,
            rh_morning_pct=base.rh_morning_pct,
            leaf_wetness_hr=base.leaf_wetness_hr,
            sunshine_hr=0.0,
            wind_speed_ms=base.wind_speed_ms,
        )
    )
    p_sunny = anthracnose_risk(
        AnthracnoseInputs(
            t_max_c=base.t_max_c,
            t_min_c=base.t_min_c,
            rh_morning_pct=base.rh_morning_pct,
            leaf_wetness_hr=base.leaf_wetness_hr,
            sunshine_hr=10.0,
            wind_speed_ms=base.wind_speed_ms,
        )
    )
    assert p_sunny <= p_overcast
