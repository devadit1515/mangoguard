"""Tests for the seasonal NDVI integral + cross-season trend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mangoguard.orchard_health.trend import (
    cross_season_trend,
    latest_dashboard_snapshot,
    season_ndvi_integral,
)
from mangoguard.schema import BlockObservation, ConnectorSource


def _ndvi_row(
    block_id: str, when: datetime, *, ndvi=None, ndre=None, ndmi=None
) -> BlockObservation:
    return BlockObservation(
        block_id=block_id,
        ts=when,
        source=ConnectorSource.SENTINEL2,
        ndvi=ndvi,
        ndre=ndre,
        ndmi=ndmi,
    )


def test_season_ndvi_integral_returns_zero_for_empty_block(store):
    assert season_ndvi_integral(store, "no_data_block", year=2024) == 0.0


def test_season_ndvi_integral_returns_finite_positive(store):
    """Three days of NDVI ~0.6 in May 2024 -> integral ~1.8."""
    for day in (10, 15, 20):
        store.insert(_ndvi_row("blk1", datetime(2024, 5, day, tzinfo=timezone.utc), ndvi=0.60))
    integral = season_ndvi_integral(store, "blk1", year=2024)
    assert 1.5 < integral < 2.0


def test_season_ndvi_integral_only_apr_to_jun(store):
    """Observations outside the Apr-Jun window must not contribute."""
    # In window: 0.60 on May 15
    store.insert(_ndvi_row("blk1", datetime(2024, 5, 15, tzinfo=timezone.utc), ndvi=0.60))
    # Outside window: 0.80 in February
    store.insert(_ndvi_row("blk1", datetime(2024, 2, 10, tzinfo=timezone.utc), ndvi=0.80))
    integral = season_ndvi_integral(store, "blk1", year=2024)
    assert integral == 0.60


def test_season_ndvi_integral_averages_same_day(store):
    """Two readings on the same day should be averaged, not summed."""
    store.insert(_ndvi_row("blk1", datetime(2024, 5, 15, 10, tzinfo=timezone.utc), ndvi=0.50))
    store.insert(_ndvi_row("blk1", datetime(2024, 5, 15, 14, tzinfo=timezone.utc), ndvi=0.70))
    integral = season_ndvi_integral(store, "blk1", year=2024)
    assert integral == 0.60


def test_cross_season_trend_returns_empty_for_no_years(store):
    df = cross_season_trend(store, "blk1", years=[])
    assert df.empty
    assert list(df.columns) == ["year", "ndvi_integral", "mean_ndre", "peak_ndmi_drop_days"]


def test_cross_season_trend_one_row_per_year(store):
    for year in (2022, 2023, 2024):
        store.insert(_ndvi_row("blk1", datetime(year, 5, 15, tzinfo=timezone.utc), ndvi=0.60))
    df = cross_season_trend(store, "blk1", years=[2022, 2023, 2024])
    assert len(df) == 3
    assert list(df["year"]) == [2022, 2023, 2024]


def test_cross_season_trend_mean_ndre_when_present(store):
    store.insert(_ndvi_row("blk1", datetime(2024, 5, 5, tzinfo=timezone.utc), ndre=0.40))
    store.insert(_ndvi_row("blk1", datetime(2024, 5, 15, tzinfo=timezone.utc), ndre=0.60))
    df = cross_season_trend(store, "blk1", years=[2024])
    assert df["mean_ndre"].iloc[0] == 0.50


def test_cross_season_trend_drop_days_zero_for_stable_ndmi(store):
    for day in (1, 8, 15, 22, 29):
        store.insert(_ndvi_row("blk1", datetime(2024, 5, day, tzinfo=timezone.utc), ndmi=0.50))
    df = cross_season_trend(store, "blk1", years=[2024])
    assert df["peak_ndmi_drop_days"].iloc[0] == 0


def test_latest_dashboard_snapshot_returns_block_summary(store):
    store.insert(_ndvi_row("blk1", datetime(2024, 5, 15, tzinfo=timezone.utc), ndvi=0.60))
    snapshot = latest_dashboard_snapshot(
        store, "blk1", end_time=datetime(2024, 5, 20, tzinfo=timezone.utc) + timedelta(days=1)
    )
    assert snapshot["block_id"] == "blk1"
    assert snapshot["n_observations"] >= 1
