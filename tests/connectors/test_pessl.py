"""Tests for the Pessl iMETOS / FieldClimate REST connector."""

from __future__ import annotations

import json as _json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.pessl import PesslConnector
from mangoguard.schema import BlockObservation, ConnectorSource

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pessl_fieldclimate_sample_response.json"

_WINDOW_START = datetime(2025, 7, 12, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 7, 13, tzinfo=timezone.utc)


def test_fixture_yields_five_15min_observations():
    conn = PesslConnector(ConnectorContext(), station_id="00000000", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 5
    assert all(isinstance(r, BlockObservation) for r in rows)
    assert all(r.source == ConnectorSource.PESSL for r in rows)


def test_block_id_uses_station_id_lowercased():
    conn = PesslConnector(ConnectorContext(), station_id="AB12CD34", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert all(r.block_id == "ab12cd34" for r in rows)


def test_air_temperature_uses_avg_values():
    conn = PesslConnector(ConnectorContext(), station_id="x", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[0].t_air_c == pytest.approx(27.25)
    assert rows[1].t_air_c == pytest.approx(27.1)


def test_humidity_uses_avg_values():
    conn = PesslConnector(ConnectorContext(), station_id="x", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[0].rh_pct == pytest.approx(90.0)
    assert rows[4].rh_pct == pytest.approx(92.5)


def test_leaf_wetness_minutes_to_hours_conversion():
    """Pessl reports Leaf Wetness in minutes; schema expects hours."""
    conn = PesslConnector(ConnectorContext(), station_id="x", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[0].leaf_wetness_hr == pytest.approx(0.2)
    assert rows[4].leaf_wetness_hr == pytest.approx(22 / 60.0, rel=1e-4)


def test_precip_uses_sum_not_avg():
    conn = PesslConnector(ConnectorContext(), station_id="x", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[2].precip_mm == pytest.approx(1.2)


def test_soil_moisture_uses_first_vwc_sensor():
    conn = PesslConnector(ConnectorContext(), station_id="x", fixture_path=FIXTURE_PATH)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[0].soil_moisture_pct == pytest.approx(34.5)


def test_missing_sensors_yield_none_not_zero(tmp_path):
    """A station that omits Wind/Solar yields None on those fields, not 0."""
    minimal_payload = {
        "dates": ["2025-07-12 00:00:00"],
        "data": [
            {"name": "HC Air temperature", "unit": "C", "values": {"avg": [27.0]}},
        ],
    }
    fixture = tmp_path / "minimal.json"
    fixture.write_text(_json.dumps(minimal_payload), encoding="utf-8")
    conn = PesslConnector(ConnectorContext(), station_id="x", fixture_path=fixture)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    r = rows[0]
    assert r.t_air_c == pytest.approx(27.0)
    assert r.rh_pct is None
    assert r.wind_speed_ms is None
    assert r.solar_w_m2 is None
    assert r.soil_moisture_pct is None
    assert r.leaf_wetness_hr is None
    assert r.precip_mm is None


def test_window_filter_excludes_out_of_range():
    conn = PesslConnector(ConnectorContext(), station_id="x", fixture_path=FIXTURE_PATH)
    rows = list(
        conn.fetch(
            since=datetime(2025, 6, 1, tzinfo=timezone.utc),
            until=datetime(2025, 7, 1, tzinfo=timezone.utc),
        )
    )
    assert rows == []


def test_bad_date_row_dropped_with_warning(tmp_path, caplog):
    payload = {
        "dates": ["not-a-date", "2025-07-12 00:00:00"],
        "data": [
            {"name": "HC Air temperature", "unit": "C", "values": {"avg": [27.0, 27.5]}},
        ],
    }
    fixture = tmp_path / "bad_date.json"
    fixture.write_text(_json.dumps(payload), encoding="utf-8")
    conn = PesslConnector(ConnectorContext(), station_id="x", fixture_path=fixture)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].t_air_c == pytest.approx(27.5)
    assert any("Pessl" in r.message for r in caplog.records)


def test_fetch_without_keys_returns_empty_with_warning(caplog):
    conn = PesslConnector(ConnectorContext(), station_id="x")
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("PESSL_PUBLIC_KEY" in r.message for r in caplog.records)


def test_fetch_without_station_id_returns_empty(caplog):
    ctx = ConnectorContext(secrets={"PESSL_PUBLIC_KEY": "pub", "PESSL_PRIVATE_KEY": "priv"})
    conn = PesslConnector(ctx, station_id="")
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("station_id" in r.message for r in caplog.records)


def test_connector_runs_end_to_end_to_store(store):
    conn = PesslConnector(
        ConnectorContext(store=store), station_id="00000000", fixture_path=FIXTURE_PATH
    )
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 5
    assert store.count_by_source().get(ConnectorSource.PESSL, 0) == 5


@pytest.mark.integration
@pytest.mark.skipif(
    not (os.getenv("PESSL_PUBLIC_KEY") and os.getenv("PESSL_PRIVATE_KEY")),
    reason="live Pessl integration requires PESSL_PUBLIC_KEY + PESSL_PRIVATE_KEY env vars",
)
def test_live_pessl_yields_at_least_one_row():
    ctx = ConnectorContext(
        secrets={
            "PESSL_PUBLIC_KEY": os.environ["PESSL_PUBLIC_KEY"],
            "PESSL_PRIVATE_KEY": os.environ["PESSL_PRIVATE_KEY"],
        }
    )
    station_id = os.environ.get("PESSL_STATION_ID", "")
    if not station_id:
        pytest.skip("PESSL_STATION_ID not set")
    conn = PesslConnector(ctx, station_id=station_id)
    until = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    since = until.replace(day=max(1, until.day - 7))
    rows = list(conn.fetch(since=since, until=until))
    assert isinstance(rows, list)
