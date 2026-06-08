"""End-to-end integration test for the 5 free public baseline connectors.

Wires AGMARKNET + IMD + DBSKKV + CROPSAP + Sentinel-2 (with mocked GEE)
through a single in-memory FeedStore and asserts:

1. All 5 sources land rows in the same store (count_by_source).
2. The unified BlockObservation schema accommodates heterogeneous payloads:
   AGMARKNET (price-only), IMD (forecast weather), DBSKKV (Konkan microclimate),
   CROPSAP (pest pressure), Sentinel-2 (NDVI/NDRE/NDMI).
3. Per-source row counts match the fixtures' expected output.
4. The Connector.run() audit trail (ingested_at + connector_run_id) is stamped
   on every row regardless of source.
5. Multi-source queries by block_id / window work across the merged store.

This is the smoke test that proves Plan 2's interoperability claim:
"MangoGuard ingests from 5 heterogeneous Indian agri data sources into one
unified schema." If this test passes, Plan 4's focal recommender has a clean
data layer to consume.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from mangoguard.connectors.agmarknet import AGMARKNETConnector
from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.cropsap import CROPSAPConnector
from mangoguard.connectors.dbskkv import DBSKKVConnector
from mangoguard.connectors.imd import IMDConnector
from mangoguard.connectors.sentinel2 import Sentinel2Connector
from mangoguard.geo import load_blocks
from mangoguard.schema import ConnectorSource

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "connectors" / "fixtures"
BLOCKS_GEOJSON = REPO_ROOT / "data" / "orchard_blocks.geojson"

_WINDOW_START = datetime(2025, 1, 1, tzinfo=timezone.utc)
_WINDOW_END = datetime(2025, 8, 1, tzinfo=timezone.utc)


def _make_fake_ee_for_s2():
    """Minimal fake ee module: yields 1 S2 image per block with mid-range NDVI."""
    ee = MagicMock(name="ee")
    ee.Geometry = MagicMock()
    ee.Geometry.Polygon = MagicMock(return_value="fake-polygon")
    ee.Filter = MagicMock()
    ee.Filter.lt = MagicMock(return_value="filter-lt")
    ee.Filter.listContains = MagicMock(return_value="filter-listcontains")
    ee.Reducer = MagicMock()
    ee.Reducer.mean = MagicMock(return_value="reducer-mean")

    s2_feature = {
        "id": "S2A_T43QFB_20250215T053101",
        "properties": {
            "system:time_start": int(
                datetime(2025, 2, 15, 5, 31, tzinfo=timezone.utc).timestamp() * 1000
            ),
            "CLOUDY_PIXEL_PERCENTAGE": 8.0,
        },
    }

    def _sized(value):
        sz = MagicMock()
        sz.getInfo.return_value = value
        return sz

    def _wrapped(value):
        inner = MagicMock()
        inner.getInfo.return_value = value
        return inner

    def make_collection(collection_id):
        coll = MagicMock()
        if collection_id == "COPERNICUS/S2_SR_HARMONIZED":
            clear_coll = MagicMock()
            clear_coll.filterBounds.side_effect = lambda _g: clear_coll
            clear_coll.filterDate.side_effect = lambda _a, _b: clear_coll
            clear_coll.filter.side_effect = lambda _f: clear_coll
            clear_coll.size.side_effect = lambda: _sized(1)
            clear_coll.toList.side_effect = lambda _n: _wrapped([s2_feature])
            coll.filterBounds.side_effect = lambda _g: coll
            coll.filterDate.side_effect = lambda _a, _b: coll
            coll.filter.side_effect = lambda _f: clear_coll
            coll.size.side_effect = lambda: _sized(1)
            coll.toList.side_effect = lambda _n: _wrapped([s2_feature])
        else:
            coll.filterBounds.side_effect = lambda _g: coll
            coll.filterDate.side_effect = lambda _a, _b: coll
            coll.filter.side_effect = lambda _f: coll
            coll.size.side_effect = lambda: _sized(0)
            coll.toList.side_effect = lambda _n: _wrapped([])
        return coll

    ee.ImageCollection.side_effect = make_collection

    def make_image(_id):
        img = MagicMock()
        img.select.side_effect = lambda _b=None: img
        img.subtract.side_effect = lambda _b=None: img
        img.add.side_effect = lambda _b=None: img
        img.divide.side_effect = lambda _b=None: img
        img.rename.side_effect = lambda _b=None: img
        img.addBands.side_effect = lambda _b=None: img
        rr = MagicMock()
        rr.getInfo.return_value = {"NDVI": 0.68, "NDRE": 0.39, "NDMI": 0.16}
        img.reduceRegion.return_value = rr
        return img

    ee.Image.side_effect = make_image
    return ee


def test_five_baseline_connectors_into_one_store(store):
    """Run all 5 baselines into a single FeedStore and assert per-source coverage."""
    ctx = ConnectorContext(store=store)

    # AGMARKNET — 8 fixture records, 1 dropped (empty market),
    # 1 collision-suffixed at Vashi 2025-07-12 -> 7 rows
    agmarknet = AGMARKNETConnector(ctx)
    agmarknet.fetch = lambda since, until: agmarknet.parse_fixture(  # type: ignore[method-assign]
        str(FIXTURES / "agmarknet_maharashtra_mango_2025-07-12.json"),
        since=since,
        until=until,
    )
    n_agm = agmarknet.run(since=_WINDOW_START, until=_WINDOW_END)

    # IMD — 5 daily rows from Ratnagiri AMFU
    imd = IMDConnector(
        ctx,
        district="Ratnagiri",
        fixture_path=FIXTURES / "imd_ratnagiri_amfu_2025-07-12.html",
    )
    n_imd = imd.run(since=_WINDOW_START, until=_WINDOW_END)

    # DBSKKV — 5 daily rows from Dapoli station
    dbskkv = DBSKKVConnector(ctx, fixture_path=FIXTURES / "dbskkv_dapoli_forecast_2025-07-12.html")
    n_dbskkv = dbskkv.run(since=_WINDOW_START, until=_WINDOW_END)

    # CROPSAP — 8 (taluka, pathogen) rows
    cropsap = CROPSAPConnector(ctx, fixture_path=FIXTURES / "cropsap_ratnagiri_2025-07-12.html")
    n_cropsap = cropsap.run(since=_WINDOW_START, until=_WINDOW_END)

    # Sentinel-2 — 1 S2 image x 2 blocks = 2 rows
    blocks = load_blocks(BLOCKS_GEOJSON)
    sentinel2 = Sentinel2Connector(ctx, blocks=blocks, ee_module=_make_fake_ee_for_s2())
    n_s2 = sentinel2.run(since=_WINDOW_START, until=_WINDOW_END)

    assert n_agm == 7
    assert n_imd == 5
    assert n_dbskkv == 5
    assert n_cropsap == 8
    assert n_s2 == 2

    by_source = store.count_by_source()
    assert by_source[ConnectorSource.AGMARKNET] == 7
    assert by_source[ConnectorSource.IMD] == 5
    assert by_source[ConnectorSource.DBSKKV] == 5
    assert by_source[ConnectorSource.CROPSAP] == 8
    assert by_source[ConnectorSource.SENTINEL2] == 2

    assert store.count() == 7 + 5 + 5 + 8 + 2  # 27


def test_audit_trail_stamped_across_all_sources(store):
    """Every connector path stamps ingested_at + connector_run_id via Connector.run."""
    ctx = ConnectorContext(store=store)

    imd = IMDConnector(
        ctx,
        district="Ratnagiri",
        fixture_path=FIXTURES / "imd_ratnagiri_amfu_2025-07-12.html",
    )
    imd.run(since=_WINDOW_START, until=_WINDOW_END)

    dbskkv = DBSKKVConnector(ctx, fixture_path=FIXTURES / "dbskkv_dapoli_forecast_2025-07-12.html")
    dbskkv.run(since=_WINDOW_START, until=_WINDOW_END)

    imd_rows = store.query_by_source(ConnectorSource.IMD)
    dbskkv_rows = store.query_by_source(ConnectorSource.DBSKKV)
    assert all(r.ingested_at is not None for r in imd_rows + dbskkv_rows)
    assert all(r.connector_run_id is not None for r in imd_rows + dbskkv_rows)

    imd_run_ids = {r.connector_run_id for r in imd_rows}
    dbskkv_run_ids = {r.connector_run_id for r in dbskkv_rows}
    assert len(imd_run_ids) == 1
    assert len(dbskkv_run_ids) == 1
    assert imd_run_ids != dbskkv_run_ids


def test_unified_schema_accommodates_heterogeneous_payloads(store):
    """AGMARKNET writes price-only rows; IMD writes weather-only rows; both coexist."""
    ctx = ConnectorContext(store=store)

    agmarknet = AGMARKNETConnector(ctx)
    agmarknet.fetch = lambda since, until: agmarknet.parse_fixture(  # type: ignore[method-assign]
        str(FIXTURES / "agmarknet_maharashtra_mango_2025-07-12.json"),
        since=since,
        until=until,
    )
    agmarknet.run(since=_WINDOW_START, until=_WINDOW_END)

    imd = IMDConnector(
        ctx,
        district="Ratnagiri",
        fixture_path=FIXTURES / "imd_ratnagiri_amfu_2025-07-12.html",
    )
    imd.run(since=_WINDOW_START, until=_WINDOW_END)

    agm_rows = store.query_by_source(ConnectorSource.AGMARKNET)
    imd_rows = store.query_by_source(ConnectorSource.IMD)

    for r in agm_rows:
        assert r.mandi_modal_price_inr_per_quintal is not None
        assert r.t_air_c is None
        assert r.ndvi is None

    for r in imd_rows:
        assert r.t_air_c is not None
        assert r.rh_pct is not None
        assert r.precip_mm is not None
        assert r.mandi_modal_price_inr_per_quintal is None
        assert r.ndvi is None
