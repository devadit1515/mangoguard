"""Maharashtra CROPSAP taluka pest-surveillance connector.

CROPSAP (Crop Pest Surveillance and Advisory Project) is the Maharashtra
state government's pest-incidence monitoring program. The public HTML
dashboard at ``cropsap.maharashtra.gov.in`` publishes taluka-level
infestation percentages for the four mango pathogens that drive the
Konkan Alphonso spray-decision tree:

- **Anthracnose** (fungal, drives PHI-aware spray choices)
- **Powdery mildew** (fungal, drives sulfur-based dust decisions)
- **Hopper** (insect, drives imidacloprid-class scheduling)
- **Thrips** (insect, drives spinosad/imidacloprid scheduling)

CROPSAP is the regional-pressure multiplier that Plan 4's disease-risk
engine uses: local microclimate signals (IMD/DBSKKV) say *whether*
infection conditions exist; CROPSAP says *how much* of the surrounding
taluka is already infected, which raises the effective risk via
spore-load / vector-population coupling.

One BlockObservation per (taluka, pathogen) row. ``block_id`` = taluka
lowercased + pathogen suffix (so 4 same-taluka-same-day rows do not
collide on the natural key). ``cropsap_pest_pressure`` = infestation
percent. ``notes`` preserves pathogen identity + severity as JSON so
Plan 4's recommender can filter to the relevant pathway.

The CROPSAP HTML is fragile (state-government IT teams rebrand
periodically). Uses the same primary-selector + fallback-class +
header-text-heuristic chain as the DBSKKV connector.
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

_CROPSAP_URL = "https://cropsap.maharashtra.gov.in/"
_IST = ZoneInfo("Asia/Kolkata")
_MISSING_TOKENS = {"", "--", "N/A", "NA", "n/a", "Not Reported"}
_HTTP_OK = 200

# Canonical pathogen slugs used in notes JSON. Matches Plan 4's expected keys.
_PATHOGEN_SLUGS = {
    "anthracnose": "anthracnose",
    "powdery mildew": "powdery_mildew",
    "powdery_mildew": "powdery_mildew",
    "hopper": "hopper",
    "mango hopper": "hopper",
    "thrips": "thrips",
}

_TABLE_SELECTORS = (
    {"name": "table", "attrs": {"class": "pest-incidence-table"}},
    {"name": "table", "attrs": {"class": lambda c: c and "incidence" in c.lower()}},
    {"name": "table", "attrs": {"class": lambda c: c and "pest" in c.lower()}},
)


class CROPSAPConnector(Connector):
    """Taluka-level pest-incidence feed from Maharashtra CROPSAP."""

    source: ClassVar[ConnectorSource] = ConnectorSource.CROPSAP
    name: ClassVar[str] = "cropsap"

    def __init__(
        self,
        ctx: ConnectorContext,
        *,
        fixture_path: str | Path | None = None,
        http_get: Callable | None = None,
    ) -> None:
        super().__init__(ctx)
        self._fixture_path = Path(fixture_path) if fixture_path else None
        self._http_get = http_get if http_get is not None else get_with_retry

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        if self._fixture_path is not None and self._fixture_path.exists():
            yield from self.parse_html_fixture(self._fixture_path, since=since, until=until)
            return
        try:
            response = self._http_get(_CROPSAP_URL)
        except Exception as e:
            logger.warning("CROPSAP: live fetch failed (%s); returning empty", e)
            return
        if response.status_code != _HTTP_OK:
            logger.warning(
                "CROPSAP: live page returned %d; returning empty",
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
        """Parse a saved CROPSAP dashboard HTML snapshot."""
        html = Path(path).read_text(encoding="utf-8")
        yield from self._parse_html(html, since=since, until=until)

    def _parse_html(
        self, html: str, *, since: datetime, until: datetime
    ) -> Iterable[BlockObservation]:
        soup = BeautifulSoup(html, "html.parser")
        table = self._find_incidence_table(soup)
        if table is None:
            logger.warning(
                "CROPSAP: incidence table not found via any selector; " "layout may have changed"
            )
            return
        for row in self._extract_rows(table):
            obs = self._row_to_observation(row)
            if obs is None:
                continue
            if since <= obs.ts < until:
                yield obs

    @staticmethod
    def _find_incidence_table(soup):
        for selector in _TABLE_SELECTORS:
            table = soup.find(selector["name"], attrs=selector["attrs"])
            if table is not None:
                return table
        # Last-resort fallback: any table whose header mentions Taluka + Pathogen.
        for table in soup.find_all("table"):
            header_text = " ".join(th.get_text(strip=True).lower() for th in table.find_all("th"))
            if "taluka" in header_text and ("pathogen" in header_text or "pest" in header_text):
                return table
        return None

    @staticmethod
    def _extract_rows(table) -> list[dict[str, str]]:
        keys = ["taluka", "pathogen", "infestation_pct", "report_date", "severity"]
        out: list[dict[str, str]] = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) < len(keys):
                continue
            out.append(dict(zip(keys, cells, strict=False)))
        return out

    def _row_to_observation(self, row: dict[str, str]) -> BlockObservation | None:
        taluka = (row.get("taluka") or "").strip().lower()
        if not taluka:
            logger.warning("CROPSAP: dropping row with empty taluka: %r", row)
            return None

        pathogen_raw = (row.get("pathogen") or "").strip().lower()
        pathogen_slug = _PATHOGEN_SLUGS.get(pathogen_raw)
        if pathogen_slug is None:
            logger.warning(
                "CROPSAP: unrecognized pathogen %r at %s; dropping",
                row.get("pathogen"),
                taluka,
            )
            return None

        try:
            ts = datetime.strptime((row.get("report_date") or "").strip(), "%Y-%m-%d").replace(
                tzinfo=_IST
            )
        except ValueError as e:
            logger.warning(
                "CROPSAP: dropping row with bad date %r at %s/%s: %s",
                row.get("report_date"),
                taluka,
                pathogen_slug,
                e,
            )
            return None

        infestation_raw = (row.get("infestation_pct") or "").strip()
        if infestation_raw in _MISSING_TOKENS:
            pressure: float | None = None
        else:
            try:
                pressure = float(infestation_raw)
            except ValueError:
                logger.warning(
                    "CROPSAP: dropping row with bad infestation_pct %r at %s/%s",
                    infestation_raw,
                    taluka,
                    pathogen_slug,
                )
                return None
            if pressure < 0:
                logger.warning(
                    "CROPSAP: negative infestation_pct %r at %s/%s; dropping",
                    pressure,
                    taluka,
                    pathogen_slug,
                )
                return None

        # Collision suffix: 4 pathogens per taluka would otherwise share the
        # same (block_id, ts, source) natural key. Suffix pathogen to block_id
        # so all 4 land as distinct rows.
        block_id = f"{taluka}_{pathogen_slug}"[:32]
        notes_payload = {
            "taluka": taluka,
            "pathogen": pathogen_slug,
            "severity": (row.get("severity") or "").strip(),
        }
        return BlockObservation(
            block_id=block_id,
            ts=ts,
            source=ConnectorSource.CROPSAP,
            cropsap_pest_pressure=pressure,
            notes=json.dumps(notes_payload)[:512],
        )
