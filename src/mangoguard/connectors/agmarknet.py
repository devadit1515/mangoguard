"""AGMARKNET mandi-price connector for mango (Maharashtra).

Uses data.gov.in's Open Government Data API. Free with an API key from
data.gov.in. Each ``BlockObservation`` represents one (market, date, variety,
grade) mandi entry; the ``mandi_modal_price_inr_per_quintal`` field holds
the modal price in INR per quintal.

Multi-variety same-day collision handling: if the same (market, date) has
more than one record, the second-and-onward rows get ``_<variety>`` suffixed
to ``block_id`` to preserve the natural-key uniqueness contract.

The fetcher accepts an injected ``http_get`` callable (default
``get_with_retry``) so tests can pass a fake without going through the
``responses`` mock machinery.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import ClassVar
from zoneinfo import ZoneInfo

from mangoguard.connectors._http import get_with_retry
from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.schema import BlockObservation, ConnectorSource

logger = logging.getLogger(__name__)

_AGMARKNET_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
_IST = ZoneInfo("Asia/Kolkata")


class AGMARKNETConnector(Connector):
    """Mango mandi-price feed from data.gov.in AGMARKNET dataset."""

    source: ClassVar[ConnectorSource] = ConnectorSource.AGMARKNET
    name: ClassVar[str] = "agmarknet"

    def __init__(
        self,
        ctx: ConnectorContext,
        *,
        state: str = "Maharashtra",
        commodity: str = "Mango",
        http_get: Callable | None = None,
    ) -> None:
        super().__init__(ctx)
        self._state = state
        self._commodity = commodity
        self._http_get = http_get if http_get is not None else get_with_retry

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        api_key = self.ctx.secrets.get("DATA_GOV_IN_KEY", "")
        if not api_key:
            logger.warning(
                "AGMARKNETConnector: DATA_GOV_IN_KEY missing from ctx.secrets; "
                "fetch() will return empty. Set the key or use a fixture path."
            )
            return

        params = {
            "api-key": api_key,
            "format": "json",
            "filters[commodity]": self._commodity,
            "filters[state.keyword]": self._state,
            "limit": 1000,
            "offset": 0,
        }
        response = self._http_get(_AGMARKNET_URL, params=params)
        response.raise_for_status()
        payload = response.json()
        yield from self._parse_records(payload.get("records", []), since=since, until=until)

    def parse_fixture(
        self,
        fixture_path: str,
        *,
        since: datetime,
        until: datetime,
    ) -> list[BlockObservation]:
        """Parse a saved JSON fixture (same shape as the live API response).

        Used by tests and the offline-demo path so we can develop without
        burning the live key.
        """
        with open(fixture_path, encoding="utf-8") as f:
            payload = json.load(f)
        return list(self._parse_records(payload.get("records", []), since=since, until=until))

    def _parse_records(
        self,
        records: list[dict],
        *,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        # First pass: group by (market_lower, ts) to detect collisions.
        bucketed: dict[tuple[str, datetime], list[dict]] = defaultdict(list)
        for rec in records:
            parsed = self._parse_one(rec)
            if parsed is None:
                continue
            key = (parsed["block_id"], parsed["ts"])
            bucketed[key].append(parsed)

        for (market, ts), rows in bucketed.items():
            if not (since <= ts < until):
                continue
            if len(rows) == 1:
                row = rows[0]
                yield BlockObservation(
                    block_id=market,
                    ts=ts,
                    source=ConnectorSource.AGMARKNET,
                    mandi_modal_price_inr_per_quintal=row["modal_price"],
                    notes=row["notes"],
                )
            else:
                for row in rows:
                    suffixed = f"{market}_{row['variety_slug']}"[:32]
                    yield BlockObservation(
                        block_id=suffixed,
                        ts=ts,
                        source=ConnectorSource.AGMARKNET,
                        mandi_modal_price_inr_per_quintal=row["modal_price"],
                        notes=row["notes"],
                    )

    @staticmethod
    def _parse_one(rec: dict) -> dict | None:
        market = (rec.get("market") or "").strip().lower()
        if not market:
            logger.warning("AGMARKNET: dropping record with empty market: %r", rec)
            return None
        try:
            ts = datetime.strptime(rec["arrival_date"], "%d/%m/%Y").replace(tzinfo=_IST)
        except (KeyError, ValueError) as e:
            logger.warning(
                "AGMARKNET: dropping record with bad arrival_date %r: %s",
                rec.get("arrival_date"),
                e,
            )
            return None
        try:
            modal_price = float(rec.get("modal_price", "") or "")
        except (TypeError, ValueError):
            logger.warning(
                "AGMARKNET: dropping record with non-numeric modal_price %r at %s/%s",
                rec.get("modal_price"),
                market,
                rec.get("arrival_date"),
            )
            return None
        variety = (rec.get("variety") or "").strip()
        grade = (rec.get("grade") or "").strip()
        notes = json.dumps({"variety": variety, "grade": grade})[:512]
        variety_slug = variety.lower().replace(" ", "-").replace("/", "-") if variety else "unknown"
        return {
            "block_id": market[:32],
            "ts": ts,
            "modal_price": modal_price,
            "notes": notes,
            "variety_slug": variety_slug,
        }
