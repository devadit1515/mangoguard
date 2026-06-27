"""Tests for the AGMARKNET mandi-price connector."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mangoguard.connectors.agmarknet import AGMARKNETConnector
from mangoguard.connectors.base import ConnectorContext
from mangoguard.schema import BlockObservation, ConnectorSource

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agmarknet_maharashtra_mango_2025-07-12.json"

# Window that covers all 3 dates in the fixture (11, 12, 13 July 2025 IST).
_WINDOW_START = datetime(2025, 7, 10, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 15, tzinfo=timezone.utc)


def _connector(ctx: ConnectorContext | None = None) -> AGMARKNETConnector:
    return AGMARKNETConnector(ctx or ConnectorContext())


def test_fixture_loads_and_yields_observations():
    conn = _connector()
    rows = conn.parse_fixture(str(FIXTURE_PATH), since=_WINDOW_START, until=_WINDOW_END)
    # 8 records, 1 dropped (empty market), 2 collide at Vashi 2025-07-12 (Alphonso + Kesar)
    # -> 7 valid, but the Vashi-12-Jul pair gets variety-suffixed, so still 7 observations.
    assert len(rows) == 7
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.source == ConnectorSource.AGMARKNET for r in rows)


def test_block_id_is_lowercased_market():
    conn = _connector()
    rows = conn.parse_fixture(str(FIXTURE_PATH), since=_WINDOW_START, until=_WINDOW_END)
    block_ids = {r.block_id for r in rows}
    # Collision suffix on Vashi 2025-07-12 -> two rows: vashi_alphonso, vashi_kesar
    # Vashi 2025-07-13 stays as plain "vashi" (no collision that day)
    assert "ratnagiri" in block_ids
    assert "devgad" in block_ids
    assert "vengurla" in block_ids
    assert "vashi" in block_ids
    assert "vashi_alphonso" in block_ids
    assert "vashi_kesar" in block_ids


def test_ts_is_timezone_aware_and_in_ist_midnight():
    conn = _connector()
    rows = conn.parse_fixture(str(FIXTURE_PATH), since=_WINDOW_START, until=_WINDOW_END)
    for r in rows:
        assert r.ts.tzinfo is not None
        # 00:00 IST == 18:30 UTC prior day. Allow either rep since pydantic stores as-passed.
        ist = r.ts.astimezone(ZoneInfo("Asia/Kolkata"))
        assert ist.hour == 0 and ist.minute == 0


def test_modal_price_is_float_and_positive():
    conn = _connector()
    rows = conn.parse_fixture(str(FIXTURE_PATH), since=_WINDOW_START, until=_WINDOW_END)
    for r in rows:
        assert isinstance(r.mandi_modal_price_inr_per_quintal, float)
        assert r.mandi_modal_price_inr_per_quintal > 0


def test_notes_carries_variety_and_grade():
    conn = _connector()
    rows = conn.parse_fixture(str(FIXTURE_PATH), since=_WINDOW_START, until=_WINDOW_END)
    devgad_row = next(r for r in rows if r.block_id == "devgad")
    parsed = json.loads(devgad_row.notes)
    assert parsed["variety"] == "Alphonso"
    assert parsed["grade"] == "Premium"


def test_window_filter_excludes_out_of_range_dates():
    conn = _connector()
    # Tight window covering only 2025-07-12 IST
    # (which is 18:30 UTC 2025-07-11 to 18:30 UTC 2025-07-12).
    rows = conn.parse_fixture(
        str(FIXTURE_PATH),
        since=datetime(2025, 7, 11, 18, 30, tzinfo=timezone.utc),
        until=datetime(2025, 7, 11, 18, 31, tzinfo=timezone.utc),
    )
    # Should catch only the 12-July IST midnight rows -> 4 markets,
    # with Vashi-Alphonso+Kesar collision-suffixed.
    # Rows on 12/07/2025 IST: Vashi (2 -> suffixed), Ratnagiri (1), Devgad (1) = 4
    assert len(rows) == 4


def test_fetch_returns_empty_when_no_api_key():
    conn = _connector(ConnectorContext(secrets={}))
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []


def test_dropped_records_do_not_raise(caplog):
    """Empty market + bad date + bad price should be skipped, not raise."""
    bad_payload = {
        "records": [
            {"market": "", "arrival_date": "12/07/2025", "modal_price": "100"},
            {"market": "Vashi", "arrival_date": "not-a-date", "modal_price": "100"},
            {"market": "Vashi", "arrival_date": "12/07/2025", "modal_price": "n/a"},
        ]
    }
    tmp = Path(__file__).parent / "fixtures" / "_agmarknet_bad_records.json"
    tmp.write_text(json.dumps(bad_payload), encoding="utf-8")
    try:
        conn = _connector()
        with caplog.at_level("WARNING"):
            rows = conn.parse_fixture(str(tmp), since=_WINDOW_START, until=_WINDOW_END)
        assert rows == []
        # At least 3 warnings emitted (one per dropped record)
        agmarknet_warnings = [r for r in caplog.records if "AGMARKNET" in r.message]
        assert len(agmarknet_warnings) >= 3
    finally:
        tmp.unlink(missing_ok=True)


def test_connector_runs_end_to_end_to_store(store):
    """Round-trip: parse fixture -> run() with synthetic fetch -> store has rows."""
    conn = AGMARKNETConnector(ConnectorContext(store=store))
    # Monkey-patch fetch to use the fixture instead of HTTP.
    conn.fetch = lambda since, until: conn.parse_fixture(  # type: ignore[method-assign]
        str(FIXTURE_PATH), since=since, until=until
    )
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 7
    assert store.count() == 7
    assert store.count_by_source().get(ConnectorSource.AGMARKNET, 0) == 7


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("DATA_GOV_IN_KEY"),
    reason="live AGMARKNET integration test requires DATA_GOV_IN_KEY env var",
)
def test_live_agmarknet_yields_at_least_one_record():
    ctx = ConnectorContext(secrets={"DATA_GOV_IN_KEY": os.environ["DATA_GOV_IN_KEY"]})
    conn = AGMARKNETConnector(ctx)
    # 90-day backward window — mango market is sparse outside Mar-Jul, but Vashi runs year-round.
    until = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    since = until - timedelta(days=90)
    rows = list(conn.fetch(since=since, until=until))
    assert len(rows) >= 1, "live AGMARKNET returned no Mango records for last 90 days"
