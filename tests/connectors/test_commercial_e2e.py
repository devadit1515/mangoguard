"""End-to-end integration test for the 4 commercial Plan 3 connectors.

Wires Pessl + Fyllo + Fasal + CSV-fallback through the registry into a
single in-memory FeedStore. Plantix is deliberately excluded (dropped
from Plan 3 -- see registry module docstring). Asserts:

1. Each registered commercial source contributes >=1 row.
2. Per-source row counts match the fixtures' expected output.
3. Connector.run() audit trail (ingested_at + connector_run_id) is
   stamped on every row regardless of vendor.
4. Multi-source query into the merged store works.

This is the symmetric complement to test_baseline_e2e.py and locks the
Plan 3 acceptance criterion: 'all commercial connectors... into one
FeedStore' (4 here + Plantix explicitly skipped and documented).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.registry import get_connector
from mangoguard.schema import ConnectorSource

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "connectors" / "fixtures"

_WINDOW_START = datetime(2025, 7, 11, 18, 0, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 13, tzinfo=timezone.utc)


def test_four_commercial_connectors_into_one_store(store):
    """Run Pessl + Fyllo + Fasal + CSV-fallback through one FeedStore."""
    ctx = ConnectorContext(store=store)

    pessl = get_connector(
        ConnectorSource.PESSL,
        ctx,
        station_id="00000000",
        fixture_path=FIXTURES / "pessl_fieldclimate_sample_response.json",
    )
    n_pessl = pessl.run(since=_WINDOW_START, until=_WINDOW_END)

    fyllo = get_connector(
        ConnectorSource.FYLLO,
        ctx,
        fixture_path=FIXTURES / "fyllo_export.csv",
    )
    n_fyllo = fyllo.run(since=_WINDOW_START, until=_WINDOW_END)

    fasal = get_connector(
        ConnectorSource.FASAL,
        ctx,
        fixture_path=FIXTURES / "fasal_export.csv",
    )
    n_fasal = fasal.run(since=_WINDOW_START, until=_WINDOW_END)

    csv_fb = get_connector(
        ConnectorSource.CSV_FALLBACK,
        ctx,
        fixture_path=FIXTURES / "csv_fallback_sample.csv",
    )
    n_csv = csv_fb.run(since=_WINDOW_START, until=_WINDOW_END)

    assert n_pessl == 5
    assert n_fyllo == 8
    assert n_fasal == 8
    assert n_csv == 6

    by_source = store.count_by_source()
    assert by_source[ConnectorSource.PESSL] == 5
    assert by_source[ConnectorSource.FYLLO] == 8
    assert by_source[ConnectorSource.FASAL] == 8
    assert by_source[ConnectorSource.CSV_FALLBACK] == 6

    assert store.count() == 5 + 8 + 8 + 6  # 27


def test_audit_trail_stamped_across_commercial_sources(store):
    """Every commercial run() stamps ingested_at + a unique connector_run_id."""
    ctx = ConnectorContext(store=store)

    pessl = get_connector(
        ConnectorSource.PESSL,
        ctx,
        station_id="00000000",
        fixture_path=FIXTURES / "pessl_fieldclimate_sample_response.json",
    )
    pessl.run(since=_WINDOW_START, until=_WINDOW_END)

    fyllo = get_connector(
        ConnectorSource.FYLLO,
        ctx,
        fixture_path=FIXTURES / "fyllo_export.csv",
    )
    fyllo.run(since=_WINDOW_START, until=_WINDOW_END)

    pessl_rows = store.query_by_source(ConnectorSource.PESSL)
    fyllo_rows = store.query_by_source(ConnectorSource.FYLLO)

    assert all(r.ingested_at is not None for r in pessl_rows + fyllo_rows)
    assert all(r.connector_run_id is not None for r in pessl_rows + fyllo_rows)

    pessl_run_ids = {r.connector_run_id for r in pessl_rows}
    fyllo_run_ids = {r.connector_run_id for r in fyllo_rows}
    assert len(pessl_run_ids) == 1
    assert len(fyllo_run_ids) == 1
    assert pessl_run_ids != fyllo_run_ids


def test_pessl_and_csv_fallback_coexist_in_unified_schema(store):
    """Pessl rows have weather; CSV-fallback row 5 has satellite NDVI. Both coexist."""
    ctx = ConnectorContext(store=store)

    pessl = get_connector(
        ConnectorSource.PESSL,
        ctx,
        station_id="00000000",
        fixture_path=FIXTURES / "pessl_fieldclimate_sample_response.json",
    )
    pessl.run(since=_WINDOW_START, until=_WINDOW_END)

    csv_fb = get_connector(
        ConnectorSource.CSV_FALLBACK,
        ctx,
        fixture_path=FIXTURES / "csv_fallback_sample.csv",
    )
    csv_fb.run(since=_WINDOW_START, until=_WINDOW_END)

    pessl_rows = store.query_by_source(ConnectorSource.PESSL)
    csv_rows = store.query_by_source(ConnectorSource.CSV_FALLBACK)

    for r in pessl_rows:
        assert r.t_air_c is not None
        assert r.ndvi is None

    assert any(r.ndvi is not None for r in csv_rows)
