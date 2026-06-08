# MangoGuard Plan 2: Free Public Baseline Connectors

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Prerequisites:** Plan 1 complete (`v0.1.0` tagged).

**Goal:** Implement the four always-on free public connectors that ship for every MangoGuard user regardless of which (if any) commercial monitoring system the farmer has: **AGMARKNET** (mango mandi prices), **IMD Mausam + Meghdoot** (district weather forecast + agromet advisory), **DBSKKV Dapoli** (Konkan-tuned microclimate + climate-trend PDFs), **Maharashtra CROPSAP** (taluka pest surveillance), plus the **Sentinel-2 via GEE** geospatial connector that powers the Orchard Health Dashboard.

**Architecture:** Each connector is a `Connector` subclass living in `src/mangoguard/connectors/`. They share the unified `BlockObservation` schema from Plan 1. HTTP-bound connectors use `requests` with retry+backoff. PDF-bound connectors use `pdfplumber` + `pymupdf`. Sentinel-2 uses `earthengine-api` (initialized lazily, mocked in tests).

**Tech Stack:** `requests`, `beautifulsoup4`, `pdfplumber`, `pymupdf`, `earthengine-api`, `freezegun`, `pytest-mock`.

---

## File Structure

```
src/mangoguard/connectors/
├── agmarknet.py          # AGMARKNET via data.gov.in OGD API
├── imd.py                # IMD Mausam + Meghdoot PDF scrape + REST API
├── dbskkv.py             # DBSKKV Dapoli HTML + climate-trend PDF
├── cropsap.py            # Maharashtra CROPSAP HTML scrape
├── sentinel2.py          # Sentinel-2 NDVI/NDRE/NDMI via GEE (Sentinel-1 SAR fallback)
└── _http.py              # shared HTTP-with-retry helper

src/mangoguard/geo.py     # GPS polygon utilities (Block dataclass, ee.Geometry adapter)

tests/connectors/
├── test_agmarknet.py
├── test_imd.py
├── test_dbskkv.py
├── test_cropsap.py
├── test_sentinel2.py
├── test_baseline_e2e.py
└── fixtures/             # pinned sample responses (HTML, JSON, PDF) for offline tests
    ├── agmarknet_maharashtra_mango_2025-07-12.json
    ├── imd_ratnagiri_amfu_2025-07-12.pdf
    ├── dbskkv_dapoli_forecast_2025-07-12.html
    └── cropsap_ratnagiri_2025-07-12.html

tests/test_geo.py
data/orchard_blocks.geojson  # ~4-8 polygon FeatureCollection from Visit 1 (placeholder ok)
```

---

## Task 1: Shared HTTP helper

**Files:** Create `src/mangoguard/connectors/_http.py` + `tests/connectors/test_http.py`.

A single `get_with_retry(url, *, params=None, headers=None, max_retries=3, backoff_base=1.5, timeout=30) -> requests.Response` function used by every HTTP connector. Retries on `ConnectionError`, `Timeout`, and HTTP 429 / 5xx. Logs each retry with `logging.warning(...)`. Sleep between retries: `backoff_base ** attempt` seconds.

- [ ] **Step 1: Write failing tests** — success on first try, retry-then-success on 503, give-up after 3 failed retries, pass-through on 404. Use the `responses` library to mock HTTP.
- [ ] **Step 2: Implement `get_with_retry`** — `requests.get` in a `for attempt in range(max_retries+1)` loop with exponential backoff.
- [ ] **Step 3: Verify all 4 tests pass.**
- [ ] **Step 4: Commit:** `feat(connectors): shared get_with_retry helper`

---

## Task 2: AGMARKNET connector

**API:** `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`. Free with API key from data.gov.in; key in `ConnectorContext.secrets["DATA_GOV_IN_KEY"]`. Query: `api-key`, `format=json`, `filters[commodity]=Mango`, `filters[state]=Maharashtra`, `limit=1000`. Response: `records[]` with `arrival_date` (`DD/MM/YYYY`), `market`, `min_price`, `max_price`, `modal_price`.

