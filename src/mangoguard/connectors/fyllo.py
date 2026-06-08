"""Fyllo (AgriHawk) connector.

Fyllo has no public REST API. Two ingestion paths:

1. **CSV export** (default, offline-friendly): Fyllo's app lets users
   download chart data as CSV. The farmer drops the export file into
   ``ctx.secrets["FYLLO_EXPORT_DIR"]`` (or a single ``fixture_path=`` for
   tests). This is the path we test against because it produces
   structured data without OCR.

2. **Browser scrape** (live, stubbed): ``playwright`` automation logs in
   at ``https://app.fyllo.in/login`` and downloads the chart CSV. Only
   runs under ``@pytest.mark.integration_browser`` with real
   ``FYLLO_EMAIL`` + ``FYLLO_PASSWORD`` in ``ctx.secrets``.

Solar reading note: Fyllo reports solar in **lux**, not W/m^2. Direct lux
-> W/m^2 conversion depends on spectrum so we DROP the solar column
rather than emit a bogus number. Use Pessl or IMD for solar.

CSV column mapping:

| Fyllo column        | BlockObservation field   | Transform        |
|---------------------|--------------------------|------------------|
| timestamp           | ts                       | parse ISO 8601   |
| plot_id             | block_id                 | lower + slug     |
| temperature_c       | t_air_c                  | identity         |
| humidity_pct        | rh_pct                   | identity         |
| leaf_wetness_min    | leaf_wetness_hr          | / 60             |
| rain_mm             | precip_mm                | identity         |
| wind_speed_ms       | wind_speed_ms            | identity         |
| solar_lux           | (dropped -- see above)   | n/a              |
"""

from __future__ import annotations

import csv
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
    """Normalize plot names to schema-safe block_ids."""
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


class FylloConnector(Connector):
    """Fyllo per-plot weather feed from CSV exports."""

    source: ClassVar[ConnectorSource] = ConnectorSource.FYLLO
    name: ClassVar[str] = "fyllo"

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
            secret_dir = self.ctx.secrets.get("FYLLO_EXPORT_DIR")
            target_dir = Path(secret_dir) if secret_dir else None

        if target_dir is None or not target_dir.exists():
            logger.warning(
                "FylloConnector: no fixture_path/export_dir; "
                "set FYLLO_EXPORT_DIR or run via browser automation. "
                "Returning empty."
            )
            return

        csv_files = sorted(target_dir.glob("*.csv"))
        if not csv_files:
            logger.warning("FylloConnector: no .csv files in %s", target_dir)
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
        """Parse a Fyllo CSV export -- yields BlockObservations row-by-row."""
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            missing = _REQUIRED_COLUMNS - cols
            if missing:
                logger.warning(
                    "FylloConnector: %s missing required columns %s; skipping",
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
            logger.warning("Fyllo: dropping row with bad timestamp %r", row.get("timestamp"))
            return None
        plot = (row.get("plot_id") or "").strip()
        if not plot:
            logger.warning("Fyllo: dropping row with empty plot_id at %s", ts)
            return None

        leaf_wetness_min = _maybe_float(row.get("leaf_wetness_min"))
        leaf_wetness_hr = leaf_wetness_min / 60.0 if leaf_wetness_min is not None else None

        return BlockObservation(
            block_id=_slug(plot),
            ts=ts,
            source=ConnectorSource.FYLLO,
            t_air_c=_maybe_float(row.get("temperature_c")),
            rh_pct=_maybe_float(row.get("humidity_pct")),
            leaf_wetness_hr=leaf_wetness_hr,
            precip_mm=_maybe_float(row.get("rain_mm")),
            wind_speed_ms=_maybe_float(row.get("wind_speed_ms")),
        )
