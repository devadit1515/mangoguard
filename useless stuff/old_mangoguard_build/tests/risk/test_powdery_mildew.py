"""Tests for the powdery mildew T-band x RH window model."""

from __future__ import annotations

import pytest

from mangoguard.risk.powdery_mildew import (
    RH_OPTIMAL_BAND,
    T_MAX_OPTIMAL_BAND,
    T_MIN_OPTIMAL_BAND,
    PowderyMildewInputs,
    powdery_mildew_risk,
)


def _ideal_inputs() -> PowderyMildewInputs:
    """Center of all three published bands -> peak risk."""
    return PowderyMildewInputs(t_max_c=24.0, t_min_c=12.5, rh_pct=68.0)


def test_returns_value_in_0_1():
    assert 0.0 <= powdery_mildew_risk(_ideal_inputs()) <= 1.0


def test_optimal_conditions_yield_high_risk():
    """All three variables centered in their bands -> risk == 1.0."""
    p = powdery_mildew_risk(_ideal_inputs())
    assert p == pytest.approx(1.0)


def test_inside_band_edges_yields_full_risk():
    """At an exact band edge the kernel is still 1.0 (inclusive band)."""
    edge_inputs = PowderyMildewInputs(
        t_max_c=T_MAX_OPTIMAL_BAND[0],
        t_min_c=T_MIN_OPTIMAL_BAND[0],
        rh_pct=RH_OPTIMAL_BAND[0],
    )
    assert powdery_mildew_risk(edge_inputs) == pytest.approx(1.0)


def test_too_hot_yields_low_risk():
    """Pre-monsoon hot day -- Tmax 38, well outside [17, 31]."""
    inp = PowderyMildewInputs(t_max_c=38.0, t_min_c=24.0, rh_pct=68.0)
    p = powdery_mildew_risk(inp)
    assert p < 0.2


def test_too_cold_yields_low_risk():
    """Cold winter night -- Tmin 6, well below [11, 14]."""
    inp = PowderyMildewInputs(t_max_c=22.0, t_min_c=6.0, rh_pct=68.0)
    p = powdery_mildew_risk(inp)
    assert p < 0.5


def test_too_dry_yields_low_risk():
    """RH 30%, way below [64, 72] band."""
    inp = PowderyMildewInputs(t_max_c=24.0, t_min_c=12.5, rh_pct=30.0)
    p = powdery_mildew_risk(inp)
    assert p < 0.1


def test_too_humid_yields_lower_risk_than_optimal():
    """RH 95% is above the band -- powdery mildew prefers moderate humidity,
    unlike anthracnose which loves saturation."""
    high_rh = PowderyMildewInputs(t_max_c=24.0, t_min_c=12.5, rh_pct=95.0)
    p = powdery_mildew_risk(high_rh)
    assert p < 0.5
    assert p < powdery_mildew_risk(_ideal_inputs())


def test_inputs_dataclass_is_frozen():
    inp = _ideal_inputs()
    with pytest.raises((AttributeError, Exception)):
        inp.t_max_c = 99.0  # type: ignore[misc]


def test_pure_function_no_state():
    inp = _ideal_inputs()
    assert powdery_mildew_risk(inp) == powdery_mildew_risk(inp)


def test_sigmas_kwarg_overrides_defaults():
    """Tightening sigma makes off-band inputs decay faster."""
    off_band = PowderyMildewInputs(t_max_c=35.0, t_min_c=12.5, rh_pct=68.0)
    default_p = powdery_mildew_risk(off_band)
    tight_p = powdery_mildew_risk(off_band, sigmas={"t_min": 2.5, "t_max": 1.0, "rh": 7.0})
    assert tight_p < default_p


def test_published_band_constants_match_nhb_icar_cish():
    """Guard against accidental drift of the literature-pinned bands."""
    assert T_MIN_OPTIMAL_BAND == (11.0, 14.0)
    assert T_MAX_OPTIMAL_BAND == (17.0, 31.0)
    assert RH_OPTIMAL_BAND == (64.0, 72.0)


def test_monotone_decreasing_as_tmax_moves_away_from_band():
    """Risk must drop monotonically as Tmax moves further above the upper band."""
    base_tmin = 12.5
    base_rh = 68.0
    p_31 = powdery_mildew_risk(PowderyMildewInputs(31.0, base_tmin, base_rh))
    p_33 = powdery_mildew_risk(PowderyMildewInputs(33.0, base_tmin, base_rh))
    p_35 = powdery_mildew_risk(PowderyMildewInputs(35.0, base_tmin, base_rh))
    assert p_31 > p_33 > p_35


def test_three_kernels_multiply_not_average():
    """Two-of-three-variables-wrong must NOT score as 'half risk' -- the
    product semantics means risk requires ALL three to align."""
    two_wrong = PowderyMildewInputs(t_max_c=40.0, t_min_c=5.0, rh_pct=68.0)
    p = powdery_mildew_risk(two_wrong)
    assert p < 0.05