**Mapping to `BlockObservation`:** `block_id` = market name lowercased (`"vashi"`, `"ratnagiri"`, `"devgad"`, `"vengurla"`); `ts` = `arrival_date` parsed as `Asia/Kolkata` midnight (use `dateutil.parser`); `source = AGMARKNET`; `mandi_modal_price_inr_per_quintal = float(modal_price)`. Weather fields stay `None`.

**Files:** Create `src/mangoguard/connectors/agmarknet.py` + `tests/connectors/fixtures/agmarknet_maharashtra_mango_2025-07-12.json` (≥5 real records) + `tests/connectors/test_agmarknet.py`.

- [ ] **Step 1:** Pull a real sample from the live API once and save as fixture JSON.
- [ ] **Step 2: Write failing test** — `test_loads_5_records_from_fixture`, `test_normalizes_market_name_lowercase`, `test_ts_is_timezone_aware`, `test_modal_price_is_float`.
- [ ] **Step 3: Implement `AGMARKNETConnector(Connector)`** with `source = ConnectorSource.AGMARKNET, name = "agmarknet"`. Accept an injected `http_get` callable defaulting to `get_with_retry`; tests pass a fake.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Add integration test** marked `@pytest.mark.integration`, skipped unless `DATA_GOV_IN_KEY` env var set. Asserts ≥1 live record.
- [ ] **Step 6: Commit:** `feat(connectors): AGMARKNET mandi-price connector`

---

## Task 3: IMD Mausam + Meghdoot connector

**Two data paths:**
1. **API:** `https://api.imd.gov.in/public/get_district_nowcast.php?district=Ratnagiri` — gated by IP whitelist (request via `sankar.nath@imd.gov.in`). JSON response.
2. **PDF scrape:** Twice-weekly (Tue/Fri) PDFs linked from `https://mausam.imd.gov.in/imd_latest/contents/agromet/advisory/englishstate_current.php`. Per-AMFU PDFs like `Ratnagiri_AMFU_YYYY-MM-DD.pdf` contain a 5-day forecast tabular section.

**Strategy:** Try API first if `secrets["IMD_API_KEY"]` set; fall back to PDF parse. Both produce daily rows with `block_id` = district name (`"ratnagiri"`, `"sindhudurg"`), `t_air_c`, `rh_pct`, `precip_mm`, `wind_speed_ms` filled.

**Files:** Create `src/mangoguard/connectors/imd.py` + `tests/connectors/fixtures/imd_ratnagiri_amfu_2025-07-12.pdf` + `tests/connectors/test_imd.py`.

- [ ] **Step 1:** Download one real IMD AMFU PDF for Ratnagiri to fixtures.
- [ ] **Step 2: Write failing tests** — `test_pdf_yields_5_daily_rows`, `test_temperature_in_plausible_range_20_40C`, `test_rh_in_0_100`, `test_district_block_id_is_ratnagiri`.
- [ ] **Step 3: Implement `_parse_imd_pdf(path: Path) -> list[BlockObservation]`** using `pdfplumber.open(path).pages[0].extract_table()`. The IMD AMFU PDFs have a 5-day forecast table on page 1; document column mapping (typically: Date | Tmax | Tmin | RH morning | RH evening | Rainfall | Wind).
- [ ] **Step 4: Implement `IMDConnector(Connector)`** with `source = ConnectorSource.IMD, name = "imd"`. `fetch()` tries API if key set, else PDF parse.
- [ ] **Step 5: Verify tests pass.**
- [ ] **Step 6: Commit:** `feat(connectors): IMD Mausam+Meghdoot agromet connector (PDF + API)`

---

## Task 4: DBSKKV Dapoli connector

