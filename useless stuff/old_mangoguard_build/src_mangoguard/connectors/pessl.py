"""Pessl iMETOS / FieldClimate REST connector.

The only Indian agri-sensor vendor with a documented public REST API.
HMAC-signed requests at ``https://api.fieldclimate.com/v2/``. Common on
rich export-grade Konkan Alphonso farms.

API response shape (worked from ``/v2/docs/``):

    {
      "dates": ["YYYY-MM-DD HH:MM:SS", ...],          # station-local
      "data": [
        {
          "name": "HC Air temperature",
          "unit": "C",
          "values": {"avg": [...], "min": [...], "max": [...]}
        },
        ...
      ]
    }

We pivot this column-major payload into one ``BlockObservation`` per
timestamp by joining all sensors at the same index. Sensor selection
priority for each ``BlockObservation`` field:

- ``t_air_c``                 <- "HC Air temperature" .values.avg
- ``rh_pct``                  <- "HC Air humidity" .values.avg
- ``leaf_wetness_hr``         <- "Leaf Wetness" .values.sum (minutes) / 60
- ``precip_mm``               <- "Precipitation" .values.sum
- ``wind_speed_ms``           <- "Wind speed" .values.avg
- ``solar_w_m2``              <- "Solar radiation" .values.avg
- ``soil_moisture_pct``       <- first sensor whose name starts with
                                  "Soil moisture VWC" .values.avg

A station that omits a sensor (e.g., no soil probe) yields rows where
that field is None -- never zero, since 0% soil moisture is a real and
distinct reading.

Tests work fully offline via ``parse_fixture``. Live integration is
gated on ``PESSL_PUBLIC_KEY`` + ``PESSL_PRIVATE_KEY`` in
``ctx.secrets``.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar

from mangoguard.connectors._auth import sign_pessl_request
from mangoguard.connectors._http import get_with_retry
from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.schema import BlockObservation, ConnectorSource

logger = logging.getLogger(__name__)

_PESSL_BASE = "https://api.fieldclimate.com/v2"
_HTTP_OK = 200


def _identity(v):
    return v


def _minutes_to_hours(v):
    return v / 60.0 if v is not None else None


# Sensor-name -> (obs_field, values_subkey, transform).
_SENSOR_MAP: tuple[tuple[str, str, str, Callable[[float | None], float | None]], ...] = (
    ("HC Air temperature", "t_air_c", "avg", _identity),
    ("HC Air humidity", "rh_pct", "avg", _identity),
    ("Leaf Wetness", "leaf_wetness_hr", "sum", _minutes_to_hours),
    ("Precipitation", "precip_mm", "sum", _identity),
    ("Wind speed", "wind_speed_ms", "avg", _identity),
    ("Solar radiation", "solar_w_m2", "avg", _identity),
)


class PesslConnector(Connector):
    """Pessl iMETOS feed via FieldClimate v2 REST."""

    source: ClassVar[ConnectorSource] = ConnectorSource.PESSL
    name: ClassVar[str] = "pessl"

    def __init__(
        self,
        ctx: ConnectorContext,
        *,
        station_id: str = "",
        fixture_path: str | Path | None = None,
        http_get: Callable | None = None,
    ) -> None:
        super().__init__(ctx)
        self._station_id = station_id.strip()
        self._fixture_path = Path(fixture_path) if fixture_path else None
        self._http_get = http_get if http_get is not None else get_with_retry

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        if self._fixture_path is not None and self._fixture_path.exists():
            yield from self.parse_fixture(self._fixture_path, since=since, until=until)
            return

        pub = self.ctx.secrets.get("PESSL_PUBLIC_KEY", "")
        priv = self.ctx.secrets.get("PESSL_PRIVATE_KEY", "")
        if not pub or not priv:
            logger.warning(
                "PesslConnector: PESSL_PUBLIC_KEY/PRIVATE_KEY missing from "
                "ctx.secrets; returning empty"
            )
            return
        if not self._station_id:
            logger.warning("PesslConnector: no station_id configured; returning empty")
            return

        since_iso = since.strftime("%Y-%m-%d")
        until_iso = until.strftime("%Y-%m-%d")
        path = f"/data/{self._station_id}/raw/from/{since_iso}/to/{until_iso}"
        headers = sign_pessl_request("GET", path, pub, priv)
        try:
            response = self._http_get(f"{_PESSL_BASE}{path}", headers=headers)
        except Exception as e:
            logger.warning("Pessl: live fetch failed (%s); returning empty", e)
            return
        if response.status_code != _HTTP_OK:
            logger.warning("Pessl: API returned %d; returning empty", response.status_code)
            return
        payload = response.json()
        yield from self._parse_payload(payload, since=since, until=until)

    def parse_fixture(
        self,
        path: str | Path,
        *,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        """Parse a saved FieldClimate JSON response (offline)."""
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        yield from self._parse_payload(payload, since=since, until=until)

    def _parse_payload(
        self,
        payload: dict,
        *,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        dates = payload.get("dates") or []
        sensors_by_name: dict[str, dict] = {
            sensor.get("name", ""): sensor for sensor in (payload.get("data") or [])
        }
        soil_sensor = next(
            (
                sensor
                for sensor in (payload.get("data") or [])
                if sensor.get("name", "").startswith("Soil moisture VWC")
            ),
            None,
        )
        block_id = (self._station_id or "pessl_fixture").lower()[:32]

        for i, date_str in enumerate(dates):
            try:
                ts = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except (TypeError, ValueError) as e:
                logger.warning("Pessl: dropping row with bad date %r: %s", date_str, e)
                continue
            if not (since <= ts < until):
                continue

            fields: dict[str, float | None] = {}
            for sensor_name, obs_field, values_key, transform in _SENSOR_MAP:
                sensor = sensors_by_name.get(sensor_name)
                fields[obs_field] = _extract_at(sensor, values_key, i, transform)

            if soil_sensor is not None:
                fields["soil_moisture_pct"] = _extract_at(soil_sensor, "avg", i, _identity)

            yield BlockObservation(
                block_id=block_id,
                ts=ts,
                source=ConnectorSource.PESSL,
                **fields,
            )


def _extract_at(
    sensor: dict | None,
    key: str,
    index: int,
    transform: Callable[[float | None], float | None],
) -> float | None:
    """Pull ``sensor.values[key][index]`` if it exists; return None otherwise."""
    if sensor is None:
        return None
    values = sensor.get("values") or {}
    series = values.get(key)
    if not isinstance(series, list) or index >= len(series):
        return None
    raw = series[index]
    if raw is None:
        return None
    try:
        return transform(float(raw))
    except (TypeError, ValueError):
        return None
