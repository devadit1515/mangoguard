"""DBSKKV Dapoli Konkan microclimate forecast connector.

Dr. Balasaheb Sawant Konkan Krishi Vidyapeeth Dapoli is the regional
agricultural university for the Konkan coast (Maharashtra). Its weather-
forecast page publishes a 5-day forecast calibrated specifically for
Konkan microclimate -- distinct from IMD's broader district-level forecast
because Konkan has unique orographic monsoon dynamics (Western Ghats
lift, 3000+ mm rainfall, 90%+ June-September cloud cover).

DBSKKV is the only Konkan-domain-authority signal in the free-public
baseline stack. Plan 4's disease-risk engine will weight DBSKKV higher
than IMD for Konkan-specific anthracnose/powdery-mildew forecasting
precisely because of this calibration.

The university website's HTML structure is fragile (university IT teams
re-skin pages periodically). Selectors are documented constants below;
the parser uses a primary-selector + fallback chain so a single class
rename does not break the connector entirely.

Missing/non-numeric cells (empty <td>, '--', 'N/A') are treated as None
on that field, not dropped from the row. A forecast row with only date
+ Tmax + Tmin still yields a BlockObservation.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from mangoguard.connectors._http import get_with_retry
from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.schema import BlockObservation, ConnectorSource

logger = logging.getLogger(__name__)

_DBSKKV_FORECAST_URL = "https://www.dbskkv.org/farmers-corner/weather-forecast"
_IST = ZoneInfo("Asia/Kolkata")
_KMH_TO_MS = 1.0 / 3.6
_MISSING_TOKENS = {"", "--", "N/A", "NA", "n/a"}
_HTTP_OK = 200

# Selector chain: try class first, fall back to header-text heuristic.
_TABLE_SELECTORS = (
    {"name": "table", "attrs": {"class": "weather-forecast-table"}},
    {"name": "table", "attrs": {"class": lambda c: c and "forecast" in c.lower()}},
    {"name": "table", "attrs": {"class": lambda c: c and "weather" in c.lower()}},
)


class DBSKKVConnector(Connector):
    """Konkan microclimate forecast feed from DBSKKV Dapoli."""

    source: ClassVar[ConnectorSource] = ConnectorSource.DBSKKV
    name: ClassVar[str] = "dbskkv"

    def __init__(
        self,
        ctx: ConnectorContext,
        *,
        station: str = "dapoli",
        fixture_path: str | Path | None = None,
        http_get: Callable | None = None,
    ) -> None:
        super().__init__(ctx)
        self._station = station.strip().lower()[:32]
        self._fixture_path = Path(fixture_path) if fixture_path else None
        self._http_get = http_get if http_get is not None else get_with_retry

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        if self._fixture_path is not None and self._fixture_path.exists():
            yield from self.parse_html_fixture(self._fixture_path, since=since, until=until)
            return
        try:
            response = self._http_get(_DBSKKV_FORECAST_URL)
        except Exception as e:
            logger.warning("DBSKKV: live fetch failed (%s); returning empty", e)
            return
        if response.status_code != _HTTP_OK:
            logger.warning(
                "DBSKKV: live page returned %d; returning empty",
                response.status_code,
            )
            return
        yield from self._parse_html(response.text, since=since, until=until)

    def parse_html_fixture(
        self,
        path: str | Path,
        *,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        """Parse a saved DBSKKV forecast HTML snapshot."""
        html = Path(path).read_text(encoding="utf-8")
        yield from self._parse_html(html, since=since, until=until)

    def _parse_html(
        self, html: str, *, since: datetime, until: datetime
    ) -> Iterable[BlockObservation]:
        soup = BeautifulSoup(html, "html.parser")
        table = self._find_forecast_table(soup)
        if table is None:
            logger.warning(
                "DBSKKV: forecast table not found via any selector; " "layout may have changed"
            )
            return
        for row in self._extract_rows(table):
            obs = self._row_to_observation(row)
            if obs is None:
                continue
            if since <= obs.ts < until:
                yield obs

    @staticmethod
    def _find_forecast_table(soup):
        for selector in _TABLE_SELECTORS:
            table = soup.find(selector["name"], attrs=selector["attrs"])
            if table is not None:
                return table
        # Last-resort fallback: any table whose header row mentions Tmax + Rain.
        for table in soup.find_all("table"):
            header_text = " ".join(th.get_text(strip=True).lower() for th in table.find_all("th"))
            if "tmax" in header_text and "rain" in header_text:
                return table
        return None

    @staticmethod
    def _extract_rows(table) -> list[dict[str, str]]:
        keys = ["date", "tmax", "tmin", "rh", "rainfall", "wind_kmh"]
        out: list[dict[str, str]] = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) < len(keys):
                continue
            out.append(dict(zip(keys, cells, strict=False)))
        return out

    def _row_to_observation(self, row: dict[str, str]) -> BlockObservation | None:
        try:
            ts = datetime.strptime(row["date"].strip(), "%Y-%m-%d").replace(tzinfo=_IST)
        except (KeyError, ValueError) as e:
            logger.warning("DBSKKV: dropping row with bad date %r: %s", row.get("date"), e)
            return None

        tmax = _maybe_float(row.get("tmax"))
        tmin = _maybe_float(row.get("tmin"))
        rh = _maybe_float(row.get("rh"))
        rainfall = _maybe_float(row.get("rainfall"))
        wind_kmh = _maybe_float(row.get("wind_kmh"))

        t_air_c = (tmax + tmin) / 2.0 if (tmax is not None and tmin is not None) else None
        wind_ms = wind_kmh * _KMH_TO_MS if wind_kmh is not None else None

        notes_payload = {
            "tmax_c": tmax,
            "tmin_c": tmin,
            "rh_pct": rh,
            "wind_kmh": wind_kmh,
            "source_url": _DBSKKV_FORECAST_URL,
        }
        return BlockObservation(
            block_id=self._station,
            ts=ts,
            source=ConnectorSource.DBSKKV,
            t_air_c=t_air_c,
            rh_pct=rh,
            precip_mm=rainfall,
            wind_speed_ms=wind_ms,
            notes=json.dumps(notes_payload)[:512],
        )


def _maybe_float(value: str | None) -> float | None:
    """Parse a cell to float, returning None for missing/non-numeric tokens."""
    if value is None:
        return None
    stripped = value.strip()
    if stripped in _MISSING_TOKENS:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None
