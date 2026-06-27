"""Tests for the PPI combiner."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from mangoguard.risk.ppi import (
    DEFAULT_WEIGHTS,
    NDRE_ANOMALY_BOOST,
    compute_ppi,
    primary_pathogen,
)
from mangoguard.schema import BlockObservation, ConnectorSource

_DAY = date(2025, 7, 15)


def _imd_row(block_id: str, when: datetime, **kw) -> BlockObservation:
    return BlockObservation(block_id=block_id, ts=when, source=ConnectorSource.IMD, **kw)


def _seed_high_anthracnose_window(store, block_id: str) -> None:
    """Seven IMD observations spanning [_DAY - 7, _DAY) with monsoon-conducive values."""
    base = datetime.combine(_DAY - timedelta(days=6), datetime.min.time(), tzinfo=timezone.utc)
    for i in range(7):
        store.insert(
            _imd_row(
                block_id,
                base + timedelta(days=i),
                t_air_c=27.0 + (i * 0.1),
                rh_pct=92.0,
                leaf_wetness_hr=4.0,
                wind_speed_ms=1.5,
                solar_w_m2=120.0,
            )
        )


def _seed_low_pressure_window(store, block_id: str) -> None:
    """Hot-dry-summer week with realistic diurnal range.

    Insert two readings per day (day + night) so Tmax/Tmin differ by
    ~14 degC, which keeps the anthracnose HTR (= morning RH / dT_range)
    in a low-risk regime instead of saturating via the dT=0 clamp.
    """
    base = datetime.combine(_DAY - timedelta(days=6), datetime.min.time(), tzinfo=timezone.utc)
    for i in range(7):
        # Daytime reading: hot, dry, sunny, breezy
        store.insert(
            _imd_row(
                block_id,
                base + timedelta(days=i, hours=12),
                t_air_c=38.0,
                rh_pct=35.0,
                leaf_wetness_hr=0.0,
                wind_speed_ms=4.0,
                solar_w_m2=900.0,
            )
        )
        # Nighttime reading: cool-ish, still dry
        store.insert(
            _imd_row(
                block_id,
                base + timedelta(days=i, hours=2),
                t_air_c=24.0,
                rh_pct=50.0,
                leaf_wetness_hr=0.0,
                wind_speed_ms=3.0,
                solar_w_m2=0.0,
            )
        )


def test_ppi_returns_dict_with_expected_keys(store):
    _seed_high_anthracnose_window(store, "block1")
    result = compute_ppi(store, "block1", _DAY)
    assert set(result.keys()) == {"ppi", "anth", "pm", "hop", "ndre_anomaly"}


def test_ppi_in_0_100_range(store):
    _seed_high_anthracnose_window(store, "block1")
    result = compute_ppi(store, "block1", _DAY)
    assert 0.0 <= result["ppi"] <= 100.0
    assert 0.0 <= result["anth"] <= 1.0
    assert 0.0 <= result["pm"] <= 1.0
    assert 0.0 <= result["hop"] <= 1.0


def test_anthracnose_conducive_window_yields_high_ppi(store):
    _seed_high_anthracnose_window(store, "block1")
    result = compute_ppi(store, "block1", _DAY)
    assert result["ppi"] > 30.0, f"expected high PPI, got {result['ppi']:.1f}"
    assert result["anth"] > 0.5


def test_hot_dry_summer_window_yields_low_ppi(store):
    _seed_low_pressure_window(store, "block1")
    result = compute_ppi(store, "block1", _DAY)
    assert result["ppi"] < 20.0, f"expected low PPI, got {result['ppi']:.1f}"


def test_empty_store_yields_finite_ppi_from_neutral_defaults(store):
    """No observations at all -> neutral defaults give a finite PPI in [0, 100]."""
    result = compute_ppi(store, "missing-block", _DAY)
    assert 0.0 <= result["ppi"] <= 100.0
    assert result["ndre_anomaly"] is False


def test_weights_sum_check_warns_if_not_unity(store, caplog):
    _seed_high_anthracnose_window(store, "block1")
    with caplog.at_level("WARNING"):
        compute_ppi(store, "block1", _DAY, weights={"anth": 0.7, "pm": 0.7, "hop": 0.1})
    assert any("not 1.0" in r.message for r in caplog.records)


def test_custom_weights_change_output(store):
    _seed_high_anthracnose_window(store, "block1")
    default_result = compute_ppi(store, "block1", _DAY)
    anth_heavy = compute_ppi(store, "block1", _DAY, weights={"anth": 1.0, "pm": 0.0, "hop": 0.0})
    assert anth_heavy["ppi"] == pytest.approx(default_result["anth"] * 100.0, abs=0.5)


def test_ndre_anomaly_boosts_anthracnose_component(store):
    """A current NDRE several SD below a 30-day mean triggers the boost."""
    _seed_high_anthracnose_window(store, "block1")
    base = datetime.combine(_DAY - timedelta(days=30), datetime.min.time(), tzinfo=timezone.utc)
    for i in range(8):
        store.insert(
            BlockObservation(
                block_id="block1",
                ts=base + timedelta(days=i * 3),
                source=ConnectorSource.SENTINEL2,
                ndvi=0.85,
                ndre=0.70 + 0.02 * ((i % 2) * 2 - 1),
                ndmi=0.55,
            )
        )
    stressed_ts = datetime.combine(
        _DAY - timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc
    )
    store.insert(
        BlockObservation(
            block_id="block1",
            ts=stressed_ts,
            source=ConnectorSource.SENTINEL2,
            ndvi=0.50,
            ndre=0.30,
            ndmi=0.20,
        )
    )

    boosted = compute_ppi(store, "block1", _DAY)
    assert boosted["ndre_anomaly"] is True

    fresh_store = type(store)(":memory:")
    _seed_high_anthracnose_window(fresh_store, "block1")
    unboosted = compute_ppi(fresh_store, "block1", _DAY)
    assert boosted["anth"] >= unboosted["anth"]
    assert boosted["anth"] - unboosted["anth"] <= NDRE_ANOMALY_BOOST + 1e-6


def test_default_weights_pinned_at_5_3_2():
    """Guard against accidental weight drift."""
    assert DEFAULT_WEIGHTS == {"anth": 0.5, "pm": 0.3, "hop": 0.2}


def test_primary_pathogen_returns_max_component():
    assert (
        primary_pathogen({"anth": 0.9, "pm": 0.2, "hop": 0.1, "ppi": 60, "ndre_anomaly": False})
        == "anthracnose"
    )
    assert (
        primary_pathogen({"anth": 0.2, "pm": 0.8, "hop": 0.1, "ppi": 35, "ndre_anomaly": False})
        == "powdery_mildew"
    )
    assert (
        primary_pathogen({"anth": 0.1, "pm": 0.1, "hop": 0.9, "ppi": 22, "ndre_anomaly": False})
        == "hopper"
    )


def test_primary_pathogen_tie_resolves_to_anthracnose():
    """Konkan-disease-prevalence prior: ties favor anth > pm > hop."""
    assert (
        primary_pathogen({"anth": 0.5, "pm": 0.5, "hop": 0.5, "ppi": 50, "ndre_anomaly": False})
        == "anthracnose"
    )


def test_cropsap_taluka_pressure_feeds_hopper_component(store):
    """A CROPSAP row in the same taluka raises the hopper component."""
    _seed_high_anthracnose_window(store, "ratnagiri_north")
    cropsap_ts = datetime.combine(
        _DAY - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
    )
    store.insert(
        BlockObservation(
            block_id="ratnagiri_hopper",
            ts=cropsap_ts,
            source=ConnectorSource.CROPSAP,
            cropsap_pest_pressure=85.0,
        )
    )
    result = compute_ppi(store, "ratnagiri_north", _DAY)
    assert result["hop"] > 0.0
