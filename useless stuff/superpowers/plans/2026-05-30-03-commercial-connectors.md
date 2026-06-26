# MangoGuard Plan 3: Commercial Connectors

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. **Prerequisites:** Plan 1 complete (`v0.1.0`). Can run in parallel with Plan 2.

**Goal:** Implement the five commercial/institutional connectors that ingest data from monitoring systems the farmer already runs: **Pessl iMETOS** (public REST API + HMAC), **Fyllo** (app-login screen-scrape), **Fasal** (app-login screen-scrape or farmer-shared CSV), **Plantix** (farmer-shared screenshot history + Vision-LLM OCR), and a generic **CSV upload fallback**.

**Architecture:** Each connector subclasses `Connector`. Pessl uses the documented REST API. Fyllo/Fasal use `playwright` for browser automation. Plantix uses Gemini 1.5 Flash Vision API for OCR. CSV fallback parses a documented schema. All connectors mockable in tests.

**Tech Stack:** `requests` + `hmac` (Pessl), `playwright` (Fyllo/Fasal), `google-generativeai` (Gemini), `pandas` (CSV).

---

## File Structure

```
src/mangoguard/connectors/
├── pessl.py              # Pessl iMETOS / FieldClimate REST API + HMAC
├── fyllo.py              # Fyllo (AgriHawk) browser scrape + chart OCR
├── fasal.py              # Fasal (Wolkus) CSV + optional browser scrape
├── plantix.py            # Plantix screenshot OCR via Gemini Vision
├── csv_fallback.py       # generic CSV upload per documented schema
├── registry.py           # ConnectorSource -> Connector class factory
└── _auth.py              # HMAC signing for Pessl

tests/connectors/
├── test_auth.py
├── test_pessl.py
├── test_fyllo.py
├── test_fasal.py
├── test_plantix.py
├── test_csv_fallback.py
├── test_registry.py
├── test_commercial_e2e.py
└── fixtures/
    ├── pessl_fieldclimate_sample_response.json
    ├── fyllo_dashboard_screenshot.png
    ├── fyllo_chart_export.png
    ├── fasal_export.csv
    ├── plantix_diagnosis_screenshot_anthracnose.png
    ├── plantix_diagnosis_screenshot_powdery_mildew.png
    └── csv_fallback_sample.csv

data/csv_fallback_schema.yaml
```

---

## Task 1: HMAC auth helper for Pessl

**Files:** Create `src/mangoguard/connectors/_auth.py` + `tests/connectors/test_auth.py`.

Pessl FieldClimate API requires HMAC-SHA256 signing: signed string = `{method}{path}{date}{public_key}`, signature = `hmac.new(private_key, signed_string, sha256).hexdigest()`. Headers needed: `Accept: application/json`, `Authorization: hmac {public_key}:{signature}`, `Date: {RFC1123 date}`.

- [ ] **Step 1: Write failing test** — `test_sign_request_produces_correct_hmac_for_known_input` using a worked example from `https://api.fieldclimate.com/v2/docs/`.
- [ ] **Step 2: Implement `sign_pessl_request(method, path, public_key, private_key) -> dict[str, str]`** returning the 3 required headers (`Accept`, `Authorization`, `Date`).
- [ ] **Step 3: Verify test passes.**
- [ ] **Step 4: Commit:** `feat(connectors): Pessl HMAC signing helper`

---

## Task 2: Pessl iMETOS connector

**API:** `https://api.fieldclimate.com/v2/`. Endpoints:
- `GET /user/stations` — list stations the user owns
- `GET /data/{station_id}/raw/from/{from_iso}/to/{to_iso}` — raw sensor data

**Auth:** Each station owner generates HMAC public/private keys at `ng.fieldclimate.com -> User -> API services -> GENERATE NEW`. Stored in `ConnectorContext.secrets["PESSL_PUBLIC_KEY"]` and `secrets["PESSL_PRIVATE_KEY"]`.

**Sensor mapping to `BlockObservation`:** `block_id` = station ID; `source = PESSL`.
- HC Air temperature → `t_air_c`
- HC Air humidity → `rh_pct`
- Leaf Wetness (minutes/hour) → `leaf_wetness_hr = minutes / 60`
- Precipitation → `precip_mm`
- Wind speed → `wind_speed_ms`
- Solar radiation → `solar_w_m2`
- Soil moisture VWC → `soil_moisture_pct`