**Path:** `https://www.dbskkv.org/farmers-corner/weather-forecast` — daily Konkan-tuned forecast table in HTML. Plus annual climate-trend PDFs (used only for historical context, not real-time).

**Mapping:** `block_id = "dapoli"`, `source = DBSKKV`, daily `t_air_c, rh_pct, precip_mm`.

**Files:** Create `src/mangoguard/connectors/dbskkv.py` + `tests/connectors/fixtures/dbskkv_dapoli_forecast_2025-07-12.html` + `tests/connectors/test_dbskkv.py`.

- [ ] **Step 1:** Save one real HTML snapshot to fixtures.
- [ ] **Step 2: Write failing test** — `test_parses_forecast_table_yields_5_rows`, `test_handles_missing_cells_gracefully`.
- [ ] **Step 3: Implement `DBSKKVConnector(Connector)`** using `BeautifulSoup4`. Identify the forecast table by `<table class="...weather...">` or by row-count heuristic. Document fragile selectors in a comment block.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(connectors): DBSKKV Dapoli Konkan microclimate connector`

---

## Task 5: Maharashtra CROPSAP connector

**Path:** `https://cropsap.maharashtra.gov.in/` — public HTML pest-incidence dashboard, filterable per taluka. Mango pests tracked: hopper, thrips, powdery mildew, anthracnose.

**Mapping:** `block_id` = taluka name (`"ratnagiri"`, `"sindhudurg"`, `"raigad"`), `source = CROPSAP`, `cropsap_pest_pressure` = reported infestation % (parsed as float), `notes` = JSON string `{"pathogen": "anthracnose"}` for downstream use.

**Files:** Create `src/mangoguard/connectors/cropsap.py` + `tests/connectors/fixtures/cropsap_ratnagiri_2025-07-12.html` + `tests/connectors/test_cropsap.py`.

- [ ] **Step 1:** Save one real HTML snapshot.
- [ ] **Step 2: Write failing test** — `test_yields_one_row_per_pathogen_per_taluka`, `test_pest_pressure_is_nonneg_float`, `test_notes_includes_pathogen_label`.
- [ ] **Step 3: Implement `CROPSAPConnector(Connector)`** using BeautifulSoup4. Yield 4 rows per taluka per query (one per tracked pathogen).
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(connectors): Maharashtra CROPSAP taluka pest-surveillance connector`

---

## Task 6: GPS polygon utilities

**Files:** Create `src/mangoguard/geo.py` + `tests/test_geo.py` + `data/orchard_blocks.geojson` (placeholder 2-block FeatureCollection).

```python
# src/mangoguard/geo.py — design sketch (implement following TDD)

from dataclasses import dataclass
from pathlib import Path
import json

@dataclass(frozen=True, slots=True)
class Block:
    id: str
    polygon_geojson: dict   # {"type": "Polygon", "coordinates": [[...]]}

def load_blocks(path: str | Path) -> list[Block]:
    """Load GeoJSON FeatureCollection and return list of Block objects.

    Each Feature MUST have properties.id (string) and a Polygon geometry."""
    data = json.loads(Path(path).read_text())
    if data.get("type") != "FeatureCollection":
        raise ValueError("Expected FeatureCollection")
    return [
        Block(id=f["properties"]["id"], polygon_geojson=f["geometry"])
        for f in data["features"]
    ]

def block_to_ee_geometry(block: Block):
    """Adapter: Block -> ee.Geometry. Imports ee lazily to keep tests offline."""
    import ee  # noqa: PLC0415 — lazy import
    return ee.Geometry.Polygon(block.polygon_geojson["coordinates"])
```

- [ ] **Step 1: Write failing test** — `test_load_blocks_yields_2_blocks_from_fixture`, `test_block_ids_are_unique`, `test_polygon_has_valid_geojson_structure`.
- [ ] **Step 2: Implement `Block` + `load_blocks` + `block_to_ee_geometry`.**
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(geo): Block dataclass + GeoJSON loader + ee.Geometry adapter`

