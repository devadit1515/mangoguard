"""Tests for the Connector ABC + ConnectorContext."""

from datetime import datetime, timedelta, timezone
from typing import Iterable

import pytest

from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.schema import BlockObservation, ConnectorSource


class _DummyConnector(Connector):
    source = ConnectorSource.IMD
    name = "dummy"

    def __init__(self, ctx: ConnectorContext, payload: list[BlockObservation]) -> None:
        super().__init__(ctx)
        self._payload = payload

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        return [o for o in self._payload if since <= o.ts < until]


def test_connector_requires_source_class_attr():
    class BadConnector(Connector):
        name = "bad"

        def fetch(self, since, until):
            return []

    ctx = ConnectorContext()
    with pytest.raises(TypeError):
        BadConnector(ctx)


def test_connector_run_writes_to_store(store):
    ctx = ConnectorContext(store=store)
    obs = BlockObservation(
        block_id="B1",
        ts=datetime(2026, 7, 12, 10, tzinfo=timezone.utc),
        source=ConnectorSource.IMD,
        t_air_c=27.5,
    )
    conn = _DummyConnector(ctx, payload=[obs])

    window_start = datetime(2026, 7, 12, tzinfo=timezone.utc)
    window_end = window_start + timedelta(days=1)
    n = conn.run(since=window_start, until=window_end)

    assert n == 1
    assert store.count() == 1


def test_connector_run_filters_by_window(store):
    ctx = ConnectorContext(store=store)
    payload = [
        BlockObservation(
            block_id="B1",
            ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
            source=ConnectorSource.IMD,
        ),
        BlockObservation(
            block_id="B1",
            ts=datetime(2026, 7, 15, tzinfo=timezone.utc),
            source=ConnectorSource.IMD,
        ),
    ]
    conn = _DummyConnector(ctx, payload=payload)
    n = conn.run(
        since=datetime(2026, 7, 11, tzinfo=timezone.utc),
        until=datetime(2026, 7, 13, tzinfo=timezone.utc),
    )
    assert n == 1


def test_connector_source_must_match_observation_source(store):
    ctx = ConnectorContext(store=store)
    obs = BlockObservation(
        block_id="B1",
        ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
        source=ConnectorSource.PESSL,
    )
    conn = _DummyConnector(ctx, payload=[obs])

    with pytest.raises(ValueError, match="source mismatch"):
        conn.run(
            since=datetime(2026, 7, 12, tzinfo=timezone.utc),
            until=datetime(2026, 7, 13, tzinfo=timezone.utc),
        )