**Files:** Create `src/mangoguard/connectors/pessl.py` + `tests/connectors/fixtures/pessl_fieldclimate_sample_response.json` + `tests/connectors/test_pessl.py`.

- [ ] **Step 1:** Save one real or worked-example Pessl response JSON to fixtures.
- [ ] **Step 2: Write failing tests** — `test_lists_stations_yields_expected_ids`, `test_raw_data_normalizes_to_block_observations`, `test_leaf_wetness_minutes_to_hours_conversion`, `test_missing_sensors_yield_none_not_zero`.
- [ ] **Step 3: Implement `PesslConnector(Connector)`** with `source = ConnectorSource.PESSL, name = "pessl"`. Inject `http_get` for testability.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Add integration test** `@pytest.mark.integration`, skipped unless `PESSL_PUBLIC_KEY` + `PESSL_PRIVATE_KEY` env vars set.
- [ ] **Step 6: Commit:** `feat(connectors): Pessl iMETOS FieldClimate REST connector`

---

## Task 3: Fyllo connector (browser scrape + OCR)

**Path:** Fyllo has no public API. Pragmatic path is `playwright` browser automation:
1. Open `https://app.fyllo.in/login`.
2. Submit credentials (`secrets["FYLLO_EMAIL"]`, `secrets["FYLLO_PASSWORD"]`).
3. Navigate to per-plot historical chart.
4. Either (a) export chart as PNG/PDF, then OCR data table, OR (b) screenshot + layout-aware extractor.

**Mapping:** `block_id` = Fyllo plot name lowercased; `source = FYLLO`. Fyllo Kairo reports: rainfall, T, RH, leaf wetness, solar/lux at ~20-min intervals.

**Files:** Create `src/mangoguard/connectors/fyllo.py` + 2 fixture PNGs + `tests/connectors/test_fyllo.py`.

- [ ] **Step 1: Capture 2 fixture screenshots** — dashboard + chart-export view. Use Fyllo's public marketing screenshots if no real account.
- [ ] **Step 2: Write failing tests** using fixture PNGs only (no live browser) — `test_parse_chart_export_yields_observations`, `test_handles_missing_sensor_columns_gracefully`.
- [ ] **Step 3: Implement `_parse_fyllo_chart(image_path: Path) -> list[BlockObservation]`** as a separable function. Use `pytesseract` or Gemini Vision for OCR.
- [ ] **Step 4: Implement `FylloConnector(Connector)`** with two modes: (a) manual — `secrets["FYLLO_CHART_DIR"]` set → scan local dir for chart exports; (b) automated — `playwright` login + export. Default to manual mode.
- [ ] **Step 5: Verify unit tests pass.**
- [ ] **Step 6: Add browser integration test** `@pytest.mark.integration_browser`, skipped by default.
- [ ] **Step 7: Commit:** `feat(connectors): Fyllo screen-scrape + OCR connector with manual upload mode`

---

## Task 4: Fasal connector

**Path:** Same constraints as Fyllo. Two sub-paths:
1. Browser automation of `https://app.fasal.co/`.
2. Farmer-shared CSV from app export (preferred — less brittle).

**Files:** Create `src/mangoguard/connectors/fasal.py` + `tests/connectors/fixtures/fasal_export.csv` + `tests/connectors/test_fasal.py`.

**Fasal CSV columns:** `timestamp, plot_id, t_air_c, rh_pct, leaf_wetness_minutes, rain_mm, solar_w_m2, soil_moisture_30cm, soil_moisture_60cm`.

- [ ] **Step 1:** Save a real or synthetic Fasal CSV as fixture.
- [ ] **Step 2: Write failing tests** — `test_csv_yields_expected_row_count`, `test_leaf_wetness_minutes_to_hours`, `test_handles_dst_in_asia_kolkata`.
- [ ] **Step 3: Implement `_parse_fasal_csv(path: Path) -> list[BlockObservation]`** with pandas.
- [ ] **Step 4: Implement `FasalConnector(Connector)`** with `source = ConnectorSource.FASAL, name = "fasal"`. Default mode = CSV-in-directory.
- [ ] **Step 5: Verify tests pass.**
- [ ] **Step 6: Commit:** `feat(connectors): Fasal CSV connector with optional browser automation`

---

## Task 5: Plantix connector (screenshot OCR via Gemini Vision)

**Path:** Farmer shares Plantix diagnosis screenshots. Connector reads a directory of PNG/JPG files and uses Gemini 1.5 Flash Vision to extract: diagnosed disease/pest class, date, location text.

