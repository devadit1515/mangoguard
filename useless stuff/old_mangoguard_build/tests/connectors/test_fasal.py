"""Tests for the Fasal (Wolkus) CSV-export connector."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.fasal import FasalConnector
from mangoguard.schema import BlockObservation, ConnectorSource

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "fasal_export.csv"

_WINDOW_START = datetime(2025, 7, 11, 18, 0, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 12, 18, 0, tzinfo=timezone.utc)


def test_fixture_yields_all_eight_rows():
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 8
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.source == ConnectorSource.FASAL for r in rows)


def test_plot_id_becomes_slugged_block_id():
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    block_ids = {r.block_id for r in rows}
    assert "devgad-alphonso" in block_ids
    assert "vengurla-block-2" in block_ids


def test_temperature_and_humidity_passthrough():
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    devgad = sorted([r for r in rows if r.block_id == "devgad-alphonso"], key=lambda r: r.ts)
    assert devgad[0].t_air_c == pytest.approx(27.4)
    assert devgad[0].rh_pct == pytest.approx(89.0)


def test_leaf_wetness_minutes_to_hours():
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    devgad = sorted([r for r in rows if r.block_id == "devgad-alphonso"], key=lambda r: r.ts)
    assert devgad[0].leaf_wetness_hr == pytest.approx(0.3)
    assert devgad[-1].leaf_wetness_hr == pytest.approx(28 / 60.0, rel=1e-4)


def test_solar_w_m2_passed_through_unchanged():
    """Fasal reports solar in W/m^2 directly -- no conversion needed."""
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        assert r.solar_w_m2 == pytest.approx(0.0)


def test_soil_moisture_30cm_becomes_primary_soil_moisture_pct():
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    devgad = sorted([r for r in rows if r.block_id == "devgad-alphonso"], key=lambda r: r.ts)
    assert devgad[0].soil_moisture_pct == pytest.approx(32.1)
    assert devgad[-1].soil_moisture_pct == pytest.approx(32.5)


def test_soil_moisture_60cm_preserved_in_notes():
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    devgad_first = next(r for r in rows if r.block_id == "devgad-alphonso")
    assert devgad_first.notes is not None
    parsed = json.loads(devgad_first.notes)
    assert parsed["soil_moisture_60cm"] == pytest.approx(28.5)


def test_ts_is_timezone_aware_ist():
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        assert r.ts.tzinfo is not None
        ist = r.ts.astimezone(ZoneInfo("Asia/Kolkata"))
        assert ist.date().isoformat() == "2025-07-12"


def test_missing_rh_cell_yields_none_not_zero():
    """Vengurla 00:30 row has empty rh_pct -> None, not 0."""
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    vengurla = sorted([r for r in rows if r.block_id == "vengurla-block-2"], key=lambda r: r.ts)
    assert vengurla[-1].rh_pct is None
    assert vengurla[-1].t_air_c == pytest.approx(27.8)


def test_window_filter_excludes_out_of_range():
    conn = FasalConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(
        conn.fetch(
            since=datetime(2025, 8, 1, tzinfo=timezone.utc),
            until=datetime(2025, 8, 31, tzinfo=timezone.utc),
        )
    )
    assert rows == []


def test_bad_timestamp_row_dropped_with_warning(tmp_path, caplog):
    bad_csv = """timestamp,plot_id,t_air_c
not-a-date,Plot A,27.0
2025-07-12T00:00:00+05:30,Plot A,27.5
"""
    fixture = tmp_path / "bad.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = FasalConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].t_air_c == pytest.approx(27.5)
    assert any("Fasal" in r.message for r in caplog.records)


def test_empty_plot_id_dropped(tmp_path, caplog):
    bad_csv = """timestamp,plot_id,t_air_c
2025-07-12T00:00:00+05:30,,27.0
2025-07-12T00:00:00+05:30,Plot B,27.5
"""
    fixture = tmp_path / "empty_plot.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = FasalConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].block_id == "plot-b"


def test_missing_required_columns_skips_file_with_warning(tmp_path, caplog):
    bad_csv = """plot_id,t_air_c
Plot A,27.0
"""
    fixture = tmp_path / "missing_ts.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = FasalConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("missing required columns" in r.message for r in caplog.records)


def test_export_dir_globs_csv_files(tmp_path):
    (tmp_path / "a.csv").write_text(
        "timestamp,plot_id,t_air_c\n2025-07-12T00:00:00+05:30,A,27.0\n",
        encoding="utf-8",
    )
    (tmp_path / "b.csv").write_text(
        "timestamp,plot_id,t_air_c\n2025-07-12T00:10:00+05:30,B,28.0\n",
        encoding="utf-8",
    )
    conn = FasalConnector(ConnectorContext(), export_dir=tmp_path)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    block_ids = {r.block_id for r in rows}
    assert block_ids == {"a", "b"}


def test_fetch_without_fixture_or_export_dir_returns_empty(caplog):
    conn = FasalConnector(ConnectorContext())
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("FASAL_EXPORT_DIR" in r.message for r in caplog.records)


def test_connector_runs_end_to_end_to_store(store):
    conn = FasalConnector(ConnectorContext(store=store), fixture_path=FIXTURE_PATH)
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 8
    assert store.count_by_source().get(ConnectorSource.FASAL, 0) == 8
