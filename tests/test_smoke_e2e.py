"""End-to-end smoke test for the foundation: connector -> store -> query."""

from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.schema import BlockObservation, ConnectorSource
from mangoguard.store import FeedStore


class _SyntheticIMDConnector(Connector):
    source = ConnectorSource.IMD
    name = "synthetic_imd"

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        cur = since
        while cur < until:
            yield BlockObservation(
                block_id="B1",
                ts=cur,
                source=ConnectorSource.IMD,
                t_air_c=24.0 + (cur.hour * 0.4),
                rh_pct=70.0 + (cur.hour * 0.5),
                precip_mm=0.0,
            )
            cur += timedelta(hours=1)


def test_foundation_round_trip():
    store = FeedStore(":memory:")
    ctx = ConnectorContext(store=store)
    conn = _SyntheticIMDConnector(ctx)

    start = datetime(2026, 7, 12, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    n = conn.run(since=start, until=end)

    assert n == 24

    rows = store.query(block_id="B1", ts_start=start, ts_end=end)
    assert len(rows) == 24
    assert rows[0].source == ConnectorSource.IMD
    assert rows[0].t_air_c == 24.0
    assert rows[-1].t_air_c == 24.0 + 23 * 0.4