**Auth:** `secrets["GEMINI_API_KEY"]`.

**Mapping:** `block_id` = `"phone_diagnosis"` (Plantix screenshots are device-level, not block-level; user re-tags per block during ingest), `source = PLANTIX`, `plantix_diagnosis_class` = normalized disease label.

**Rate limit:** Gemini free tier = 15 req/min; `time.sleep(4.0)` between calls.

**Structured output:** Define a Pydantic response model `PlantixDiagnosis(diagnosis_class: str, ts: datetime, confidence: float | None)` and use Gemini's structured-output / function-calling mode to force the response shape.

**Files:** Create `src/mangoguard/connectors/plantix.py` + 2 fixture screenshots + `tests/connectors/test_plantix.py`.

- [ ] **Step 1: Save** 2 sample Plantix diagnosis screenshots to fixtures (anthracnose + powdery mildew). Use Plantix public marketing material if no real account access.
- [ ] **Step 2: Write failing tests** with mocked Gemini responses — `test_extracts_anthracnose_label`, `test_extracts_powdery_mildew_label`, `test_handles_unparseable_screenshot_returns_none`.
- [ ] **Step 3: Implement `PlantixConnector(Connector)`** with `source = ConnectorSource.PLANTIX, name = "plantix"`. Inject `genai.Client` for tests.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Add integration test** `@pytest.mark.integration_llm`, skipped unless `GEMINI_API_KEY` set.
- [ ] **Step 6: Commit:** `feat(connectors): Plantix screenshot OCR via Gemini Vision`

---

## Task 6: CSV upload fallback

**Path:** Documented schema CSV any vendor can produce.

**Files:** Create `src/mangoguard/connectors/csv_fallback.py` + `data/csv_fallback_schema.yaml` + `tests/connectors/fixtures/csv_fallback_sample.csv` + `tests/connectors/test_csv_fallback.py`.

**Schema columns:** `block_id, ts_iso, source, t_air_c, rh_pct, leaf_wetness_hr, precip_mm, wind_speed_ms, solar_w_m2, soil_moisture_pct, ndvi, ndre, ndmi, plantix_diagnosis_class, cropsap_pest_pressure, mandi_modal_price_inr_per_quintal, notes`. Required: `block_id, ts_iso, source`. All others optional.

- [ ] **Step 1: Write the schema YAML** documenting every column with type + range + required/optional. This file is the contract the farmer reads.
- [ ] **Step 2: Write failing tests** — `test_loads_valid_csv_yields_observations`, `test_rejects_csv_with_missing_required_columns`, `test_skips_rows_with_invalid_ts_and_logs_warning`.
- [ ] **Step 3: Implement `CSVFallbackConnector(Connector)`** with `source = ConnectorSource.CSV_FALLBACK, name = "csv_fallback"`. Use `pandas.read_csv`. Per-row try/except `ValidationError` → warning + skip.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(connectors): vendor-agnostic CSV fallback connector + schema doc`

---

## Task 7: Connector registry

**Files:** Create `src/mangoguard/connectors/registry.py` + `tests/connectors/test_registry.py`.

Single `get_connector(source: ConnectorSource, ctx: ConnectorContext) -> Connector` factory using `dict[ConnectorSource, type[Connector]]` lookup. All 10 sources registered.

- [ ] **Step 1: Write failing tests** — `test_registry_returns_right_concrete_class_for_each_source`, `test_registry_raises_for_unknown_source`.
- [ ] **Step 2: Implement `get_connector`**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(connectors): connector registry`

---

## Task 8: End-to-end integration test

**Files:** Create `tests/connectors/test_commercial_e2e.py`.

Test loads all 5 commercial connectors (with mocked external deps) into one `FeedStore` and asserts each source contributes ≥1 row.

- [ ] **Step 1: Write the test.**
- [ ] **Step 2: Verify PASS.**
- [ ] **Step 3: Commit:** `test(connectors): end-to-end commercial-stack integration test`

---

## Task 9: Bump version + tag

- [ ] Bump to `0.3.0`, commit, tag `v0.3.0`.

---

## Acceptance criteria for Plan 3 complete

- [ ] All 5 commercial connectors have unit tests with pinned fixtures.
- [ ] Pessl + Plantix have integration tests (skipped without keys).
- [ ] End-to-end test loads all 5 into one FeedStore.
- [ ] Connector registry returns correct class for every `ConnectorSource`.
- [ ] Tagged `v0.3.0`.
