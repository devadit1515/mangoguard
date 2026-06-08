"""Tests for the IMD Mausam + Meghdoot agromet connector."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.imd import IMDConnector
from mangoguard.schema import BlockObservation, ConnectorSource

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "imd_ratnagiri_amfu_2025-07-12.html"

# Window covering all 5 forecast dates (13-17 July 2025 IST).
_WINDOW_START = datetime(2025, 7, 12, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 18, tzinfo=timezone.utc)


def test_fixture_yields_5_daily_rows():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 5
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.source == ConnectorSource.IMD for r in rows)


def test_block_id_is_district_lowercase():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert all(r.block_id == "ratnagiri" for r in rows)


def test_t_air_c_is_mean_of_tmax_tmin_and_in_plausible_range():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    first = rows[0]
    # Fixture row 1: Tmax=30.5, Tmin=24.0 -> mean 27.25
    assert first.t_air_c == pytest.approx(27.25)
    for r in rows:
        assert 20.0 <= r.t_air_c <= 40.0


def test_rh_pct_is_mean_of_morn_eve_and_in_range():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    # Fixture row 1: RH morn=92, eve=78 -> mean 85
    assert rows[0].rh_pct == pytest.approx(85.0)
    for r in rows:
        assert 0.0 <= r.rh_pct <= 100.0


def test_precip_mm_carries_rainfall():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    # Row 3 (2025-07-15) is monsoon-peak: 45.6 mm
    monsoon_peak = next(
        r
        for r in rows
        if r.ts.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat() == "2025-07-15"
    )
    assert monsoon_peak.precip_mm == pytest.approx(45.6)


def test_wind_kmh_converted_to_ms():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    # Row 1 wind 14.0 km/h -> 3.8889 m/s
    assert rows[0].wind_speed_ms == pytest.approx(14.0 / 3.6, rel=1e-4)


def test_notes_preserves_raw_quartet():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    parsed = json.loads(rows[0].notes)
    assert parsed["tmax_c"] == 30.5
    assert parsed["tmin_c"] == 24.0
    assert parsed["rh_morn_pct"] == 92
    assert parsed["rh_eve_pct"] == 78
    assert parsed["wind_kmh"] == 14.0


def test_ts_is_ist_midnight():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        ist = r.ts.astimezone(ZoneInfo("Asia/Kolkata"))
        assert ist.hour == 0 and ist.minute == 0


def test_window_filter_excludes_out_of_range_dates():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=FIXTURE_PATH)
    # Only 2025-07-14 IST midnight should match.
    rows = list(
        conn.fetch(
            since=datetime(2025, 7, 13, 18, 30, tzinfo=timezone.utc),
            until=datetime(2025, 7, 13, 18, 31, tzinfo=timezone.utc),
        )
    )
    assert len(rows) == 1
    assert rows[0].ts.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat() == "2025-07-14"


def test_fetch_returns_empty_without_fixture_or_api_key():
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri")
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []


def test_malformed_row_is_skipped_with_warning(tmp_path, caplog):
    bad_html = """
    <html><body><table id="five-day-forecast">
      <tr><th>Date</th><th>Tmax</th><th>Tmin</th><th>RH morning</th>
          <th>RH evening</th><th>Rainfall</th><th>Wind speed</th></tr>
      <tr><td>not-a-date</td><td>30</td><td>24</td><td>92</td><td>78</td><td>10</td><td>14</td></tr>
      <tr><td>2025-07-13</td><td>30.5</td><td>24.0</td><td>92</td><td>78</td><td>18.4</td><td>14.0</td></tr>
    </table></body></html>
    """
    fixture = tmp_path / "bad.html"
    fixture.write_text(bad_html, encoding="utf-8")
    conn = IMDConnector(ConnectorContext(), district="Ratnagiri", fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1  # bad row dropped, good row kept
    assert rows[0].ts.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat() == "2025-07-13"
    imd_warnings = [r for r in caplog.records if "IMD" in r.message]
    assert len(imd_warnings) >= 1


def test_connector_runs_end_to_end_to_store(store):
    conn = IMDConnector(
        ConnectorContext(store=store),
        district="Ratnagiri",
        fixture_path=FIXTURE_PATH,
    )
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 5
    assert store.count() == 5
    assert store.count_by_source().get(ConnectorSource.IMD, 0) == 5


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("IMD_API_KEY"),
    reason="live IMD integration test requires IMD_API_KEY env var (IP-whitelist needed)",
)
def test_live_imd_nowcast_yields_at_least_one_row():
    # Stub — live JSON path not yet implemented (Plan 2 ships the PDF/HTML path).
    pytest.skip("live IMD JSON nowcast path not implemented in Plan 2; pending API whitelist.")
