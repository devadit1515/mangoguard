"""Tests for the orchard-health queries module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mangoguard.orchard_health.queries import (
    block_anomalies,
    block_latest_indices,
    block_vegetation_timeseries,
    index_in_valid_range,
)
from mangoguard.schema import BlockObservation, ConnectorSource

_END = datetime(2025, 7, 15, tzinfo=timezone.utc)


def _ndvi_row(block_id: str, when: datetime, ndvi: float, **kw) -> BlockObservation:
    return BlockObservation(
        block_id=block_id,
        ts=when,
        source=ConnectorSource.SENTINEL2,
        ndvi=ndvi,
        **kw,
    )


def test_timeseries_returns_empty_for_empty_block(store):
    df = block_vegetation_timeseries(store, "no_data_block", end_time=_END)
    assert df.empty
    assert list(df.columns) == ["ts", "ndvi", "ndre", "ndmi"]


def test_timeseries_sorted_oldest_first(store):
    for i in range(5):
        # offset by 1 day so all rows sit inside the half-open [start, end) window
        store.insert(_ndvi_row("blk1", _END - timedelta(days=i * 7 + 1), ndvi=0.5 + i * 0.05))
    df = block_vegetation_timeseries(store, "blk1", end_time=_END)
    assert len(df) == 5
    assert df["ts"].is_monotonic_increasing


def test_timeseries_excludes_blockless_indices(store):
    """A row with only weather (no NDVI/NDRE/NDMI) should be excluded."""
    store.insert(
        BlockObservation(
            block_id="blk1",
            ts=_END - timedelta(days=1),
            source=ConnectorSource.IMD,
            t_air_c=28.0,
        )
    )
    df = block_vegetation_timeseries(store, "blk1", end_time=_END)
    assert df.empty


def test_timeseries_partial_index_preserved(store):
    """A row with only NDRE (no NDVI/NDMI) should still appear with NaNs in the missing cols."""
    store.insert(
        BlockObservation(
            block_id="blk1",
            ts=_END - timedelta(days=1),
            source=ConnectorSource.SENTINEL2,
            ndre=0.45,
        )
    )
    df = block_vegetation_timeseries(store, "blk1", end_time=_END)
    assert len(df) == 1
    assert df["ndre"].iloc[0] == 0.45


def test_anomalies_empty_for_block_with_no_data(store):
    anomalies = block_anomalies(store, "no_data_block", end_time=_END)
    assert anomalies == []


def test_anomalies_flags_known_drop(store):
    """A clear drop after a stable baseline must produce a flagged anomaly."""
    base_ts = _END - timedelta(days=40)
    # 30 days of stable NDVI ~0.65
    for i in range(30):
        store.insert(_ndvi_row("blk1", base_ts + timedelta(days=i), ndvi=0.65 + (i % 2) * 0.005))
    # Then a sharp drop to 0.30 on the most recent day
    store.insert(_ndvi_row("blk1", _END - timedelta(days=1), ndvi=0.30))
    anomalies = block_anomalies(store, "blk1", end_time=_END, sd_threshold=1.0)
    assert len(anomalies) >= 1
    flagged = anomalies[-1]
    assert flagged["index"] == "ndvi"
    assert flagged["value"] < 0.5
    assert flagged["deviation_sd"] >= 1.0


def test_anomalies_no_drop_returns_empty(store):
    """Stable NDVI should NOT produce any anomalies."""
    base_ts = _END - timedelta(days=30)
    for i in range(30):
        store.insert(_ndvi_row("blk1", base_ts + timedelta(days=i), ndvi=0.65))
    anomalies = block_anomalies(store, "blk1", end_time=_END, sd_threshold=1.0)
    assert anomalies == []


def test_anomalies_rejects_invalid_index_name(store):
    with pytest.raises(ValueError, match="index must be"):
        block_anomalies(store, "blk1", index="bogus", end_time=_END)


def test_latest_indices_returns_latest_per_index(store):
    store.insert(_ndvi_row("blk1", _END - timedelta(days=5), ndvi=0.55))
    store.insert(_ndvi_row("blk1", _END - timedelta(days=2), ndvi=0.60))
    store.insert(
        BlockObservation(
            block_id="blk1",
            ts=_END - timedelta(days=3),
            source=ConnectorSource.SENTINEL2,
            ndre=0.45,
        )
    )
    latest = block_latest_indices(store, "blk1", end_time=_END)
    assert latest["ndvi"] == pytest.approx(0.60)
    assert latest["ndre"] == pytest.approx(0.45)
    assert latest["ndmi"] is None


def test_latest_indices_empty_block_returns_all_none(store):
    latest = block_latest_indices(store, "no_data_block", end_time=_END)
    assert latest == {"ndvi": None, "ndre": None, "ndmi": None}


def test_index_valid_range():
    assert index_in_valid_range(0.5)
    assert index_in_valid_range(-1.0)
    assert index_in_valid_range(1.0)
    assert index_in_valid_range(None)
    assert not index_in_valid_range(1.5)
    assert not index_in_valid_range(-2.0)
