"""Risk engine: Akem model behaviour, leaf wetness, variety, spray rules."""

from __future__ import annotations

import numpy as np

from aamrakshak.riskengine.anthracnose import (
    AnthracnoseInputs,
    anthracnose_risk,
    humid_thermal_ratio,
)
from aamrakshak.riskengine.leafwetness import (
    LeafWetnessSensor,
    estimate_lw_hours_from_rh,
)
from aamrakshak.riskengine.ppi import (
    VARIETY_SUSCEPTIBILITY,
    infection_risk_pct,
    spray_schedule_calendar,
    spray_schedule_early_warning,
)


def _base(**kw):
    d = dict(
        t_max_c=32, t_min_c=24, rh_morning_pct=80, leaf_wetness_hr=6, sunshine_hr=7, wind_speed_ms=2
    )
    d.update(kw)
    return AnthracnoseInputs(**d)


def test_risk_in_unit_interval():
    for lw in range(0, 18):
        r = anthracnose_risk(_base(leaf_wetness_hr=lw))
        assert 0.0 <= r <= 1.0


def test_leaf_wetness_and_humidity_raise_risk():
    assert anthracnose_risk(_base(leaf_wetness_hr=12)) > anthracnose_risk(_base(leaf_wetness_hr=0))
    assert anthracnose_risk(_base(rh_morning_pct=95)) > anthracnose_risk(_base(rh_morning_pct=55))


def test_sun_and_wind_lower_risk():
    assert anthracnose_risk(_base(sunshine_hr=10)) < anthracnose_risk(_base(sunshine_hr=2))
    assert anthracnose_risk(_base(wind_speed_ms=5)) < anthracnose_risk(_base(wind_speed_ms=0.5))


def test_htr_denominator_clamped_when_no_diurnal_range():
    # Tmax == Tmin must not raise; clamp keeps HTR finite.
    htr = humid_thermal_ratio(28.0, 28.0, 90.0)
    assert np.isfinite(htr)
    assert anthracnose_risk(_base(t_max_c=28, t_min_c=28, rh_morning_pct=95)) <= 1.0


def test_estimate_lw_monotone_and_bounded():
    assert estimate_lw_hours_from_rh(50) == 0.0
    assert estimate_lw_hours_from_rh(95) > estimate_lw_hours_from_rh(90)
    assert estimate_lw_hours_from_rh(100) <= 16.0


def test_sensor_separates_wet_and_dry():
    rng = np.random.default_rng(1)
    s = LeafWetnessSensor()
    thr = s.calibration_threshold()
    wet = [s.classify_wet(s.read_adc(0.9, rng), thr) for _ in range(200)]
    dry = [s.classify_wet(s.read_adc(0.05, rng), thr) for _ in range(200)]
    assert np.mean(wet) > 0.85
    assert np.mean(dry) < 0.15


def test_measured_lw_tracks_truth():
    rng = np.random.default_rng(2)
    s = LeafWetnessSensor()
    long = np.mean([s.measured_lw_hours(12.0, rng) for _ in range(50)])
    short = np.mean([s.measured_lw_hours(1.0, rng) for _ in range(50)])
    assert long > short


def test_variety_susceptibility_orders_risk():
    inp = _base(rh_morning_pct=92, leaf_wetness_hr=10)
    assert infection_risk_pct(inp, "alphonso") > infection_risk_pct(inp, "kesar")
    assert VARIETY_SUSCEPTIBILITY["alphonso"] > VARIETY_SUSCEPTIBILITY["totapuri"]


def test_calendar_schedule_count():
    events = spray_schedule_calendar(100, interval_days=12, first_spray_day=5)
    assert len(events) == len(range(5, 100, 12))
    assert all(e.reason == "calendar" for e in events)


def test_early_warning_respects_lockout():
    risk = [90.0] * 30  # persistently high
    events = spray_schedule_early_warning(risk, threshold=50, sustain_days=1, lockout_days=10)
    days = [e.day for e in events]
    # No two sprays closer than the lockout window.
    assert all(days[i + 1] - days[i] >= 10 for i in range(len(days) - 1))


def test_early_warning_silent_when_low():
    assert spray_schedule_early_warning([10.0] * 50, threshold=50) == []
