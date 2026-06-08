"""Vendor-agnostic CSV fallback connector.

Any data source without a dedicated MangoGuard connector can produce a
CSV matching ``data/csv_fallback_schema.yaml`` and feed this connector.
The required columns are ``block_id``, ``ts_iso``, and ``source`` (which
must be the literal string ``csv_fallback``); every other column is
optional and maps 1:1 to a ``BlockObservation`` field of the same name.

The schema mirrors the unified ``BlockObservation`` directly, so this
connector is also the canonical "round-trip via disk" path: dump rows
to CSV, edit by hand, re-ingest.

Validation strategy: pydantic ``BlockObservation(**row)`` per row inside
a try/except. ``ValidationError`` -> WARNING + skip that row, never
crash the whole file. This is intentional: the farmer hand-editing a
single bad cell should not lose the rest of the upload.
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from pydantic import ValidationError

from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.schema import BlockObservation, ConnectorSource

logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = {"block_id", "ts_iso", "source"}
_FLOAT_COLUMNS = {
    "t_air_c",
    "rh_pct",
    "leaf_wetness_hr",
    "precip_mm",
    "wind_speed_ms",
    "solar_w_m2",
    "soil_moisture_pct",
    "ndvi",
    "ndre",
    "ndmi",
    "cropsap_pest_pressure",
    "mandi_modal_price_inr_per_quintal",
}
_STRING_COLUMNS = {"plantix_diagnosis_class", "notes"}
_MISSING_TOKENS = {"", "nan", "n/a", "na", "--"}


def _maybe_float(value: str) -> float | None:
    text = (value or "").strip()
    if not text or text.lower() in _MISSING_TOKENS:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _maybe_string(value: str) -> str | None:
    text = (value or "").strip()
    if not text or text.lower() in _MISSING_TOKENS:
        return None
    return text


def _parse_iso8601(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


class CSVFallbackConnector(Connector):
    """Universal CSV-uploaded BlockObservation feed."""

    source: ClassVar[ConnectorSource] = ConnectorSource.CSV_FALLBACK
    name: ClassVar[str] = "csv_fallback"

    def __init__(
        self,
        ctx: ConnectorContext,
        *,
        fixture_path: str | Path | None = None,
        upload_dir: str | Path | None = None,
    ) -> None:
        super().__init__(ctx)
        self._fixture_path = Path(fixture_path) if fixture_path else None
        self._upload_dir = Path(upload_dir) if upload_dir else None

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        if self._fixture_path is not None and self._fixture_path.exists():
            yield from self._parse_csv(self._fixture_path, since=since, until=until)
            return

        target_dir = self._upload_dir
        if target_dir is None:
            secret_dir = self.ctx.secrets.get("CSV_FALLBACK_UPLOAD_DIR")
            target_dir = Path(secret_dir) if secret_dir else None

        if target_dir is None or not target_dir.exists():
            logger.warning(
                "CSVFallbackConnector: no fixture_path/upload_dir; set "
                "CSV_FALLBACK_UPLOAD_DIR or pass upload_dir=. Returning empty."
            )
            return

        csv_files = sorted(target_dir.glob("*.csv"))
        if not csv_files:
            logger.warning("CSVFallbackConnector: no .csv files in %s", target_dir)
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
                    "CSVFallbackConnector: %s missing required columns %s; skipping",
                    path,
                    sorted(missing),
                )
                return
            for row_num, row in enumerate(reader, start=2):
                obs = self._row_to_observation(row, path=path, row_num=row_num)
                if obs is None:
                    continue
                if since <= obs.ts < until:
                    yield obs

    @staticmethod
    def _row_to_observation(row: dict, *, path: Path, row_num: int) -> BlockObservation | None:
        block_id = (row.get("block_id") or "").strip()
        ts = _parse_iso8601(row.get("ts_iso", ""))
        source_str = (row.get("source") or "").strip().lower()
        if not block_id or ts is None or source_str != "csv_fallback":
            logger.warning(
                "CSVFallback: %s row %d has bad required field "
                "(block_id=%r, ts_iso=%r, source=%r); skipping",
                path.name,
                row_num,
                block_id,
                row.get("ts_iso"),
                row.get("source"),
            )
            return None

        kwargs: dict[str, Any] = {
            "block_id": block_id,
            "ts": ts,
            "source": ConnectorSource.CSV_FALLBACK,
        }
        for col in _FLOAT_COLUMNS:
            value = _maybe_float(row.get(col, ""))
            if value is not None:
                kwargs[col] = value
        for col in _STRING_COLUMNS:
            value = _maybe_string(row.get(col, ""))
            if value is not None:
                kwargs[col] = value

        try:
            return BlockObservation(**kwargs)
        except ValidationError as e:
            logger.warning(
                "CSVFallback: %s row %d failed schema validation: %s",
                path.name,
                row_num,
                e,
            )
            return None
