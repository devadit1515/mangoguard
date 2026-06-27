"""Fasal (Wolkus) connector.

Fasal stations expose data through the app, not a public REST API. The
ingestion contract is the user-exported CSV (similar to Fyllo) with
Fasal's specific column names. Browser-automation against
``https://app.fasal.co/`` is a future enhancement gated on
``@pytest.mark.integration_browser``.

CSV column mapping:

| Fasal column          | BlockObservation field   | Transform               |
|-----------------------|--------------------------|-------------------------|
| timestamp             | ts                       | parse ISO 8601          |
| plot_id               | block_id                 | lower + slug            |
| t_air_c               | t_air_c                  | identity                |
| rh_pct                | rh_pct                   | identity                |
| leaf_wetness_minutes  | leaf_wetness_hr          | / 60                    |
| rain_mm               | precip_mm                | identity                |
| solar_w_m2            | solar_w_m2               | identity (W/m^2 -- unlike Fyllo lux) |
| soil_moisture_30cm    | soil_moisture_pct        | identity (primary depth)|
| soil_moisture_60cm    | (preserved in notes)     | JSON                    |
| wind_speed_ms         | wind_speed_ms            | identity                |

Default mode is CSV-in-directory: glob ``*.csv`` from
``ctx.secrets["FASAL_EXPORT_DIR"]`` (or ``export_dir=`` for tests).
``fixture_path=`` parses a single file.
"""

from __future__ import annotations

import csv
import json
import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.schema import BlockObservation, ConnectorSource

logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = {"timestamp", "plot_id"}


def _slug(s: str) -> str:
    return s.strip().lower().replace(" ", "-")[:32]


def _parse_iso8601(value: str) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _maybe_float(value) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "n/a", "na", "--"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


class FasalConnector(Connector):
    """Fasal per-plot weather feed from CSV exports."""

    source: ClassVar[ConnectorSource] = ConnectorSource.FASAL
    name: ClassVar[str] = "fasal"

    def __init__(
        self,
        ctx: ConnectorContext,
        *,
        fixture_path: str | Path | None = None,
        export_dir: str | Path | None = None,
    ) -> None:
        super().__init__(ctx)
        self._fixture_path = Path(fixture_path) if fixture_path else None
        self._export_dir = Path(export_dir) if export_dir else None

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        if self._fixture_path is not None and self._fixture_path.exists():
            yield from self._parse_csv(self._fixture_path, since=since, until=until)
            return

        target_dir = self._export_dir
        if target_dir is None:
            secret_dir = self.ctx.secrets.get("FASAL_EXPORT_DIR")
            target_dir = Path(secret_dir) if secret_dir else None

        if target_dir is None or not target_dir.exists():
            logger.warning(
                "FasalConnector: no fixture_path/export_dir; set "
                "FASAL_EXPORT_DIR or pass export_dir=. Returning empty."
            )
            return

        csv_files = sorted(target_dir.glob("*.csv"))
        if not csv_files:
            logger.warning("FasalConnector: no .csv files in %s", target_dir)
            return
        for csv_path in csv_files:
            yield from self._parse_csv(csv_path, since=since, until=until)

    def _parse_csv(
        self,
        path: Path,
        *,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            missing = _REQUIRED_COLUMNS - cols
            if missing:
                logger.warning(
                    "FasalConnector: %s missing required columns %s; skipping",
                    path,
                    sorted(missing),
                )
                return
            for row in reader:
                obs = self._row_to_observation(row)
                if obs is None:
                    continue
                if since <= obs.ts < until:
                    yield obs

    @staticmethod
    def _row_to_observation(row: dict) -> BlockObservation | None:
        ts = _parse_iso8601(row.get("timestamp", ""))
        if ts is None:
            logger.warning("Fasal: dropping row with bad timestamp %r", row.get("timestamp"))
            return None
        plot = (row.get("plot_id") or "").strip()
        if not plot:
            logger.warning("Fasal: dropping row with empty plot_id at %s", ts)
            return None

        leaf_wetness_min = _maybe_float(row.get("leaf_wetness_minutes"))
        leaf_wetness_hr = leaf_wetness_min / 60.0 if leaf_wetness_min is not None else None

        soil_30 = _maybe_float(row.get("soil_moisture_30cm"))
        soil_60 = _maybe_float(row.get("soil_moisture_60cm"))
        notes_payload: dict = {}
        if soil_60 is not None:
            notes_payload["soil_moisture_60cm"] = soil_60
        notes_json = json.dumps(notes_payload)[:512] if notes_payload else None

        return BlockObservation(
            block_id=_slug(plot),
            ts=ts,
            source=ConnectorSource.FASAL,
            t_air_c=_maybe_float(row.get("t_air_c")),
            rh_pct=_maybe_float(row.get("rh_pct")),
            leaf_wetness_hr=leaf_wetness_hr,
            precip_mm=_maybe_float(row.get("rain_mm")),
            wind_speed_ms=_maybe_float(row.get("wind_speed_ms")),
            solar_w_m2=_maybe_float(row.get("solar_w_m2")),
            soil_moisture_pct=soil_30,
            notes=notes_json,
        )
