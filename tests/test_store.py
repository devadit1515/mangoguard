"""Tests for the SQLite-backed FeedStore repository."""

from datetime import datetime, timedelta, timezone

import pytest

from mangoguard.schema import BlockObservation, ConnectorSource
from mangoguard.store import _COLUMNS, FeedStore


def test_store_initializes_empty(store):
    assert store.count() == 0


def test_insert_one_observation_and_count(store, sample_observation):
    store.insert(sample_observation)
    assert store.count() == 1


def test_insert_many_observations(store, sample_observations):
    store.insert_many(sample_observations)
    assert store.count() == len(sample_observations)


def test_query_by_block_and_window(store, sample_observations):
    store.insert_many(sample_observations)
    window_start = datetime(2026, 7, 12, tzinfo=timezone.utc)
    window_end = window_start + timedelta(hours=12)

    rows = store.query(block_id="B1", ts_start=window_start, ts_end=window_end)

    assert len(rows) == 2
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.block_id == "B1" for r in rows)


def test_query_by_source_filter(store, sample_observation):
    store.insert(sample_observation)
    rows = store.query_by_source(ConnectorSource.PESSL)
    assert len(rows) == 1
    assert rows[0].block_id == "B3"

    rows_other = store.query_by_source(ConnectorSource.FYLLO)
    assert rows_other == []


def test_insert_is_idempotent_on_natural_key(store, sample_observation):
    store.insert(sample_observation)
    updated = sample_observation.model_copy(update={"notes": "second pass"})
    store.insert(updated)
    assert store.count() == 1
    rows = store.query(
        block_id="B3",
        ts_start=sample_observation.ts,
        ts_end=sample_observation.ts + timedelta(seconds=1),
    )
    assert rows[0].notes == "second pass"


def test_round_trip_preserves_optional_fields(store, sample_observation):
    store.insert(sample_observation)
    rows = store.query(
        block_id="B3",
        ts_start=sample_observation.ts,
        ts_end=sample_observation.ts + timedelta(seconds=1),
    )
    rt = rows[0]
    assert rt.ts == sample_observation.ts
    assert rt.ts.tzinfo is not None
    assert rt.t_air_c == pytest.approx(sample_observation.t_air_c)
    assert rt.rh_pct == pytest.approx(sample_observation.rh_pct)
    assert rt.leaf_wetness_hr == pytest.approx(sample_observation.leaf_wetness_hr)
    assert rt.precip_mm == pytest.approx(sample_observation.precip_mm)
    assert rt.source == sample_observation.source


def test_query_normalizes_non_utc_bounds(store, sample_observation):
    """Callers may pass non-UTC tz-aware bounds; query must normalize correctly."""
    ist = timezone(timedelta(hours=5, minutes=30))
    store.insert(sample_observation)
    # sample_observation.ts is 2026-07-12 10:30 UTC == 16:00 IST.
    ts_start_ist = sample_observation.ts.astimezone(ist) - timedelta(minutes=1)
    ts_end_ist = sample_observation.ts.astimezone(ist) + timedelta(minutes=1)

    rows = store.query(block_id="B3", ts_start=ts_start_ist, ts_end=ts_end_ist)

    assert len(rows) == 1
    assert rows[0].ts == sample_observation.ts


def test_columns_constant_matches_obs_to_row_arity():
    """`_COLUMNS` and `_obs_to_row` must stay in sync — same length always."""
    obs = BlockObservation(
        block_id="B1",
        ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
        source=ConnectorSource.IMD,
    )
    row = FeedStore._obs_to_row(obs)
    assert len(row) == len(
        _COLUMNS
    ), f"_obs_to_row arity ({len(row)}) drifted from _COLUMNS length ({len(_COLUMNS)})"


def test_columns_constant_matches_block_observation_fields():
    """Guards against silent drift between BlockObservation fields and store columns.

    If a new field is added to BlockObservation without being added to
    _COLUMNS (and the corresponding read/write helpers), round-trips silently
    drop data. This test fails loudly in that case.
    """
    from mangoguard.schema import BlockObservation  # noqa: PLC0415
    from mangoguard.store import _COLUMNS  # noqa: PLC0415

    assert set(_COLUMNS) == set(BlockObservation.model_fields)


def test_count_by_source(store, sample_observations):
    store.insert_many(sample_observations)
    extra = sample_observations[0].model_copy(
        update={"source": ConnectorSource.PESSL, "block_id": "B9"}
    )
    store.insert(extra)
    counts = store.count_by_source()
    assert counts[ConnectorSource.IMD] == len(sample_observations)
    assert counts[ConnectorSource.PESSL] == 1
