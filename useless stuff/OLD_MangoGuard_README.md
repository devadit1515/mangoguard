---
title: MangoGuard
emoji: 🥭
colorFrom: yellow
colorTo: red
sdk: streamlit
sdk_version: "1.58.0"
app_file: src/mangoguard/app/main.py
pinned: false
license: mit
short_description: Climate- and market-aware pesticide decisions for Indian mango orchards.
---

# 🥭 MangoGuard

**Smarter mango spraying with machine learning and open data.**

A market-conditioned pesticide recommender for mid-sized Konkan Alphonso mango growers. CREST Gold submission, Summer 2026.

## What it does

MangoGuard is an **interoperability + intelligence layer** for Indian mango orchards. It ingests data from monitoring systems the farm already runs (Fyllo, Fasal, Pessl iMETOS, IMD Mausam + Meghdoot, plus free public baselines from AGMARKNET, DBSKKV, CROPSAP, and Sentinel-2 via Google Earth Engine), normalizes everything into a unified `BlockObservation` schema, and produces five outputs:

1. **Disease detector** -- upload a leaf photo, get the class + Grad-CAM heatmap (MobileNetV3-Small fine-tuned on MangoLeafBD + an Alphonso Visit-1 dataset).
2. **Orchard health** -- NDVI/NDRE/NDMI time-series + anomaly detection + seasonal aggregations.
3. **Spray Audit & Recommender** *(focal module)* -- per-block per-segment recommendations that combine a PPI risk engine (anthracnose / powdery mildew / hopper), the CIB&RC registered-pesticide list, the target market's MRL chain, and historical RASFF rejection probability.
4. **Yield + Mandi Price** -- XGBoost regressors over tabular features with SHAP explainability.
5. **AskHapus** -- RAG chatbot grounded in ICAR-CISH, KVK Konkan, DBSKKV, and NHB documents.

The focal contribution is **module 3**: no commercial mango tool combines disease-pressure, MRL, and RASFF history into one per-block per-segment decision. The retrospective backtest + RASFF counterfactual harnesses quantify the win against the ICAR-CISH calendar baseline.

## Repository layout

```
src/mangoguard/
  connectors/        # Plan 2 + 3 -- AGMARKNET, IMD, DBSKKV, CROPSAP, Sentinel-2, Pessl, Fyllo, Fasal, CSV
  risk/              # Plan 4 -- anthracnose HTR, powdery mildew, hopper, PPI combiner, calibration
  recommend/         # Plan 4 -- markets, MRL loader, CIB&RC, RASFF, pesticide metadata, ranker, recommend()
  evaluation/        # Plan 4 -- baseline schedules + retrospective backtest + RASFF counterfactual
  disease_detector/  # Plan 5 -- MobileNetV3 model + data + Grad-CAM + train + infer
  orchard_health/    # Plan 5 -- vegetation index queries + seasonal trend
  yield_price/       # Plan 5 -- XGBoost yield + price + SHAP
  chatbot/           # Plan 5 -- corpus manifest + PDF ingest + RAG with citations
  fieldwork/         # Plan 6 -- visit logbook pydantic models
  app/               # Plan 6 -- Streamlit 6-page dashboard
data/                # YAMLs + CSVs (CIB&RC, MRL tables, RASFF, baseline schedules, chatbot manifest)
notebooks/           # 02 HTR calibration, 05 recommender evaluation
docs/
  superpowers/       # design spec + 6 implementation plans
  report/            # CREST report scaffold + Student Profile Form scaffold
tests/               # 500+ pytest tests
```

## Install (dev)

```bash
pip install -e ".[dev,ml,geo,dashboard,scrape,llm]"
pre-commit install
```

## Run tests

```bash
pytest
```

500+ tests across the seven sub-packages. Live-integration tests (`@pytest.mark.integration`) are gated on API-key environment variables and skip by default.

## Run the Streamlit dashboard

```bash
streamlit run src/mangoguard/app/main.py
```

Six pages: Home (connector status), Disease Detector, Orchard Health, Spray Recommender, Yield + Mandi Price, AskHapus chatbot.

## Read the spec + plans

1. `CLAUDE.md` -- project memory + the verbatim CREST Gold criteria + locked report structure (§9, §9.5, §9.6).
2. `docs/superpowers/specs/2026-05-30-mangoguard-design.md` -- canonical design spec.
3. `docs/superpowers/plans/00-INDEX.md` -- implementation plans index.
4. `docs/report/CREST_REPORT_SCAFFOLD.md` -- the report skeleton; the student's writing target.

## Status

- ✅ `v0.1.0` foundation (schema + FeedStore + Connector ABC)
- ✅ `v0.2.0` free public connectors (AGMARKNET, IMD, DBSKKV, CROPSAP, Sentinel-2)
- ✅ `v0.3.0` commercial connectors (Pessl, Fyllo, Fasal, CSV)
- ✅ `v0.4.0` risk engine + market-conditioned recommender + evaluation harness
- ✅ `v0.5.0` supporting modules (disease detector, orchard health, yield/price, chatbot)
- ✅ `v1.0.0-rc1` Streamlit dashboard + fieldwork logbook + CREST report scaffold

## License

MIT. Project developed with substantial use of Claude (Anthropic); see `docs/report/CREST_REPORT_SCAFFOLD.md` Appendix E for the full AI use disclosure.
