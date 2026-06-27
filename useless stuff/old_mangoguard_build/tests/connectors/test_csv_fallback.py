"""Tests for the vendor-agnostic CSV fallback connector."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.csv_fallback import CSVFallbackConnector
from mangoguard.schema import BlockObservation, ConnectorSource

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "csv_fallback_sample.csv"

_WINDOW_START = datetime(2025, 7, 11, 18, 0, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 12, 18, 0, tzinfo=timezone.utc)


def test_fixture_yields_all_six_rows():
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 6
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.source == ConnectorSource.CSV_FALLBACK for r in rows)


def test_block_ids_preserved_lowercase():
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    block_ids = {r.block_id for r in rows}
    assert "south-block" in block_ids
    assert "north-block" in block_ids


def test_weather_fields_passthrough():
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    south_first = next(r for r in rows if r.block_id == "south-block" and r.t_air_c is not None)
    assert south_first.t_air_c == pytest.approx(27.3)
    assert south_first.rh_pct == pytest.approx(90.5)
    assert south_first.precip_mm == pytest.approx(0.4)


def test_satellite_fields_passthrough():
    """Row 4 (north-block 00:00) has NDVI/NDRE/NDMI populated."""
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    north_sat = next(r for r in rows if r.block_id == "north-block" and r.ndvi is not None)
    assert north_sat.ndvi == pytest.approx(0.71)
    assert north_sat.ndre == pytest.approx(0.42)
    assert north_sat.ndmi == pytest.approx(0.18)


def test_domain_fields_passthrough():
    """Row 6 carries cropsap_pest_pressure + plantix_diagnosis_class + notes JSON."""
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    domain = next(r for r in rows if r.plantix_diagnosis_class is not None)
    assert domain.plantix_diagnosis_class == "anthracnose"
    assert domain.cropsap_pest_pressure == pytest.approx(34.5)
    assert domain.notes is not None
    assert "sample fields used" in domain.notes


def test_blank_cells_yield_none_not_zero():
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    # Row 4 (north-block 00:00) has empty leaf_wetness_hr cell
    north_no_leafwet = next(r for r in rows if r.block_id == "north-block" and r.ndvi is not None)
    assert north_no_leafwet.leaf_wetness_hr is None
    assert north_no_leafwet.t_air_c == pytest.approx(27.4)


def test_ts_is_timezone_aware():
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        assert r.ts.tzinfo is not None


def test_window_filter_excludes_out_of_range():
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=FIXTURE_PATH)
    rows = list(
        conn.fetch(
            since=datetime(2025, 8, 1, tzinfo=timezone.utc),
            until=datetime(2025, 8, 31, tzinfo=timezone.utc),
        )
    )
    assert rows == []


def test_missing_required_columns_skips_file_with_warning(tmp_path, caplog):
    bad_csv = """block_id,ts_iso
south,2025-07-12T00:00:00+05:30
"""
    fixture = tmp_path / "no_source.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("missing required columns" in r.message for r in caplog.records)


def test_wrong_source_value_skips_row(tmp_path, caplog):
    bad_csv = """block_id,ts_iso,source
south,2025-07-12T00:00:00+05:30,fyllo
north,2025-07-12T00:00:00+05:30,csv_fallback
"""
    fixture = tmp_path / "wrong_source.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].block_id == "north"


def test_bad_ts_iso_row_skipped(tmp_path, caplog):
    bad_csv = """block_id,ts_iso,source
south,not-a-date,csv_fallback
south,2025-07-12T00:00:00+05:30,csv_fallback
"""
    fixture = tmp_path / "bad_ts.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert any("CSVFallback" in r.message for r in caplog.records)


def test_out_of_range_rh_pct_fails_schema_validation_and_skips(tmp_path, caplog):
    """RH=150 is out of [0,100] range -- schema rejects, row skipped."""
    bad_csv = """block_id,ts_iso,source,rh_pct
south,2025-07-12T00:00:00+05:30,csv_fallback,150.0
north,2025-07-12T00:00:00+05:30,csv_fallback,85.0
"""
    fixture = tmp_path / "bad_rh.csv"
    fixture.write_text(bad_csv, encoding="utf-8")
    conn = CSVFallbackConnector(ConnectorContext(), fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].block_id == "north"
    assert any("validation" in r.message.lower() for r in caplog.records)


def test_upload_dir_globs_csv_files(tmp_path):
    (tmp_path / "a.csv").write_text(
        "block_id,ts_iso,source\nA,2025-07-12T00:00:00+05:30,csv_fallback\n",
        encoding="utf-8",
    )
    (tmp_path / "b.csv").write_text(
        "block_id,ts_iso,source\nB,2025-07-12T00:10:00+05:30,csv_fallback\n",
        encoding="utf-8",
    )
    conn = CSVFallbackConnector(ConnectorContext(), upload_dir=tmp_path)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    block_ids = {r.block_id for r in rows}
    assert block_ids == {"A", "B"}


def test_fetch_without_fixture_or_upload_dir_returns_empty(caplog):
    conn = CSVFallbackConnector(ConnectorContext())
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("CSV_FALLBACK_UPLOAD_DIR" in r.message for r in caplog.records)


def test_connector_runs_end_to_end_to_store(store):
    conn = CSVFallbackConnector(ConnectorContext(store=store), fixture_path=FIXTURE_PATH)
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 6
    assert store.count_by_source().get(ConnectorSource.CSV_FALLBACK, 0) == 6
