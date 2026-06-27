"""Tests for the yield/price feature engineering."""

from __future__ import annotations

from datetime import datetime, timezone

from mangoguard.schema import BlockObservation, ConnectorSource
from mangoguard.yield_price.features import FEATURE_NAMES, build_features


def _row(block_id, when, **kw):
    return BlockObservation(block_id=block_id, ts=when, source=ConnectorSource.IMD, **kw)


def test_returns_dict_with_all_required_keys(store):
    features = build_features(store, "blk1", season_year=2024)
    for name in FEATURE_NAMES:
        assert name in features


def test_handles_empty_store(store):
    """No observations and no metadata -> all-None / zero output, no crash."""
    features = build_features(store, "blk1", season_year=2024)
    assert features["acreage"] is None
    assert features["ndvi_integral_apr_jun"] == 0.0
    assert features["cum_gdd_above_10c"] == 0.0


def test_uses_block_meta_when_provided(store):
    meta = {
        "acreage": 10.0,
        "tree_count": 250,
        "mean_tree_age": 12,
        "soil_texture_class": "loamy",
        "soil_ph": 6.5,
        "prev_season_yield_kg_per_acre": 8500.0,
    }
    features = build_features(store, "blk1", season_year=2024, block_meta=meta)
    assert features["acreage"] == 10.0
    assert features["tree_count"] == 250
    assert features["soil_ph"] == 6.5
    assert features["prev_season_yield_kg_per_acre"] == 8500.0


def test_ndvi_integral_uses_apr_jun_window(store):
    """An NDVI observation in February should NOT contribute to the integral."""
    store.insert(
        BlockObservation(
            block_id="blk1",
            ts=datetime(2024, 2, 15, tzinfo=timezone.utc),
            source=ConnectorSource.SENTINEL2,
            ndvi=0.80,
        )
    )
    features = build_features(store, "blk1", season_year=2024)
    assert features["ndvi_integral_apr_jun"] == 0.0


def test_cumulative_gdd_above_threshold(store):
    """Sum of (T - 10) for warm readings only."""
    for day in (10, 15, 20):
        store.insert(_row("blk1", datetime(2024, 5, day, tzinfo=timezone.utc), t_air_c=25.0))
    features = build_features(store, "blk1", season_year=2024)
    assert features["cum_gdd_above_10c"] == 3 * 15.0


def test_cumulative_gdd_skips_cold_readings(store):
    """T<=10C contributes 0 to GDD."""
    store.insert(_row("blk1", datetime(2024, 5, 10, tzinfo=timezone.utc), t_air_c=8.0))
    features = build_features(store, "blk1", season_year=2024)
    assert features["cum_gdd_above_10c"] == 0.0


def test_total_rainfall_sums_precip(store):
    for day in (5, 10, 15):
        store.insert(_row("blk1", datetime(2024, 5, day, tzinfo=timezone.utc), precip_mm=12.0))
    features = build_features(store, "blk1", season_year=2024)
    assert features["total_rainfall_mm"] == 36.0


def test_mean_rh_pct_averages_when_present(store):
    store.insert(_row("blk1", datetime(2024, 5, 5, tzinfo=timezone.utc), rh_pct=60.0))
    store.insert(_row("blk1", datetime(2024, 5, 10, tzinfo=timezone.utc), rh_pct=80.0))
    features = build_features(store, "blk1", season_year=2024)
    assert features["mean_rh_pct"] == 70.0


def test_season_year_round_trips(store):
    features = build_features(store, "blk1", season_year=2024)
    assert features["season_year"] == 2024


def test_handles_missing_prev_season_yield(store):
    features = build_features(store, "blk1", season_year=2024, block_meta={"acreage": 10})
    assert features["prev_season_yield_kg_per_acre"] is None
