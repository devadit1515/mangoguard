"""IMD (India Meteorological Department) Mausam + Meghdoot agromet connector.

Konkan Alphonso growers depend on twice-weekly AMFU (Agromet Field Unit)
bulletins published as district-level PDFs at
``mausam.imd.gov.in/imd_latest/contents/agromet/``. Each bulletin contains
a 5-day forecast table that this connector parses into per-block per-day
``BlockObservation`` records.

Two ingestion paths:

1. **HTML/PDF table parse** (offline-capable, default). Tests use a hand-
   authored HTML fixture that mimics the PDF's table representation.
   Production code accepts either HTML (via BeautifulSoup) or PDF (via
   ``pdfplumber.extract_table``) and normalizes both to a common
   list-of-rows intermediate before mapping to BlockObservation.
2. **JSON nowcast API** at ``api.imd.gov.in/public/get_district_nowcast.php``
   -- IP-whitelist gated. Stubbed; returns empty until ``IMD_API_KEY`` is
   provisioned via ``secrets["IMD_API_KEY"]``.

Daily mean fields (``t_air_c``, ``rh_pct``) are computed as agromet-standard
averages of the forecast's Tmax/Tmin and RH morning/evening pairs. Raw
quartet values are preserved in ``notes`` for downstream consumers that
want max-only or min-only signals.
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

_IMD_NOWCAST_URL = "https://api.imd.gov.in/public/get_district_nowcast.php"
_IST = ZoneInfo("Asia/Kolkata")
_KMH_TO_MS = 1.0 / 3.6
# Forecast table layout: header row + at least one data row.
_MIN_TABLE_ROWS = 2
# Columns: Date, Tmax, Tmin, RH-morn, RH-eve, Rainfall, Wind.
_EXPECTED_COLS = 7


class IMDConnector(Connector):
    """IMD Mausam + Meghdoot agromet forecast feed for Konkan AMFUs."""

    source: ClassVar[ConnectorSource] = ConnectorSource.IMD
    name: ClassVar[str] = "imd"

    def __init__(
        self,
        ctx: ConnectorContext,
        *,
        district: str = "Ratnagiri",
        fixture_path: str | Path | None = None,
        http_get: Callable | None = None,
    ) -> None:
        super().__init__(ctx)
        self._district = district
        self._fixture_path = Path(fixture_path) if fixture_path else None
        self._http_get = http_get if http_get is not None else get_with_retry

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        if self._fixture_path is not None and self._fixture_path.exists():
            yield from self.parse_html_fixture(self._fixture_path, since=since, until=until)
            return

        api_key = self.ctx.secrets.get("IMD_API_KEY", "")
        if not api_key:
            logger.warning(
                "IMDConnector: no fixture_path and IMD_API_KEY missing; "
                "fetch() returning empty. Provide a fixture or request API "
                "whitelisting at sankar.nath@imd.gov.in."
            )
            return
        logger.info(
            "IMDConnector: live JSON nowcast API path not yet implemented; "
            "returning empty until IP-whitelist provisioning completes."
        )
        # Future: hit _IMD_NOWCAST_URL with the api_key + district.

    def parse_html_fixture(
        self,
        path: str | Path,
        *,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        """Parse an AMFU bulletin's 5-day forecast HTML table.

        The fixture intentionally mirrors the structure ``pdfplumber``
        produces from the real IMD PDF: a ``<table>`` with header row
        Date / Tmax / Tmin / RH-morn / RH-eve / Rain / Wind.
        """
        soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
        table = soup.find("table", id="five-day-forecast") or soup.find("table")
        if table is None:
            logger.warning("IMD: no <table> found in %s", path)
            return
        rows = self._extract_rows(table)
        yield from self._rows_to_observations(rows, since=since, until=until)

    def parse_pdf(
        self,
        path: str | Path,
        *,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        """Parse an AMFU bulletin PDF using pdfplumber.

        Defensive lazy import: ``pdfplumber`` is in the ``scrape`` optional
        dependency group, so importing at module top-level would break
        installs that only need the foundation. Raises ``RuntimeError`` if
        called without the extra installed.
        """
        try:
            import pdfplumber  # noqa: PLC0415 -- lazy import for optional dep
        except ImportError as e:
            msg = "IMDConnector.parse_pdf requires the 'scrape' extra: pip install -e '.[scrape]'"
            raise RuntimeError(msg) from e

        with pdfplumber.open(path) as pdf:
            table = pdf.pages[0].extract_table()
        if not table or len(table) < _MIN_TABLE_ROWS:
            logger.warning("IMD: empty or malformed table in PDF %s", path)
            return
        rows = [
            {
                "date": r[0],
                "tmax": r[1],
                "tmin": r[2],
                "rh_morn": r[3],
                "rh_eve": r[4],
                "rainfall": r[5],
                "wind_kmh": r[6],
            }
            for r in table[1:]
            if r and len(r) >= _EXPECTED_COLS
        ]
        yield from self._rows_to_observations(rows, since=since, until=until)

    @staticmethod
    def _extract_rows(table) -> list[dict[str, str]]:
        keys = ["date", "tmax", "tmin", "rh_morn", "rh_eve", "rainfall", "wind_kmh"]
        out: list[dict[str, str]] = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) < len(keys):
                continue
            out.append(dict(zip(keys, cells, strict=False)))
        return out

    def _rows_to_observations(
        self,
        rows: list[dict[str, str]],
        *,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        block_id = self._district.strip().lower()[:32]
        for row in rows:
            obs = self._row_to_observation(block_id, row)
            if obs is None:
                continue
            if since <= obs.ts < until:
                yield obs

    @staticmethod
    def _row_to_observation(block_id: str, row: dict[str, str]) -> BlockObservation | None:
        try:
            ts = datetime.strptime(row["date"].strip(), "%Y-%m-%d").replace(tzinfo=_IST)
            tmax = float(row["tmax"])
            tmin = float(row["tmin"])
            rh_morn = float(row["rh_morn"])
            rh_eve = float(row["rh_eve"])
            rainfall = float(row["rainfall"])
            wind_kmh = float(row["wind_kmh"])
        except (KeyError, ValueError) as e:
            logger.warning("IMD: dropping malformed forecast row %r: %s", row, e)
            return None

        t_air_c = (tmax + tmin) / 2.0
        rh_pct = (rh_morn + rh_eve) / 2.0
        wind_ms = wind_kmh * _KMH_TO_MS
        notes_payload = {
            "tmax_c": tmax,
            "tmin_c": tmin,
            "rh_morn_pct": rh_morn,
            "rh_eve_pct": rh_eve,
            "wind_kmh": wind_kmh,
        }
        return BlockObservation(
            block_id=block_id,
            ts=ts,
            source=ConnectorSource.IMD,
            t_air_c=t_air_c,
            rh_pct=rh_pct,
            precip_mm=rainfall,
            wind_speed_ms=wind_ms,
            notes=json.dumps(notes_payload)[:512],
        )
