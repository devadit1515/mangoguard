"""Parse real AamRakshak node logs into ``Reading`` records.

The node writes a daily summary to flash (CSV) and can POST the same record as
JSON over WiFi. Both collapse to one ``Reading``, which feeds the same risk
engine the evaluation uses, so a real node and a simulated season share a code
path. Sunshine and wind are optional (the node has no light/wind sensor); when
absent they default to neutral values or a supplied district feed.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from aamrakshak.riskengine.anthracnose import AnthracnoseInputs

# Neutral fallbacks when the node cannot supply a field (no light/wind sensor).
DEFAULT_SUNSHINE_HR = 7.0
DEFAULT_WIND_MS = 1.5


@dataclass(frozen=True, slots=True)
class Reading:
    """One daily summary from a node (or a simulated equivalent)."""

    node_id: str
    date: str
    t_max_c: float
    t_min_c: float
    rh_morning_pct: float
    leaf_wetness_hr: float
    sunshine_hr: float = DEFAULT_SUNSHINE_HR
    wind_speed_ms: float = DEFAULT_WIND_MS
    risk_pct: float | None = None

    def to_inputs(self) -> AnthracnoseInputs:
        return AnthracnoseInputs(
            t_max_c=self.t_max_c,
            t_min_c=self.t_min_c,
            rh_morning_pct=self.rh_morning_pct,
            leaf_wetness_hr=self.leaf_wetness_hr,
            sunshine_hr=self.sunshine_hr,
            wind_speed_ms=self.wind_speed_ms,
        )


def _reading_from_dict(d: dict) -> Reading:
    return Reading(
        node_id=str(d.get("node_id", "unknown")),
        date=str(d.get("date") or d.get("ts") or ""),
        t_max_c=float(d["t_max_c"]),
        t_min_c=float(d["t_min_c"]),
        rh_morning_pct=float(d.get("rh_morning_pct", d.get("rh_pct"))),
        leaf_wetness_hr=float(d["leaf_wetness_hr"]),
        sunshine_hr=float(d.get("sunshine_hr", DEFAULT_SUNSHINE_HR)),
        wind_speed_ms=float(d.get("wind_speed_ms", DEFAULT_WIND_MS)),
        risk_pct=float(d["risk_pct"]) if d.get("risk_pct") is not None else None,
    )


def readings_from_node_json(payload: str | dict | list) -> list[Reading]:
    """Parse a node JSON POST: a single object or a list of daily summaries."""
    data = json.loads(payload) if isinstance(payload, str) else payload
    if isinstance(data, dict):
        data = [data]
    return [_reading_from_dict(d) for d in data]


def readings_from_csv(path: str | Path) -> list[Reading]:
    """Parse the node's on-flash daily CSV log."""
    with open(path, newline="", encoding="utf-8") as f:
        return [_reading_from_dict(row) for row in csv.DictReader(f)]
