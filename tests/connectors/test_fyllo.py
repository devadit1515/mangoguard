"""Tests for the Fyllo (AgriHawk) CSV-export connector."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.fyllo import FylloConnector
from mangoguard.schema import BlockObservation, ConnectorSource

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "fyllo_export.csv"

# Fixture timestamps are IST (+05:30). Window covers 12 July 2025 IST.
_WINDOW_START = datetime(2025, 7, 11, 18, 0, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 12, 18, 0, tzinfo=timezone.utc)


def test_fixture_yields_all_eight_rows():
    conn = FylloConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 8
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.source == ConnectorSource.FYLLO for r in rows)


def test_plot_id_becomes_slugged_block_id():
    conn = FylloConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    block_ids = {r.block_id for r in rows}
    assert "hapus-north" in block_ids
    assert "hapus-south" in block_ids


def test_temperature_and_humidity_passthrough():
    conn = FylloConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    north_rows = sorted([r for r in rows if r.block_id == "hapus-north"], key=lambda r: r.ts)
    assert north_rows[0].t_air_c == pytest.approx(27.3)
    assert north_rows[0].rh_pct == pytest.approx(90.5)


def test_leaf_wetness_minutes_to_hours():
    """Fyllo reports leaf_wetness_min; schema wants hours."""
    conn = FylloConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    north_rows = sorted([r for r in rows if r.block_id == "hapus-north"], key=lambda r: r.ts)
    assert north_rows[0].leaf_wetness_hr == pytest.approx(0.25)
    assert north_rows[-1].leaf_wetness_hr == pytest.approx(20 / 60.0, rel=1e-4)


def test_solar_lux_is_dropped_not_passed_through():
    """Fyllo solar is lux, not W/m^2 -- schema solar_w_m2 must be None."""
    conn = FylloConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert all(r.solar_w_m2 is None for r in rows)


def test_ts_is_timezone_aware_ist():
    conn = FylloConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        assert r.ts.tzinfo is not None
        ist = r.ts.astimezone(ZoneInfo("Asia/Kolkata"))
        assert ist.date().isoformat() == "2025-07-12"


def test_missing_rain_cell_yields_none_not_zero():
    """Hapus South 00:40 row has empty rain cell -> precip_mm is None."""
    conn = FylloConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    south_rows = sorted([r for r in rows if r.block_id == "hapus-south"], key=lambda r: r.ts)
    assert south_rows[-1].precip_mm is None
    assert south_rows[-1].t_air_c == pytest.approx(27.2)


def test_window_filter_excludes_out_of_range():
    conn = FylloConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(
        conn.fetch(
            since=datetime(2025, 8, 1, tzinfo=timezone.utc),
            until=datetime(2025, 8, 31, tzinfo=timezone.utc),
        )
    )
    assert rows == []


def test_bad_timestamp_row_dropped_with_warning(tmp_path, caplog):
    bad_csv = """timestamp,plot_id,temperature_c
not-a-date,Plot A,27.0
2025-07-12T00:00:00+05:30,Plot A,27.5
"""
    fixture = tmp_path / "bad.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = FylloConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].t_air_c == pytest.approx(27.5)
    assert any("Fyllo" in r.message for r in caplog.records)


def test_empty_plot_id_row_dropped(tmp_path, caplog):
    bad_csv = """timestamp,plot_id,temperature_c
2025-07-12T00:00:00+05:30,,27.0
2025-07-12T00:00:00+05:30,Plot B,27.5
"""
    fixture = tmp_path / "empty_plot.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = FylloConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].block_id == "plot-b"


def test_missing_required_columns_skips_file_with_warning(tmp_path, caplog):
    bad_csv = """plot_id,temperature_c
Plot A,27.0
"""
    fixture = tmp_path / "missing_ts.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = FylloConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("missing required columns" in r.message for r in caplog.records)


def test_export_dir_globs_csv_files(tmp_path):
    """If export_dir set, all *.csv files in it are read."""
    (tmp_path / "a.csv").write_text(
        "timestamp,plot_id,temperature_c\n2025-07-12T00:00:00+05:30,A,27.0\n",
        encoding="utf-8",
    )
    (tmp_path / "b.csv").write_text(
        "timestamp,plot_id,temperature_c\n2025-07-12T00:10:00+05:30,B,28.0\n",
        encoding="utf-8",
    )
    (tmp_path / "not_a_csv.txt").write_text("ignored", encoding="utf-8")
    conn = FylloConnector(ConnectorContext(), export_dir=tmp_path)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    block_ids = {r.block_id for r in rows}
    assert block_ids == {"a", "b"}


def test_fetch_without_fixture_or_export_dir_returns_empty(caplog):
    conn = FylloConnector(ConnectorContext())
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("FYLLO_EXPORT_DIR" in r.message for r in caplog.records)


def test_connector_runs_end_to_end_to_store(store):
    conn = FylloConnector(ConnectorContext(store=store), fixture_path=FIXTURE_PATH)
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 8
    assert store.count_by_source().get(ConnectorSource.FYLLO, 0) == 8