---

## Task 7: Sentinel-2 connector

**API:** Google Earth Engine. Authenticate once interactively (`ee.Authenticate()`), then `ee.Initialize(project="<gcp-project-id>")` from `secrets["GEE_PROJECT_ID"]`. Tests skip EE init by setting env `MANGOGUARD_SKIP_EE=1` and mocking `ee` module via `pytest-mock`.

**Indices:**
- NDVI = (B8 - B4) / (B8 + B4)
- NDRE = (B8 - B5) / (B8 + B5)
- NDMI = (B8 - B11) / (B8 + B11)

**Cloud filter:** `COPERNICUS/S2_SR_HARMONIZED`, filter `CLOUDY_PIXEL_PERCENTAGE < 30`. Reduce per-polygon with `mean()`. One `BlockObservation` per (block, image date).

**Monsoon fallback:** If a target ISO week has ≥80% of S2 images cloud-masked for the queried polygon, additionally pull Sentinel-1 SAR (`COPERNICUS/S1_GRD`, VV polarization) and log `notes='{"sar_fallback": true, "vv_db": <mean>}'`. Do NOT populate NDVI/NDRE/NDMI from SAR (different signal).

**Files:** Create `src/mangoguard/connectors/sentinel2.py` + `tests/connectors/test_sentinel2.py`.

- [ ] **Step 1: Write failing test** with `ee` module mocked. Test cases: `test_yields_one_row_per_block_per_date`, `test_ndvi_in_range_minus1_to_1`, `test_sar_fallback_triggers_when_cloud_cover_high`.
- [ ] **Step 2: Implement `Sentinel2Connector(Connector)`** with `source = ConnectorSource.SENTINEL2, name = "sentinel2"`. Lazy-init EE on first `fetch()` unless `MANGOGUARD_SKIP_EE` is set.
- [ ] **Step 3: Verify unit tests pass.**
- [ ] **Step 4: Add integration test** marked `@pytest.mark.integration`, runs against live GEE with one reference orchard polygon (Ratnagiri).
- [ ] **Step 5: Commit:** `feat(connectors): Sentinel-2 NDVI/NDRE/NDMI via GEE with SAR fallback`

---

## Task 8: End-to-end integration test for the 5 free baselines

**Files:** Create `tests/connectors/test_baseline_e2e.py`.

A single test that:
1. Creates `FeedStore(":memory:")`.
2. Runs all 5 free public connectors (`AGMARKNET, IMD, DBSKKV, CROPSAP, Sentinel-2`) over a 7-day window using pinned fixtures (no live network; Sentinel-2 uses mocked `ee`).
3. Asserts the store contains rows from all 5 sources via `count_by_source()` helper.
4. Asserts at least one row per `(source, block_id)` combination.

- [ ] **Step 1: Add a helper to `FeedStore` if needed:** `count_by_source() -> dict[ConnectorSource, int]`. Test it; commit separately as `feat(store): add count_by_source helper`.
- [ ] **Step 2: Write the e2e test.**
- [ ] **Step 3: Run, verify PASS.**
- [ ] **Step 4: Commit:** `test(connectors): end-to-end baseline-stack integration test`

---

## Task 9: Bump version + tag

- [ ] **Step 1:** Bump `__version__` and `pyproject.toml` to `0.2.0`.
- [ ] **Step 2:** Run `pytest -v` — expect all Plan 1 + Plan 2 tests pass.
- [ ] **Step 3:** Commit + tag `v0.2.0`.

---

## Acceptance criteria for Plan 2 complete

- [ ] All 5 baseline connectors (`AGMARKNET, IMD, DBSKKV, CROPSAP, Sentinel-2`) have unit tests with pinned fixtures.
- [ ] At least 3 of 5 have integration tests (skipped unless API keys / GEE auth available).
- [ ] End-to-end test loads all 5 into one FeedStore.
- [ ] Tagged `v0.2.0`.
