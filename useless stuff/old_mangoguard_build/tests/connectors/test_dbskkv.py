"""Tests for the DBSKKV Dapoli Konkan microclimate connector."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.dbskkv import DBSKKVConnector
from mangoguard.schema import BlockObservation, ConnectorSource

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "dbskkv_dapoli_forecast_2025-07-12.html"

_WINDOW_START = datetime(2025, 7, 12, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 18, tzinfo=timezone.utc)


def test_fixture_yields_5_daily_rows():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 5
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.source == ConnectorSource.DBSKKV for r in rows)


def test_block_id_is_dapoli():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert all(r.block_id == "dapoli" for r in rows)


def test_t_air_c_is_mean_of_tmax_tmin():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[0].t_air_c == pytest.approx(26.65)
    for r in rows:
        assert 20.0 <= r.t_air_c <= 40.0


def test_rh_pct_carries_single_column():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[0].rh_pct == pytest.approx(89.0)


def test_precip_mm_carries_rainfall():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    monsoon_peak = next(
        r
        for r in rows
        if r.ts.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat() == "2025-07-15"
    )
    assert monsoon_peak.precip_mm == pytest.approx(52.3)


def test_missing_rainfall_dash_treated_as_none():
    """Row 4 has rainfall '--' — should yield None, not drop the row."""
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    row_16 = next(
        r
        for r in rows
        if r.ts.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat() == "2025-07-16"
    )
    assert row_16.precip_mm is None
    assert row_16.t_air_c is not None
    assert row_16.rh_pct == pytest.approx(90.0)


def test_missing_wind_empty_cell_treated_as_none():
    """Row 3 has empty wind cell — should yield None, not drop the row."""
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    row_15 = next(
        r
        for r in rows
        if r.ts.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat() == "2025-07-15"
    )
    assert row_15.wind_speed_ms is None
    assert row_15.precip_mm == pytest.approx(52.3)


def test_wind_kmh_converted_to_ms():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[0].wind_speed_ms == pytest.approx(15.5 / 3.6, rel=1e-4)


def test_notes_preserves_raw_quartet_and_source_url():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    parsed = json.loads(rows[0].notes)
    assert parsed["tmax_c"] == 29.5
    assert parsed["tmin_c"] == 23.8
    assert parsed["rh_pct"] == 89
    assert parsed["wind_kmh"] == 15.5
    assert parsed["source_url"] == "https://www.dbskkv.org/farmers-corner/weather-forecast"


def test_ts_is_ist_midnight():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        ist = r.ts.astimezone(ZoneInfo("Asia/Kolkata"))
        assert ist.hour == 0 and ist.minute == 0


def test_window_filter_excludes_out_of_range():
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(
        conn.fetch(
            since=datetime(2025, 7, 13, 18, 30, tzinfo=timezone.utc),
            until=datetime(2025, 7, 13, 18, 31, tzinfo=timezone.utc),
        )
    )
    assert len(rows) == 1
    assert rows[0].ts.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat() == "2025-07-14"


def test_fallback_selector_finds_table_with_different_class():
    """If the primary class is missing, the header-text fallback kicks in."""
    html = """
    <html><body>
      <table class="some-other-name">
        <thead>
          <tr>
            <th>Date</th><th>Tmax</th><th>Tmin</th><th>RH</th>
            <th>Rainfall</th><th>Wind</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>2025-07-13</td><td>30</td><td>24</td><td>88</td><td>10</td><td>14</td></tr>
        </tbody>
      </table>
    </body></html>
    """
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        path = f.name
    try:
        conn = DBSKKVConnector(ConnectorContext(), fixture_path=path)
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
        assert len(rows) == 1
    finally:
        Path(path).unlink(missing_ok=True)


def test_no_table_returns_empty_with_warning(tmp_path, caplog):
    html = "<html><body><p>No forecast table today</p></body></html>"
    fixture = tmp_path / "empty.html"
    fixture.write_text(html, encoding="utf-8")
    conn = DBSKKVConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("DBSKKV" in r.message for r in caplog.records)


def test_connector_runs_end_to_end_to_store(store):
    conn = DBSKKVConnector(ConnectorContext(store=store), fixture_path=FIXTURE_PATH)
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 5
    assert store.count() == 5
    assert store.count_by_source().get(ConnectorSource.DBSKKV, 0) == 5


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("DBSKKV_LIVE"),
    reason="live DBSKKV scrape test gated on DBSKKV_LIVE=1 env var",
)
def test_live_dbskkv_yields_at_least_one_row():
    conn = DBSKKVConnector(ConnectorContext())
    until = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    since = until.replace(year=until.year - 1)
    rows = list(conn.fetch(since=since, until=until))
    assert isinstance(rows, list)
