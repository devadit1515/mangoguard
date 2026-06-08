"""Tests for the SQLite-backed FeedStore repository."""

from datetime import datetime, timedelta, timezone

import pytest

from mangoguard.schema import BlockObservation, ConnectorSource


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
    assert rt.t_air_c == pytest.approx(sample_observation.t_air_c)
    assert rt.rh_pct == pytest.approx(sample_observation.rh_pct)
    assert rt.leaf_wetness_hr == pytest.approx(sample_observation.leaf_wetness_hr)
    assert rt.precip_mm == pytest.approx(sample_observation.precip_mm)
    assert rt.source == sample_observation.source
