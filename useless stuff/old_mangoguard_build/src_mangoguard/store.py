"""SQLite-backed FeedStore repository.

Natural key: `(block_id, ts, source)`. Re-inserting the same key updates the row
(`INSERT OR REPLACE`), so connectors can re-run on a window idempotently.

Stored timestamps are ISO 8601 strings of the original tz-aware datetime; query
bounds are normalized to UTC before lexicographic comparison so callers may
safely pass any tz-aware datetime without producing wrong-result bugs from
mixed-zone strings.

The connection is opened with sqlite3's default `check_same_thread=True`. Do
not share a single FeedStore across threads — create one per worker.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone

from mangoguard.schema import BlockObservation, ConnectorSource

_SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    block_id        TEXT NOT NULL,
    ts              TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN (
        'fyllo','fasal','pessl','imd','plantix',
        'agmarknet','dbskkv','cropsap','sentinel2','csv_fallback'
    )),
    t_air_c         REAL,
    rh_pct          REAL,
    leaf_wetness_hr REAL,
    precip_mm       REAL,
    wind_speed_ms   REAL,
    solar_w_m2      REAL,
    soil_moisture_pct REAL,
    ndvi            REAL,
    ndre            REAL,
    ndmi            REAL,
    plantix_diagnosis_class TEXT,
    cropsap_pest_pressure REAL,
    mandi_modal_price_inr_per_quintal REAL,
    notes           TEXT,
    ingested_at     TEXT,
    connector_run_id TEXT,
    quality_flag    TEXT,
    PRIMARY KEY (block_id, ts, source)
);

CREATE INDEX IF NOT EXISTS idx_obs_block_ts ON observations (block_id, ts);
CREATE INDEX IF NOT EXISTS idx_obs_source   ON observations (source);
"""

_COLUMNS = (
    "block_id",
    "ts",
    "source",
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
    "plantix_diagnosis_class",
    "cropsap_pest_pressure",
    "mandi_modal_price_inr_per_quintal",
    "notes",
    "ingested_at",
    "connector_run_id",
    "quality_flag",
)


class FeedStore:
    def __init__(self, path: str = "feeds.db") -> None:
        self._conn = sqlite3.connect(
            path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            isolation_level=None,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) AS n FROM observations")
        return cur.fetchone()["n"]

    def insert(self, obs: BlockObservation) -> None:
        self.insert_many([obs])

    def insert_many(self, observations: Iterable[BlockObservation]) -> None:
        rows = [self._obs_to_row(o) for o in observations]
        if not rows:
            return
        placeholders = ", ".join(["?"] * len(_COLUMNS))
        sql = f"INSERT OR REPLACE INTO observations ({', '.join(_COLUMNS)}) VALUES ({placeholders})"
        self._conn.executemany(sql, rows)

    def query(
        self,
        block_id: str,
        ts_start: datetime,
        ts_end: datetime,
    ) -> list[BlockObservation]:
        """Return observations for ``block_id`` in the half-open window ``[ts_start, ts_end)``.

        Both bounds are normalized to UTC before string comparison, so naive
        tz-aware inputs in any zone produce the same result. Rows are returned
        ordered by ``ts ASC, source ASC`` for deterministic downstream behavior.
        """
        # Normalize query bounds to UTC so lexicographic ISO comparison matches
        # chronological order regardless of caller's input timezone.
        start_utc = ts_start.astimezone(timezone.utc).isoformat()
        end_utc = ts_end.astimezone(timezone.utc).isoformat()
        cur = self._conn.execute(
            "SELECT * FROM observations "
            "WHERE block_id = ? AND ts >= ? AND ts < ? "
            "ORDER BY ts ASC, source ASC",
            (block_id, start_utc, end_utc),
        )
        return [self._row_to_obs(r) for r in cur.fetchall()]

    def query_by_source(self, source: ConnectorSource) -> list[BlockObservation]:
        cur = self._conn.execute(
            "SELECT * FROM observations WHERE source = ? ORDER BY ts ASC, block_id ASC",
            (source.value,),
        )
        return [self._row_to_obs(r) for r in cur.fetchall()]

    def count_by_source(self) -> dict[ConnectorSource, int]:
        """Return ``{source: row_count}`` across all observations."""
        cur = self._conn.execute("SELECT source, COUNT(*) AS n FROM observations GROUP BY source")
        return {ConnectorSource(row["source"]): row["n"] for row in cur.fetchall()}

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Context manager wrapping a single SQLite transaction.

        Yields, then commits on success or rolls back on any exception. Useful
        for grouping a multi-batch ``Connector.run`` write so a half-failed
        pull does not leave partial state visible.
        """
        self._conn.execute("BEGIN")
        try:
            yield
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        else:
            self._conn.execute("COMMIT")

    @staticmethod
    def _obs_to_row(o: BlockObservation) -> tuple:
        return (
            o.block_id,
            o.ts.isoformat(),
            o.source.value,
            o.t_air_c,
            o.rh_pct,
            o.leaf_wetness_hr,
            o.precip_mm,
            o.wind_speed_ms,
            o.solar_w_m2,
            o.soil_moisture_pct,
            o.ndvi,
            o.ndre,
            o.ndmi,
            o.plantix_diagnosis_class,
            o.cropsap_pest_pressure,
            o.mandi_modal_price_inr_per_quintal,
            o.notes,
            o.ingested_at.isoformat() if o.ingested_at is not None else None,
            o.connector_run_id,
            o.quality_flag,
        )

    @staticmethod
    def _row_to_obs(r: sqlite3.Row) -> BlockObservation:
        ingested_at_raw = r["ingested_at"]
        return BlockObservation(
            block_id=r["block_id"],
            ts=datetime.fromisoformat(r["ts"]),
            source=ConnectorSource(r["source"]),
            t_air_c=r["t_air_c"],
            rh_pct=r["rh_pct"],
            leaf_wetness_hr=r["leaf_wetness_hr"],
            precip_mm=r["precip_mm"],
            wind_speed_ms=r["wind_speed_ms"],
            solar_w_m2=r["solar_w_m2"],
            soil_moisture_pct=r["soil_moisture_pct"],
            ndvi=r["ndvi"],
            ndre=r["ndre"],
            ndmi=r["ndmi"],
            plantix_diagnosis_class=r["plantix_diagnosis_class"],
            cropsap_pest_pressure=r["cropsap_pest_pressure"],
            mandi_modal_price_inr_per_quintal=r["mandi_modal_price_inr_per_quintal"],
            notes=r["notes"],
            ingested_at=datetime.fromisoformat(ingested_at_raw) if ingested_at_raw else None,
            connector_run_id=r["connector_run_id"],
            quality_flag=r["quality_flag"],
        )
