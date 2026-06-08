"""Sentinel-2 NDVI/NDRE/NDMI connector via Google Earth Engine.

Per-block canopy stress signal from Copernicus Sentinel-2 surface
reflectance. One ``BlockObservation`` per (block, image-date) where
the cloud filter admits at least one image inside the block polygon.

**Konkan monsoon problem.** From mid-June through mid-September the
Konkan coast sits under 90-92% optical cloud cover from Western Ghats
orographic lift. Sentinel-2 (optical) is effectively blind during this
window. The connector falls back to **Sentinel-1 SAR** (C-band radar,
VV polarization) which penetrates clouds -- different signal entirely,
so we DO NOT populate NDVI/NDRE/NDMI from SAR. Instead we emit a
BlockObservation with ``quality_flag = "sar_fallback"`` and the mean
VV backscatter (dB) encoded in ``notes`` so Plan 4's risk engine and
Plan 6's dashboard can show "monsoon SAR proxy, optical unavailable".

**Indices** (Copernicus S2_SR_HARMONIZED band names):
- NDVI = (B8 - B4) / (B8 + B4)            -- canopy vigor / leaf area
- NDRE = (B8 - B5) / (B8 + B5)            -- chlorophyll / N status
- NDMI = (B8 - B11) / (B8 + B11)          -- canopy water content

**Auth.** Set ``MANGOGUARD_SKIP_EE=1`` to skip ``ee.Initialize`` (tests
do this and inject a fake ``ee`` module). Otherwise the first ``fetch``
call lazily calls ``ee.Initialize(project=secrets["GEE_PROJECT_ID"])``.
You must run ``earthengine authenticate`` once interactively beforehand.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, ClassVar

from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.geo import Block, block_to_ee_geometry
from mangoguard.schema import BlockObservation, ConnectorSource

logger = logging.getLogger(__name__)

_S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
_S1_COLLECTION = "COPERNICUS/S1_GRD"
_CLOUD_PROP = "CLOUDY_PIXEL_PERCENTAGE"
_DEFAULT_CLOUD_THRESHOLD = 30.0
# SAR fallback triggers when this fraction of S2 candidates are over the
# cloud threshold. 0.8 = 80% of revisits cloud-masked.
_SAR_FALLBACK_RATIO = 0.8


class Sentinel2Connector(Connector):
    """Block-level NDVI/NDRE/NDMI from Sentinel-2 with SAR monsoon fallback."""

    source: ClassVar[ConnectorSource] = ConnectorSource.SENTINEL2
    name: ClassVar[str] = "sentinel2"

    def __init__(
        self,
        ctx: ConnectorContext,
        *,
        blocks: list[Block],
        cloud_threshold_pct: float = _DEFAULT_CLOUD_THRESHOLD,
        ee_module: Any | None = None,
    ) -> None:
        super().__init__(ctx)
        if not blocks:
            msg = "Sentinel2Connector requires at least one Block"
            raise ValueError(msg)
        self._blocks = blocks
        self._cloud_threshold = cloud_threshold_pct
        # ee_module lets tests inject a fake without monkeypatching sys.modules.
        self._ee = ee_module
        self._ee_initialized = ee_module is not None

    def _ensure_ee(self) -> Any:
        """Lazy-init the ``ee`` module. Returns the live module."""
        if self._ee is not None:
            return self._ee
        if os.environ.get("MANGOGUARD_SKIP_EE") == "1":
            msg = (
                "Sentinel2Connector: MANGOGUARD_SKIP_EE=1 and no ee_module "
                "injected; cannot fetch"
            )
            raise RuntimeError(msg)
        try:
            import ee  # noqa: PLC0415 — lazy import for optional dep
        except ImportError as e:
            msg = "Sentinel2Connector requires the 'geo' extra: " "pip install -e '.[geo]'"
            raise RuntimeError(msg) from e
        if not self._ee_initialized:
            project_id = self.ctx.secrets.get("GEE_PROJECT_ID")
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            self._ee_initialized = True
        self._ee = ee
        return ee

    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        ee = self._ensure_ee()
        for block in self._blocks:
            yield from self._fetch_block(ee, block, since, until)

    def _fetch_block(
        self,
        ee: Any,
        block: Block,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        geom = block_to_ee_geometry(block, ee_module=ee)
        date_start = since.strftime("%Y-%m-%d")
        date_end = until.strftime("%Y-%m-%d")

        all_images = (
            ee.ImageCollection(_S2_COLLECTION).filterBounds(geom).filterDate(date_start, date_end)
        )
        clear_images = all_images.filter(ee.Filter.lt(_CLOUD_PROP, self._cloud_threshold))

        total = int(all_images.size().getInfo() or 0)
        clear = int(clear_images.size().getInfo() or 0)

        if total > 0 and clear / total < (1 - _SAR_FALLBACK_RATIO):
            # >= 80% of revisits cloud-masked -> fall back to SAR.
            yield from self._fetch_block_sar(ee, block, geom, since, until)
            return

        for feature in clear_images.toList(clear).getInfo() or []:
            obs = self._image_feature_to_obs(ee, block, geom, feature)
            if obs is None:
                continue
            if since <= obs.ts < until:
                yield obs

    def _image_feature_to_obs(
        self,
        ee: Any,
        block: Block,
        geom: Any,
        feature: dict[str, Any],
    ) -> BlockObservation | None:
        props = feature.get("properties") or {}
        ts_raw = props.get("system:time_start") or props.get("system:index")
        try:
            if isinstance(ts_raw, int | float):
                # GEE epoch millis
                ts = datetime.fromtimestamp(ts_raw / 1000.0, tz=timezone.utc)
            elif isinstance(ts_raw, str) and ts_raw:
                # S2 system:index format: YYYYMMDDTHHMMSS_..._...
                stamp = ts_raw.split("_", 1)[0]
                ts = datetime.strptime(stamp[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            else:
                return None
        except ValueError:
            logger.warning("Sentinel-2: dropping image with bad ts=%r", ts_raw)
            return None

        # Build an ee.Image, compute the 3 indices, reduceRegion(mean).
        image = ee.Image(feature.get("id"))
        b4 = image.select("B4")
        b5 = image.select("B5")
        b8 = image.select("B8")
        b11 = image.select("B11")
        ndvi = b8.subtract(b4).divide(b8.add(b4)).rename("NDVI")
        ndre = b8.subtract(b5).divide(b8.add(b5)).rename("NDRE")
        ndmi = b8.subtract(b11).divide(b8.add(b11)).rename("NDMI")
        composite = ndvi.addBands(ndre).addBands(ndmi)
        means = (
            composite.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geom,
                scale=10,
                maxPixels=1_000_000,
            ).getInfo()
            or {}
        )

        def _clamp(v: Any) -> float | None:
            if v is None:
                return None
            try:
                f = float(v)
            except (TypeError, ValueError):
                return None
            import math  # noqa: PLC0415 — stdlib lazy import OK in hot path

            if math.isnan(f):
                return None
            return max(-1.0, min(1.0, f))

        return BlockObservation(
            block_id=block.id,
            ts=ts,
            source=ConnectorSource.SENTINEL2,
            ndvi=_clamp(means.get("NDVI")),
            ndre=_clamp(means.get("NDRE")),
            ndmi=_clamp(means.get("NDMI")),
            notes=json.dumps(
                {
                    "image_id": feature.get("id"),
                    "cloud_pct": props.get(_CLOUD_PROP),
                }
            )[:512],
        )

    def _fetch_block_sar(
        self,
        ee: Any,
        block: Block,
        geom: Any,
        since: datetime,
        until: datetime,
    ) -> Iterable[BlockObservation]:
        date_start = since.strftime("%Y-%m-%d")
        date_end = until.strftime("%Y-%m-%d")
        sar = (
            ee.ImageCollection(_S1_COLLECTION)
            .filterBounds(geom)
            .filterDate(date_start, date_end)
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        )
        listed = sar.toList(sar.size()).getInfo() or []
        if not listed:
            logger.warning(
                "Sentinel2Connector: SAR fallback found no S1 GRD images " "for block %s in %s..%s",
                block.id,
                date_start,
                date_end,
            )
            return
        for feature in listed:
            props = feature.get("properties") or {}
            ts_raw = props.get("system:time_start")
            if not isinstance(ts_raw, int | float):
                continue
            ts = datetime.fromtimestamp(ts_raw / 1000.0, tz=timezone.utc)
            if not (since <= ts < until):
                continue
            image = ee.Image(feature.get("id"))
            vv_db = (
                image.select("VV")
                .reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=geom,
                    scale=10,
                    maxPixels=1_000_000,
                )
                .getInfo()
                or {}
            )
            yield BlockObservation(
                block_id=block.id,
                ts=ts,
                source=ConnectorSource.SENTINEL2,
                quality_flag="sar_fallback",
                notes=json.dumps(
                    {
                        "sar_fallback": True,
                        "vv_db": vv_db.get("VV"),
                        "image_id": feature.get("id"),
                    }
                )[:512],
            )
