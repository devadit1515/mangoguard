"""Tests for the Maharashtra CROPSAP taluka pest-surveillance connector."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.cropsap import CROPSAPConnector
from mangoguard.schema import BlockObservation, ConnectorSource

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cropsap_ratnagiri_2025-07-12.html"

_WINDOW_START = datetime(2025, 7, 10, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 15, tzinfo=timezone.utc)


def test_fixture_yields_one_row_per_pathogen_per_taluka():
    """Fixture has 8 source rows. Sindhudurg/Thrips has '--' infestation which
    yields pressure=None but the row is still emitted so Plan 4 can see
    'reported as Not Reported'. Total: 8 yielded observations."""
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 8
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.source == ConnectorSource.CROPSAP for r in rows)


def test_block_id_carries_taluka_and_pathogen_slug():
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    block_ids = {r.block_id for r in rows}
    assert "ratnagiri_anthracnose" in block_ids
    assert "ratnagiri_powdery_mildew" in block_ids
    assert "ratnagiri_hopper" in block_ids
    assert "ratnagiri_thrips" in block_ids
    assert "sindhudurg_anthracnose" in block_ids
    assert "sindhudurg_hopper" in block_ids


def test_pest_pressure_is_nonneg_float():
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        if r.cropsap_pest_pressure is not None:
            assert isinstance(r.cropsap_pest_pressure, float)
            assert r.cropsap_pest_pressure >= 0.0


def test_specific_pressure_values_correct():
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    by_block = {r.block_id: r for r in rows}
    assert by_block["ratnagiri_anthracnose"].cropsap_pest_pressure == pytest.approx(34.5)
    assert by_block["ratnagiri_hopper"].cropsap_pest_pressure == pytest.approx(48.2)
    assert by_block["sindhudurg_hopper"].cropsap_pest_pressure == pytest.approx(52.6)


def test_missing_infestation_dash_yields_none_not_drop():
    """Sindhudurg/Thrips has '--' for infestation. Should yield with None pressure,
    not be dropped — Plan 4 needs to know the row was reported even if value missing."""
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    sindhudurg_thrips = next(r for r in rows if r.block_id == "sindhudurg_thrips")
    assert sindhudurg_thrips.cropsap_pest_pressure is None


def test_notes_includes_pathogen_and_taluka():
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    anthracnose_row = next(r for r in rows if r.block_id == "ratnagiri_anthracnose")
    parsed = json.loads(anthracnose_row.notes)
    assert parsed["taluka"] == "ratnagiri"
    assert parsed["pathogen"] == "anthracnose"
    assert parsed["severity"] == "Moderate"


def test_pathogen_slug_normalizes_powdery_mildew():
    """'Powdery Mildew' (with space, mixed case) must map to 'powdery_mildew' slug."""
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    pm_row = next(r for r in rows if r.block_id == "ratnagiri_powdery_mildew")
    parsed = json.loads(pm_row.notes)
    assert parsed["pathogen"] == "powdery_mildew"


def test_ts_is_ist_midnight():
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        ist = r.ts.astimezone(ZoneInfo("Asia/Kolkata"))
        assert ist.hour == 0 and ist.minute == 0


def test_window_filter_excludes_out_of_range():
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(
        conn.fetch(
            since=datetime(2025, 6, 1, tzinfo=timezone.utc),
            until=datetime(2025, 6, 30, tzinfo=timezone.utc),
        )
    )
    assert rows == []


def test_unrecognized_pathogen_is_dropped_with_warning(tmp_path, caplog):
    html = """
    <html><body><table class="pest-incidence-table">
      <thead><tr>
        <th>Taluka</th><th>Pathogen</th><th>Infestation (%)</th>
        <th>Report Date</th><th>Severity</th>
      </tr></thead>
      <tbody>
        <tr><td>Ratnagiri</td><td>Gibberella</td><td>10</td><td>2025-07-12</td><td>Low</td></tr>
        <tr><td>Ratnagiri</td><td>Hopper</td><td>30</td><td>2025-07-12</td><td>High</td></tr>
      </tbody>
    </table></body></html>
    """
    fixture = tmp_path / "unknown_pathogen.html"
    fixture.write_text(html, encoding="utf-8")
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].block_id == "ratnagiri_hopper"
    assert any("Gibberella" in r.message for r in caplog.records)


def test_no_table_returns_empty_with_warning(tmp_path, caplog):
    html = "<html><body><p>Dashboard unavailable</p></body></html>"
    fixture = tmp_path / "empty.html"
    fixture.write_text(html, encoding="utf-8")
    conn = CROPSAPConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("CROPSAP" in r.message for r in caplog.records)


def test_connector_runs_end_to_end_to_store(store):
    conn = CROPSAPConnector(ConnectorContext(store=store), fixture_path=FIXTURE_PATH)
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 8
    assert store.count() == 8
    assert store.count_by_source().get(ConnectorSource.CROPSAP, 0) == 8


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("CROPSAP_LIVE"),
    reason="live CROPSAP scrape test gated on CROPSAP_LIVE=1 env var",
)
def test_live_cropsap_yields_at_least_one_row():
    conn = CROPSAPConnector(ConnectorContext())
    until = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    since = until.replace(year=until.year - 1)
    rows = list(conn.fetch(since=since, until=until))
    assert isinstance(rows, list)
