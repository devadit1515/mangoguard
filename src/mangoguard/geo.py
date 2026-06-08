"""GPS polygon utilities for orchard blocks.

A `Block` represents one polygon-bounded chunk of an orchard. Plan 2's
Sentinel-2 connector queries Google Earth Engine per Block per revisit
to compute mean NDVI/NDRE/NDMI inside the polygon. Plan 4's disease-risk
engine attaches per-Block weather/CROPSAP signals to each polygon-area
spray decision. Plan 6's dashboard renders Blocks as a map overlay.

GeoJSON FeatureCollection schema this module accepts:

    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {"id": "B1"},
          "geometry": {"type": "Polygon", "coordinates": [[[lon, lat], ...]]}
        }
      ]
    }

Block IDs must be unique within a FeatureCollection. They become
``block_id`` on every BlockObservation produced by a polygon-aware
connector (currently Sentinel-2).

The ``ee`` (Google Earth Engine) import is lazy inside
``block_to_ee_geometry`` so this module loads cleanly in environments
without earthengine-api installed. Tests that mock ee never touch the
import path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Block:
    """One orchard block: a polygon plus a stable string id.

    The polygon is stored as a parsed GeoJSON geometry dict
    (``{"type": "Polygon", "coordinates": [[[lon, lat], ...]]}``) rather
    than a Shapely / GeoPandas object so this module has no heavy
    geospatial dependencies. Conversion to ``ee.Geometry`` happens on
    demand in ``block_to_ee_geometry``.
    """

    id: str
    polygon_geojson: dict[str, Any]


def load_blocks(path: str | Path) -> list[Block]:
    """Load a GeoJSON FeatureCollection and return its blocks.

    Each Feature MUST have:
    - ``properties.id``: non-empty string, unique within the collection
    - ``geometry.type == "Polygon"``
    - ``geometry.coordinates``: a non-empty list of linear rings

    Raises ``ValueError`` on malformed input. Order of returned blocks
    matches the order of features in the source file.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("type") != "FeatureCollection":
        msg = f"Expected GeoJSON FeatureCollection, got type={raw.get('type')!r}"
        raise ValueError(msg)

    features = raw.get("features")
    if not isinstance(features, list):
        msg = "FeatureCollection.features must be a list"
        raise ValueError(msg)

    blocks: list[Block] = []
    seen_ids: set[str] = set()
    for i, feat in enumerate(features):
        if not isinstance(feat, dict) or feat.get("type") != "Feature":
            msg = f"feature[{i}] is not a Feature dict"
            raise ValueError(msg)
        props = feat.get("properties") or {}
        block_id = props.get("id")
        if not isinstance(block_id, str) or not block_id.strip():
            msg = f"feature[{i}].properties.id must be a non-empty string"
            raise ValueError(msg)
        if block_id in seen_ids:
            msg = f"duplicate block id {block_id!r} in {path}"
            raise ValueError(msg)
        seen_ids.add(block_id)

        geom = feat.get("geometry")
        if not isinstance(geom, dict) or geom.get("type") != "Polygon":
            geom_type = geom.get("type") if isinstance(geom, dict) else type(geom).__name__
            msg = f"feature[{i}] ({block_id!r}) geometry must be Polygon, got {geom_type}"
            raise ValueError(msg)
        coords = geom.get("coordinates")
        if not isinstance(coords, list) or not coords or not coords[0]:
            msg = f"feature[{i}] ({block_id!r}) Polygon.coordinates must be non-empty"
            raise ValueError(msg)

        blocks.append(Block(id=block_id, polygon_geojson=geom))

    return blocks


def block_to_ee_geometry(block: Block, ee_module: Any | None = None) -> Any:
    """Adapter: convert a Block to an ``ee.Geometry.Polygon``.

    If ``ee_module`` is provided (tests inject a fake), it is used directly.
    Otherwise lazy-imports ``ee`` (earthengine-api) so this module loads in
    environments that have not installed the ``geo`` extra. Caller is
    responsible for ``ee.Initialize()`` having been called.

    Raises ``RuntimeError`` if ``ee`` is unavailable.
    """
    if ee_module is not None:
        ee = ee_module
    else:
        try:
            import ee  # noqa: PLC0415 — lazy import for optional dep
        except ImportError as e:
            msg = "block_to_ee_geometry requires earthengine-api: pip install -e '.[geo]'"
            raise RuntimeError(msg) from e

    return ee.Geometry.Polygon(block.polygon_geojson["coordinates"])
