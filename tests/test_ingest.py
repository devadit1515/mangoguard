"""Node-log ingest: JSON and CSV parse to the same Reading the engine consumes."""

from __future__ import annotations

import json

from aamrakshak.io.ingest import readings_from_csv, readings_from_node_json
from aamrakshak.riskengine.anthracnose import anthracnose_risk

SAMPLE = {
    "node_id": "AR-01",
    "date": "2026-03-12",
    "t_max_c": 31.2,
    "t_min_c": 23.4,
    "rh_morning_pct": 90.0,
    "leaf_wetness_hr": 9.5,
    "sunshine_hr": 5.0,
    "wind_speed_ms": 1.8,
    "risk_pct": 41.0,
}


def test_json_single_and_list():
    one = readings_from_node_json(json.dumps(SAMPLE))
    many = readings_from_node_json([SAMPLE, SAMPLE])
    assert len(one) == 1 and len(many) == 2
    assert one[0].node_id == "AR-01"
    assert 0.0 <= anthracnose_risk(one[0].to_inputs()) <= 1.0


def test_json_defaults_when_no_light_wind():
    minimal = {k: v for k, v in SAMPLE.items() if k not in ("sunshine_hr", "wind_speed_ms")}
    r = readings_from_node_json(minimal)[0]
    assert r.sunshine_hr > 0 and r.wind_speed_ms > 0  # neutral fallbacks applied


def test_csv_roundtrip(tmp_path):
    p = tmp_path / "log.csv"
    cols = [
        "node_id",
        "date",
        "t_max_c",
        "t_min_c",
        "rh_morning_pct",
        "leaf_wetness_hr",
        "risk_pct",
    ]
    p.write_text(
        ",".join(cols) + "\n" + "AR-01,2026-03-12,31.2,23.4,90,9.5,41.0\n",
        encoding="utf-8",
    )
    rows = readings_from_csv(p)
    assert len(rows) == 1
    assert rows[0].leaf_wetness_hr == 9.5
