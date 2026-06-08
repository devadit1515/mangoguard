"""Tests for the Sentinel-2 NDVI/NDRE/NDMI connector.

All tests inject a fake ``ee`` module via the ``ee_module=`` constructor
parameter -- no live GEE calls, no network, no auth required. The fake
mimics the chainable ``ee.ImageCollection(...).filterBounds(...).filterDate(...)``
API plus ``.size().getInfo()``, ``.toList(n).getInfo()``, and
``ee.Image(id).select(...).reduceRegion(...).getInfo()``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.sentinel2 import Sentinel2Connector
from mangoguard.geo import load_blocks
from mangoguard.schema import ConnectorSource

REPO_ROOT = Path(__file__).resolve().parents[2]
BLOCKS_FIXTURE = REPO_ROOT / "data" / "orchard_blocks.geojson"

_WINDOW_START = datetime(2025, 1, 1, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 2, 1, tzinfo=timezone.utc)


def _sized_mock(value):
    sz = MagicMock()
    sz.getInfo.return_value = value
    return sz


def _wrapped_list(value):
    inner = MagicMock()
    inner.getInfo.return_value = value
    return inner


def _make_s2_collection(total_s2, clear_s2, s2_features):
    coll = MagicMock(name="s2-coll")
    coll.filterBounds.side_effect = lambda _g: coll
    coll.filterDate.side_effect = lambda _a, _b: coll
    coll.size.side_effect = lambda: _sized_mock(total_s2)

    clear_coll = MagicMock(name="s2-clear-coll")
    clear_coll.filterBounds.side_effect = lambda _g: clear_coll
    clear_coll.filterDate.side_effect = lambda _a, _b: clear_coll
    clear_coll.filter.side_effect = lambda _f: clear_coll
    clear_coll.size.side_effect = lambda: _sized_mock(clear_s2)
    clear_coll.toList.side_effect = lambda _n: _wrapped_list(s2_features or [])

    coll.filter.side_effect = lambda _f: clear_coll
    coll.toList.side_effect = lambda _n: _wrapped_list(s2_features or [])
    return coll


def _make_s1_collection(s1_features):
    coll = MagicMock(name="s1-coll")
    coll.filterBounds.side_effect = lambda _g: coll
    coll.filterDate.side_effect = lambda _a, _b: coll
    coll.filter.side_effect = lambda _f: coll
    coll.size.side_effect = lambda: _sized_mock(len(s1_features or []))
    coll.toList.side_effect = lambda _n: _wrapped_list(s1_features or [])
    return coll


def _make_image_factory(s2_index_means, s1_vv_db):
    def make_image(_image_id):
        img = MagicMock(name="image")
        img.select.side_effect = lambda _b=None: img
        img.subtract.side_effect = lambda _b=None: img
        img.add.side_effect = lambda _b=None: img
        img.divide.side_effect = lambda _b=None: img
        img.rename.side_effect = lambda _b=None: img
        img.addBands.side_effect = lambda _b=None: img
        rr = MagicMock(name="reduce-region")
        rr.getInfo.return_value = s2_index_means or (
            {"VV": s1_vv_db} if s1_vv_db is not None else {}
        )
        img.reduceRegion.return_value = rr
        return img

    return make_image


def _make_fake_ee(
    *,
    total_s2: int = 2,
    clear_s2: int = 2,
    s2_features: list[dict] | None = None,
    s2_index_means: dict[str, float] | None = None,
    s1_features: list[dict] | None = None,
    s1_vv_db: float | None = None,
):
    """Build a fake ``ee`` module that returns scripted values."""
    ee = MagicMock(name="ee")
    ee.Geometry = MagicMock()
    ee.Geometry.Polygon = MagicMock(return_value="fake-polygon")
    ee.Filter = MagicMock()
    ee.Filter.lt = MagicMock(return_value="filter-lt")
    ee.Filter.listContains = MagicMock(return_value="filter-listcontains")
    ee.Reducer = MagicMock()
    ee.Reducer.mean = MagicMock(return_value="reducer-mean")

    def make_collection(collection_id):
        if collection_id == "COPERNICUS/S2_SR_HARMONIZED":
            return _make_s2_collection(total_s2, clear_s2, s2_features)
        return _make_s1_collection(s1_features)

    ee.ImageCollection.side_effect = make_collection
    ee.Image.side_effect = _make_image_factory(s2_index_means, s1_vv_db)
    return ee


def test_yields_one_row_per_clear_image_per_block():
    """Two blocks x 2 clear S2 images each = 4 observations."""
    s2_features = [
        {
            "id": "S2A_T43QFB_20250115T053101",
            "properties": {
                "system:time_start": int(
                    datetime(2025, 1, 15, 5, 31, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "CLOUDY_PIXEL_PERCENTAGE": 12.5,
            },
        },
        {
            "id": "S2A_T43QFB_20250120T053101",
            "properties": {
                "system:time_start": int(
                    datetime(2025, 1, 20, 5, 31, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "CLOUDY_PIXEL_PERCENTAGE": 8.0,
            },
        },
    ]
    fake_ee = _make_fake_ee(
        total_s2=2,
        clear_s2=2,
        s2_features=s2_features,
        s2_index_means={"NDVI": 0.72, "NDRE": 0.41, "NDMI": 0.18},
    )
    blocks = load_blocks(BLOCKS_FIXTURE)
    conn = Sentinel2Connector(ConnectorContext(), blocks=blocks, ee_module=fake_ee)

    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 4
    assert all(r.source == ConnectorSource.SENTINEL2 for r in rows)
    block_ids = {r.block_id for r in rows}
    assert block_ids == {"B1", "B2"}


def test_ndvi_ndre_ndmi_populated_in_minus1_to_1_range():
    s2_features = [
        {
            "id": "S2A_T43QFB_20250115T053101",
            "properties": {
                "system:time_start": int(
                    datetime(2025, 1, 15, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "CLOUDY_PIXEL_PERCENTAGE": 5.0,
            },
        },
    ]
    fake_ee = _make_fake_ee(
        total_s2=1,
        clear_s2=1,
        s2_features=s2_features,
        s2_index_means={"NDVI": 0.65, "NDRE": 0.32, "NDMI": 0.15},
    )
    blocks = load_blocks(BLOCKS_FIXTURE)
    conn = Sentinel2Connector(ConnectorContext(), blocks=blocks, ee_module=fake_ee)

    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    for r in rows:
        assert r.ndvi == pytest.approx(0.65)
        assert r.ndre == pytest.approx(0.32)
        assert r.ndmi == pytest.approx(0.15)
        for v in (r.ndvi, r.ndre, r.ndmi):
            assert -1.0 <= v <= 1.0


def test_index_means_outside_minus1_1_get_clamped():
    """A buggy reduceRegion that returns ndvi=1.5 should be clamped to 1.0."""
    s2_features = [
        {
            "id": "S2A_bad",
            "properties": {
                "system:time_start": int(
                    datetime(2025, 1, 15, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "CLOUDY_PIXEL_PERCENTAGE": 5.0,
            },
        }
    ]
    fake_ee = _make_fake_ee(
        total_s2=1,
        clear_s2=1,
        s2_features=s2_features,
        s2_index_means={"NDVI": 1.5, "NDRE": -2.0, "NDMI": float("nan")},
    )
    blocks = load_blocks(BLOCKS_FIXTURE)
    conn = Sentinel2Connector(ConnectorContext(), blocks=blocks[:1], ee_module=fake_ee)

    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].ndvi == 1.0
    assert rows[0].ndre == -1.0
    assert rows[0].ndmi is None  # NaN -> None


def test_sar_fallback_triggers_when_cloud_cover_high():
    """If only 1 of 10 S2 images is clear, fall back to S1 GRD VV."""
    s1_features = [
        {
            "id": "S1A_IW_GRDH_20250715",
            "properties": {
                "system:time_start": int(
                    datetime(2025, 1, 16, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "transmitterReceiverPolarisation": ["VV", "VH"],
            },
        }
    ]
    fake_ee = _make_fake_ee(
        total_s2=10,
        clear_s2=1,  # 10% clear, 90% cloud -> fallback
        s2_features=[],
        s1_features=s1_features,
        s1_vv_db=-12.5,
    )
    blocks = load_blocks(BLOCKS_FIXTURE)
    conn = Sentinel2Connector(ConnectorContext(), blocks=blocks[:1], ee_module=fake_ee)

    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert len(rows) == 1
    assert rows[0].source == ConnectorSource.SENTINEL2
    assert rows[0].quality_flag == "sar_fallback"
    assert rows[0].ndvi is None
    assert rows[0].ndre is None
    assert rows[0].ndmi is None
    notes = json.loads(rows[0].notes)
    assert notes["sar_fallback"] is True
    assert notes["vv_db"] == -12.5


def test_no_clear_no_sar_yields_empty_with_warning(caplog):
    fake_ee = _make_fake_ee(
        total_s2=10,
        clear_s2=0,
        s2_features=[],
        s1_features=[],
    )
    blocks = load_blocks(BLOCKS_FIXTURE)
    conn = Sentinel2Connector(ConnectorContext(), blocks=blocks[:1], ee_module=fake_ee)
    with caplog.at_level("WARNING"):
        rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows == []
    assert any("SAR fallback" in r.message for r in caplog.records)


def test_constructor_rejects_empty_blocks_list():
    with pytest.raises(ValueError, match="at least one Block"):
        Sentinel2Connector(ConnectorContext(), blocks=[], ee_module=MagicMock())


def test_ts_is_timezone_aware_utc():
    s2_features = [
        {
            "id": "S2A_x",
            "properties": {
                "system:time_start": int(
                    datetime(2025, 1, 15, 5, 31, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "CLOUDY_PIXEL_PERCENTAGE": 5.0,
            },
        }
    ]
    fake_ee = _make_fake_ee(
        total_s2=1,
        clear_s2=1,
        s2_features=s2_features,
        s2_index_means={"NDVI": 0.5, "NDRE": 0.3, "NDMI": 0.1},
    )
    blocks = load_blocks(BLOCKS_FIXTURE)
    conn = Sentinel2Connector(ConnectorContext(), blocks=blocks[:1], ee_module=fake_ee)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    assert rows[0].ts.tzinfo is not None
    assert rows[0].ts.utcoffset().total_seconds() == 0


def test_notes_carries_image_id_and_cloud_pct():
    s2_features = [
        {
            "id": "S2A_T43QFB_20250115T053101",
            "properties": {
                "system:time_start": int(
                    datetime(2025, 1, 15, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "CLOUDY_PIXEL_PERCENTAGE": 12.5,
            },
        }
    ]
    fake_ee = _make_fake_ee(
        total_s2=1,
        clear_s2=1,
        s2_features=s2_features,
        s2_index_means={"NDVI": 0.7, "NDRE": 0.4, "NDMI": 0.2},
    )
    blocks = load_blocks(BLOCKS_FIXTURE)
    conn = Sentinel2Connector(ConnectorContext(), blocks=blocks[:1], ee_module=fake_ee)
    rows = list(conn.fetch(since=_WINDOW_START, until=_WINDOW_END))
    notes = json.loads(rows[0].notes)
    assert notes["image_id"] == "S2A_T43QFB_20250115T053101"
    assert notes["cloud_pct"] == 12.5


def test_connector_runs_end_to_end_to_store(store):
    s2_features = [
        {
            "id": "S2A_x",
            "properties": {
                "system:time_start": int(
                    datetime(2025, 1, 15, tzinfo=timezone.utc).timestamp() * 1000
                ),
                "CLOUDY_PIXEL_PERCENTAGE": 5.0,
            },
        }
    ]
    fake_ee = _make_fake_ee(
        total_s2=1,
        clear_s2=1,
        s2_features=s2_features,
        s2_index_means={"NDVI": 0.7, "NDRE": 0.4, "NDMI": 0.2},
    )
    blocks = load_blocks(BLOCKS_FIXTURE)
    conn = Sentinel2Connector(ConnectorContext(store=store), blocks=blocks, ee_module=fake_ee)
    n = conn.run(since=_WINDOW_START, until=_WINDOW_END)
    assert n == 2
    assert store.count_by_source().get(ConnectorSource.SENTINEL2, 0) == 2
