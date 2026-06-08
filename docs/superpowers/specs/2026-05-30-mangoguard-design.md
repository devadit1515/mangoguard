# MangoGuard — Design Specification

**Project:** MangoGuard (working name) — an AI orchard-management & spray-audit system for mid-sized Indian Alphonso mango growers
**Author:** Grade-11 student (sole researcher)
**Duration:** 12 weeks, summer 2026
**Sole deliverable:** CREST Gold Award submission
**Spec date:** 2026-05-30
**Spec status:** awaiting user review; no implementation skill may be invoked until approved

---

## 0. Purpose of this Document

This is the canonical design specification for the MangoGuard project. It is the artifact required by the `superpowers:brainstorming` skill before any implementation work begins. It locks every architectural, data, evaluation, and process decision. Subsequent work (the week-by-week implementation plan) must conform to this spec; deviations are recorded as change-log entries in `CLAUDE.md`.

The companion documents for this project are:
- `CLAUDE.md` — high-level project memory, change log, open decisions
- `CREST_Official_Guidelines_Research.md` — the 15 Gold criteria and what "excellent" looks like
- `CREST_Precedents_And_Patterns.md` — what past good student work looks like and the lessons
- `Mango_Farm_Monitoring_Landscape.md` — landscape of monitoring infrastructure (now historical reference)
- `Monitoring_System_Integration_Options.md` — the API-realism audit that justifies the 5 connectors

Read those before this spec if you are new to the project.

---

## 1. Aim and Sub-Objectives

### 1.1 One-sentence aim *(CREST 1.1)*

> **Design, build, and field-validate an AI decision-support system that ingests data from whichever existing monitoring infrastructure a mid-sized Konkan Alphonso grower already uses, fuses it with public agroclimatic and pest-surveillance data, and produces market-conditioned, MRL-aware pesticide recommendations whose predicted residue-noncompliance risk and per-acre cost are both lower than (a) the cooperating farmer's actual 2026 spray schedule and (b) the canonical ICAR-CISH / KVK Konkan published baseline schedule.**

### 1.2 Six measurable sub-objectives

Each sub-objective maps to a downstream module and to specific CREST criteria.

1. **O1. Interoperability layer.** Build software connectors for five existing monitoring systems (Fyllo, Fasal, Pessl iMETOS, IMD Mausam+Meghdoot, Plantix) plus four free public baselines (AGMARKNET, DBSKKV Dapoli, CROPSAP Maharashtra, Sentinel-2 via GEE) that normalize their disparate outputs into a single unified data schema.
   - *Success metric:* a documented schema (`feeds_schema.yaml`) plus working ingest scripts for ≥3 of the 5 commercial connectors (Fyllo, Fasal, Pessl, IMD, Plantix), tested against ≥1 real sample per connector.
   - *CREST criteria served:* 1.1, 4.1, 4.4.

2. **O2. Disease-risk engine.** Operationalize three published Indian-mango infection-risk models (anthracnose, powdery mildew, mango hopper) on the unified schema, producing a per-block, per-day Pest Pressure Index (PPI).
   - *Success metric:* PPI computable for the cooperating farmer's orchard end-to-end; backtest precision ≥75% on retrospective CROPSAP outbreak data 2018–2024.
   - *CREST criteria served:* 1.4, 3.2, 4.1.

3. **O3. Market-conditioned MRL recommender.** Build a pesticide recommendation engine that filters candidate sprays by destination-market MRL profile (EU/Japan, Gulf/ME, FSSAI, mandi-floor), CIB&RC registration, pre-harvest interval, and historical RASFF rejection patterns.
   - *Success metric:* on a held-out 2024-2025 RASFF mango-rejection set, recommender's residue-noncompliance probability is ≥30% lower than the standard ICAR-CISH/KVK spray schedule for the same disease-pressure profile.
   - *CREST criteria served:* 1.1, 3.1, 4.3.

4. **O4. Disease-detection module (supporting).** Train a MobileNetV3-Small mango leaf-disease classifier on MangoLeafBD, calibrate it on 300–500 original Indian Alphonso photos collected at Visit 1, and produce Grad-CAM explanations for predictions.
   - *Success metric:* ≥85% test accuracy on the held-out Indian Alphonso set after fine-tuning; Grad-CAM heatmaps reviewed and qualitatively approved by the cooperating farmer.
   - *CREST criteria served:* 2.1, 4.1.

5. **O5. Orchard-health dashboard + yield/price estimator (supporting).** Streamlit dashboard that visualizes block-level Sentinel-2 NDVI/NDRE/NDMI time-series, an XGBoost yield-and-price model trained on public AGMARKNET + IMD data, and the AskHapus RAG chatbot over ICAR-CISH/KVK/DBSKKV bulletins.
   - *Success metric:* dashboard demonstrable end-to-end on the cooperating farmer's orchard; chatbot answers 20 pre-defined Alphonso agronomy questions with source citations; yield/price model beats a seasonal-mean baseline by ≥15% MAE.
   - *Scope discipline:* the AskHapus chatbot is the largest single supporting deliverable inside O5. If the connector, disease-detector, or recommender work slips, the chatbot is the *first* item to descope (drop to a "stretch" deliverable) — never the focal Module 3.
   - *CREST criteria served:* 4.3, 4.5.

6. **O6. Field validation + reflection.** Three structured visits to the cooperating farmer's orchard (data collection, mid-trial check, final feedback), plus two structured demos to FPO field officers and two interviews with APEDA-registered exporters. Capture observations, photographs, and structured feedback (SUS-style usability scale + open-ended questions) for the final report.
   - *Success metric:* a logbook of all stakeholder interactions; ≥3 specific stakeholder quotes attributable in the final report.
   - *CREST criteria served:* 2.1, 3.1, 3.3, 4.4.

---

## 2. Wider Purpose *(CREST 1.2)*

The wider purpose is structured to name specific stakeholders, statistics, and policy gaps — per Section 4 lesson #2 of `CREST_Official_Guidelines_Research.md`.

### 2.1 The stakes for Indian mango growers

- India produces ~21 million tonnes of mango per year — ~40% of global supply — yet exports under 1.5% of that. The remaining ~96% is consumed domestically.
- The export gap is largely driven by **residue compliance failures**: India is the #1 source country in the EU's RASFF pesticide-rejection database (~18.1% of all notifications). Repeatedly cited residues on Konkan Alphonso: Imidacloprid, Cypermethrin, Quinalphos, Hexaconazole.
- Each rejected export consignment represents ₹3–8 lakh in direct loss to the packing exporter, with downstream losses to the contract growers.
- Domestic risk is rising too: FSSAI residue surveillance is expanding; organized retail (Reliance Fresh, DMart, Big Basket) and processors (Maaza, Frooti, Slice — all major Alphonso-pulp buyers) increasingly residue-test suppliers and blacklist non-compliant ones.

### 2.2 Why current tools don't solve this

- **ICAR-CISH and KVK extension advisories** publish blanket spray schedules per crop per district. They do not condition recommendations on the grower's target market segment (export-EU vs domestic-mandi), so the same advice goes to a Tokyo-bound consignment and a Vashi-mandi consignment.
- **Commercial agri-IoT (Fyllo, Fasal, Pessl)** provides excellent farm-microclimate data but bundles it with vendor-specific disease alerts that do not integrate MRL filtering, RASFF history, or destination-market constraints.
- **Phone apps (Plantix)** identify diseases but make no spray recommendation; if they do, it is not market-conditioned.
- **No existing tool — commercial or academic — integrates monitoring-system data, disease-risk modeling, and market-conditioned MRL filtering for Indian mango.** This is verified white space (see `CREST_Precedents_And_Patterns.md` lesson 9).

### 2.3 Beneficiaries

| Tier | Group | Scale | Direct or Indirect |
|---|---|---|---|
| Primary user | Mid-sized Konkan Alphonso grower (5–20 acres) | ~30–50k in Konkan | Direct |
| Secondary user | FPO/cooperative field officers (e.g., Devgad Mango Growers, Ratnagiri cooperatives) | ~30–60 FPOs in Konkan, each serving 100–500 farmers | Direct (force-multiplier role) |
| Indirect beneficiaries | Smallholder Alphonso growers served by these FPOs | ~30–50k farmers indirectly | Indirect (via FPO adoption) |
| Stakeholder validators | APEDA-registered exporters (~150 nationally) | n/a | Validator (interview source for the report) |
| Policy-level | APEDA, FSSAI, ICAR-CISH | n/a | Policy implications discussed in Section 5 of the report |

---

## 3. Range of Approaches Considered *(CREST 1.3)*

Three architectural approaches were evaluated before settling on the chosen design.

### Approach A — Pure-CV-only (rejected)

A mobile-friendly mango disease classifier (MangoLeafBD + transfer learning) as the sole research contribution.

| Pro | Con |
|---|---|
| Saturated leaderboard means strong baselines exist | DenseNet201 already hits 99.33% on MangoLeafBD — no publishable accuracy gain |
| Low data-collection burden | No real-world impact lever — predicting disease ≠ preventing it |
| Standard student-project shape | JEI March-2026 rule rejects pure-CS / public-data-only; even though we are CREST-only, the work is still weak by CREST 4.3 (creativity) |

**Rejected** because the contribution is not novel and does not address the actual problem (overspraying / residue noncompliance).

### Approach B — Rule-based MRL recommender (rejected)

A spreadsheet-style lookup of "given disease X and target market Y, recommend pesticide Z" sourced from CIB&RC and country MRL lists.

| Pro | Con |
|---|---|
| Computationally trivial | Does not need ML — student project looks small |
| Genuinely novel for Indian mango | No method↔result link (CREST 3.2) — a lookup table is not an experiment |
| Easy to validate against RASFF data | Cannot react to real-time disease pressure; recommends same thing every time |

**Rejected** because it lacks ML method depth and cannot integrate live farm-state inputs.

### Approach C — Hybrid intelligence-layer over existing monitoring (CHOSEN)

Build an interoperability layer that ingests data from existing on-farm monitoring systems (the 5 connectors), fuses with public agroclimatic + pest-surveillance data, runs published disease-risk models to compute Pest Pressure Index per block, and outputs market-conditioned MRL-aware recommendations. Disease detection becomes one supporting module, not the focal claim.

| Pro | Con |
|---|---|
| Novel: no commercial or academic tool does this for Indian mango | Higher engineering surface area (5 connectors + 5 modules) |
| Real method↔result links via tier-coverage analysis | Depends on connector data availability — fallback to free public baselines if commercial systems unavailable |
| Operates on published agronomy models (anthracnose R² = 0.93), not invented ML | Some connectors lack public APIs — Fyllo/Fasal require app-login scrape (engineering risk) |
| Each connector teaches different skills — strong CREST 4.1 / 4.4 evidence | Requires ~70-110 hrs of connector work alone |

**Chosen.** Approach C is the only design that simultaneously satisfies the novelty requirement (CREST 4.3), the methodological-rigor requirement (CREST 3.2, 4.1), the wider-purpose requirement (CREST 1.2 — real users with a real problem), and the integration-across-techniques requirement (CREST 4.4).

### A secondary design choice within Approach C — install hardware or not (rejected hardware)

Within Approach C, an earlier iteration of the design called for installing a ~₹13k DIY ESP32 station (with leaf-wetness sensor) on the cooperating farmer's orchard. This was rejected on 2026-05-30 in favor of pure software interoperability for the following reasons:

1. The cooperating farmer's target persona (rich, mid-sized, partially absentee Konkan Alphonso owner) plausibly already has a commercial monitoring system (Fyllo / Fasal / Pessl). Installing new hardware would be redundant.
2. Hardware introduces deployment risk (install during monsoon, battery failure, vandalism, sensor drift) that the 12-week timeline cannot absorb.
3. The interoperability-layer story is more deployable across the Konkan FPO ecosystem (every member farm has a different setup; MangoGuard normalizes them all) and stronger for college application essays.

---

## 4. Plan & Methodology *(CREST 1.4)*

### 4.1 System architecture

```
                                         ┌────────────────────────────┐
                                         │  Streamlit Dashboard (UI)  │
                                         └────────────┬───────────────┘
                                                      │
       ┌──────────────────────────────────────────────┼──────────────────────────────────────────────┐
       │                                              │                                              │
       ▼                                              ▼                                              ▼
┌──────────────┐                       ┌─────────────────────────────┐                       ┌──────────────┐
│  Module 1    │                       │   Module 3 (FOCAL)          │                       │  Module 5    │
│  Disease     │                       │   Spray Audit & Recommender │                       │  AskHapus    │
│  Detector    │                       │                             │                       │  RAG Chatbot │
│  (MobileNet  │                       │  ┌───────────────────────┐  │                       │  (LangChain  │
│   V3-Small + │                       │  │  Disease-Risk Engine  │  │                       │   + Chroma)  │
│   Grad-CAM)  │                       │  │  (anthracnose HTR,    │  │                       └──────┬───────┘
└──────┬───────┘                       │  │   powdery mildew RH,  │  │                              │
       │                               │  │   hopper × CROPSAP)   │  │                              │
       │                               │  └───────────┬───────────┘  │                              │
       │                               │              │              │                              │
       │     ┌─────────────────┐       │  ┌───────────▼───────────┐  │       ┌─────────────────┐    │
       │     │  Module 2       │       │  │ Pest Pressure Index   │  │       │  Module 4       │    │
       │     │  Orchard Health │◀──────│  │ (per block, per day)  │  │──────▶│  Yield + Price  │    │
       │     │  Dashboard      │       │  └───────────┬───────────┘  │       │  Estimator      │    │
       │     │  (Sentinel-2    │       │              │              │       │  (XGBoost on    │    │
       │     │   NDVI/NDRE)    │       │  ┌───────────▼───────────┐  │       │   AGMARKNET +   │    │
       │     └────────┬────────┘       │  │  MRL Recommender      │  │       │   IMD + NDVI    │    │
       │              │                │  │  (CIB&RC × Market MRL │  │       │   integral)     │    │
       │              │                │  │   × PHI × RASFF hist) │  │       └────────┬────────┘    │
       │              │                │  └───────────────────────┘  │                │             │
       │              │                └─────────────┬───────────────┘                │             │
       │              │                              │                                │             │
       │              └──────────────────────────────┼────────────────────────────────┘             │
       │                                             │                                              │
       │                                             ▼                                              │
       │                          ┌───────────────────────────────────┐                             │
       └──────────────────────────│   Unified Data Schema (feeds.db)  │◀────────────────────────────┘
                                  └─────────────────┬─────────────────┘
                                                    │
       ┌────────────────────────────────────────────┼─────────────────────────────────────────────┐
       │                                            │                                             │
       ▼ Commercial connectors (when present)       ▼ Free public baselines (always-on)           ▼
 ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
 │  Fyllo       │  │  Fasal       │  │  Pessl       │    │  AGMARKNET   │  │  IMD Mausam  │  │  DBSKKV      │
 │  (scrape)    │  │  (scrape)    │  │  (HMAC API)  │    │  (data.gov.in)│ │  Meghdoot    │  │  Dapoli      │
 └──────────────┘  └──────────────┘  └──────────────┘    └──────────────┘  └──────────────┘  └──────────────┘
                                                                  │                  │              │
                                                          ┌──────────────┐  ┌──────────────┐
                                                          │  CROPSAP     │  │  Sentinel-2  │
                                                          │  (scrape)    │  │  (GEE)       │
                                                          └──────────────┘  └──────────────┘
       ┌──────────────────────────────────────────────────────────────────────────────────────────┐
       │                                                                                          │
       ▼ Phone-app-side connector                                                                  ▼ Manual fallback
 ┌──────────────┐                                                                          ┌──────────────┐
 │  Plantix     │                                                                          │  CSV upload  │
 │  (screenshot │                                                                          │  (any vendor │
 │   + Vision-  │                                                                          │   no API)    │
 │   LLM OCR)   │                                                                          └──────────────┘
 └──────────────┘
```

### 4.2 Data flow

1. Daily / hourly: each connector pulls its native data into a per-connector raw table in `feeds.db` (SQLite for v1; portable, single-file, no server).
2. A normalization layer (`normalize.py`) maps each connector's raw schema into a unified per-block-per-timestamp schema with fields: `block_id, ts, t_air_C, rh_pct, leaf_wetness_hr, precip_mm, ndvi, ndre, ndmi, dominant_pathogen_signal, plantix_diagnosis_class, ...`.
3. The disease-risk engine (`risk.py`) reads the unified schema, applies the published infection-risk equations, and writes a per-block-per-day PPI to a `ppi` table.
4. When `PPI(block, day) > threshold`, the recommender (`recommend.py`) computes ranked pesticide candidates filtered by target-market MRL (the user selects per block per season), CIB&RC registration, PHI (pre-harvest interval), and historical RASFF rejection probability.
5. The Streamlit dashboard renders modules 1–5 with shared access to `feeds.db`.

### 4.3 Module-level design specifications

#### Module 1 — Disease Detector

- **Model:** MobileNetV3-Small backbone, ImageNet-pretrained, fine-tuned on MangoLeafBD (8 classes). Custom head: GlobalAveragePooling2D → Dense(256, ReLU) → Dropout(0.5) → Dense(N, softmax).
- **Calibration:** Visit-1 dataset of 300–500 Indian Alphonso leaf photos labeled across 4–6 classes (anthracnose, powdery mildew, mango hopper damage, sooty mould, healthy, ± fruit-fly damage). Two-phase fine-tuning: Phase 1 (head only, Adam 1e-3, 5 epochs); Phase 2 (full unfreeze, Adam 1e-5, 15 epochs, early-stopping patience 5).
- **Explanation:** Grad-CAM++ (with GradientTape fallback for tf-keras-vis version issues) per prediction.
- **Output:** disease class probability vector + saliency heatmap, written to a Streamlit panel.
- **Why MobileNetV3-Small, not DenseNet201:** the SOTA is saturated; we explicitly choose efficiency over peak accuracy so the model is deployable on entry-level Android (Redmi 10A) and we discuss the trade-off in Section 5 of the report. This serves CREST 1.3 (range of approaches).

#### Module 2 — Orchard Health Dashboard

- **Data source:** Sentinel-2 L2A via Google Earth Engine, 10m resolution, 5-day revisit cadence.
- **Indices:** NDVI, NDRE, NDMI computed per block (orchard subdivided into 4–8 polygons by GPS walk during Visit 1).
- **Monsoon fallback:** Sentinel-1 SAR (VV/VH backscatter) for July–August when Western Ghats cloud cover is 90–92% and Sentinel-2 is mostly blacked out.
- **Visualization:** block-level time-series with seasonal overlays for 2023, 2024, 2025; pixel-level alerts intentionally not surfaced because 10m × 10m pixel + overlapping mango crowns make per-pixel claims unreliable.
- **Purpose:** lets the absentee owner verify orchard health remotely; also visually striking for a "show off to friends" use case.

#### Module 3 — Spray Audit & Recommender *(FOCAL)*

##### 3a. Connector layer

| Connector | Integration | Effort | Status |
|---|---|---|---|
| Fyllo | Farmer-app-login screen-scrape + chart-export OCR | 20–30 hrs | Build speculatively against public app screenshots; reach out to sales@fyllo.in for student demo data |
| Fasal | Farmer-app-login screen-scrape + farmer-shared CSV | 20–30 hrs | Same — speculative build, reach out to connect@wolkus.com |
| Pessl iMETOS / FieldClimate | Public REST API v2 + HMAC auth, SatAgro Python client | 6–10 hrs | Build against public FieldClimate demo station immediately; farmer's HMAC keys if available are bonus |
| IMD Mausam + Meghdoot agromet | Public REST API (email-whitelist via sankar.nath@imd.gov.in) + scrape Marathi PDF bulletins | 8–12 hrs | Apply for API whitelist Week 1 |
| Plantix | Farmer-shared screenshot history + Vision-LLM OCR parse (Gemini 1.5 Flash free tier or local Llava-via-Ollama) | 15–25 hrs | Collect synthetic test screenshots from Plantix marketing material |

Plus four free public baselines (always-on, lightweight scrape):
- **AGMARKNET / data.gov.in** — daily mango mandi prices (Vashi, Ratnagiri, Devgad, Vengurla), free API key.
- **DBSKKV Dapoli** — Konkan-tuned microclimate, climate-trend PDFs (Konkan domain authority).
- **CROPSAP Maharashtra** — taluka-level pest-surveillance (HTML scrape; no public API).
- **Sentinel-2 NDVI/NDRE block-level via GEE** — also used by Module 2.

Total connector effort: ~70–110 hrs (~6–9 hrs/week of connector work across 12 weeks).

##### 3b. Disease-risk engine

Three published Indian-mango disease-risk models, operationalized (not invented):

| Pathogen | Model | Inputs | Source |
|---|---|---|---|
| Anthracnose (*Colletotrichum gloeosporioides*) | HTR-based logistic regression (R² = 0.93 published) | T_air, RH_morning, wind, sunshine, leaf-wetness duration | Akem 2006; corroborated in `Mango_Farm_Monitoring_Landscape.md` C-section |
| Powdery mildew (*Oidium mangiferae*) | Temperature-band × RH-window threshold rule + ICAR forewarning logistic regression | T_min 11–14°C, T_max 17–31°C, RH 40–72% | NHB technical bulletin + ICAR forewarning paper |
| Mango hopper (*Idioscopus spp.*) | CROPSAP regional taluka-level pressure × local microclimate multiplier | CROPSAP taluka pest-count, T_air | CROPSAP / NCIPM |

The combined per-block, per-day Pest Pressure Index is:

```
PPI(block, day) =
  w_anth · score_anthracnose(weather, leaf_wetness, ndre_anomaly)
+ w_pm   · score_powdery_mildew(t_min, t_max, rh)
+ w_hop  · score_hopper(cropsap_taluka_pressure, t_air)
```

Weights `w_anth, w_pm, w_hop` are calibrated against the cooperating farmer's 2025 season log (if available) or against the 2018–2024 retrospective CROPSAP archive (always available). The weights are *fitted to one orchard*, not claimed as universal.

##### 3c. Market-conditioned MRL recommender

Market segments (user picks per block per season):

| Segment | Share | MRL profile |
|---|---|---|
| Export — EU/Japan/US | ~1–2% | Strictest. EU MRL often 0.01 mg/kg. RASFF historical rejection prior. |
| Export — Gulf/ME/SE Asia | ~2–3% | Codex MRLs. |
| Domestic — organized retail & processors (Reliance, DMart, Big Basket, Maaza, Frooti, Slice) | ~25–30% | FSSAI + buyer-specific stricter. |
| Domestic — traditional mandi & wholesale | ~60–65% | FSSAI floor. |

Recommender flow:

1. If `PPI(block, day) > threshold` → flag the block.
2. Pull effective pesticides for the dominant predicted pathogen from CIB&RC registered list.
3. Filter by selected target market's MRL list (build a lookup table from public PDFs: EU pesticide database, Japan MHLW positive list, FSSAI MRLs).
4. Filter by pre-harvest interval (PHI) given days-to-harvest.
5. Rank by `(efficacy_score) / (residue_half_life_days × cost_per_acre_INR)` — higher efficacy is better, *lower* residue half-life is better (faster clearance from fruit), *lower* cost-per-acre is better. Log-transform each factor for numerical stability.
6. For export-market recommendations, additionally compute a RASFF historical rejection probability for the chosen pesticide × destination pair.
7. Output JSON-structured recommendation rendered in the Streamlit dashboard:

```json
{
  "block": "B3",
  "date": "2026-07-12",
  "ppi": 87,
  "primary_pathogen": "anthracnose",
  "target_market": "EU export",
  "recommendation": {
    "pesticide": "Hexaconazole 5 EC",
    "dose": "2 ml/L",
    "phi_days": 30,
    "harvest_date_constraint": "no harvest before 2026-08-11",
    "expected_rasff_rejection_p": 0.04,
    "alternatives": ["Difenoconazole 25 EC", "Mancozeb 75 WP"]
  }
}
```

#### Module 4 — Yield & Mandi-Price Estimator

- **Yield model:** XGBoost regressor on per-block tabular features:
  - Block acreage, tree count, mean tree age
  - Season-integrated NDVI (mean NDVI across April–June)
  - Season-aggregated weather (cumulative GDD, total rainfall, mean RH)
  - Soil indices from SoilGrids 250m
  - Lagged previous-season yield if known
- **Price model:** XGBoost or attention-based model on AGMARKNET 2001–2025 mango price history per mandi, with weather + arrival-volume features. Reference: PLOS ONE 2024 mango-price-prediction paper (R² = 0.873 with hybrid ETS+SVM).
- **Output:** per-block yield forecast + expected mandi price at harvest week + total expected revenue.
- **Baseline:** seasonal-mean price for the matched mandi and matched ISO week. Success metric: ≥15% MAE improvement over baseline.

#### Module 5 — AskHapus RAG Chatbot

- **Corpus:** ICAR-CISH mango IPM bulletins, KVK Konkan pamphlets, DBSKKV Dapoli technical guides, NHB mango handbook (~50–100 PDFs).
- **Pipeline:** PDF text extraction (pdfplumber + Tesseract for scanned PDFs) → chunking (1000 tokens, 200 overlap) → embedding (Gemini text-embedding-004 free tier OR local nomic-embed-text via Ollama) → ChromaDB vector store → LangChain RAG prompt → Gemini 1.5 Flash (15 req/min free) or local Llama-3-8B-Instruct.
- **Languages:** English, Marathi, Hindi (let the LLM translate; verify with the cooperating farmer at Visit 2).
- **Source citations:** every chatbot response must cite the source PDF + page. Hallucinated agronomy is an automatic failure.

### 4.4 Repository & deliverables structure

```
CREST_Research/
├── CLAUDE.md                                       (project memory; auto-loaded)
├── CREST_Official_Guidelines_Research.md           (15 criteria, AI policy)
├── CREST_Precedents_And_Patterns.md                (16 papers mined, lessons)
├── Mango_Farm_Monitoring_Landscape.md              (historical reference)
├── Monitoring_System_Integration_Options.md        (5-connector justification)
│
├── docs/
│   ├── superpowers/specs/
│   │   └── 2026-05-30-mangoguard-design.md         (THIS FILE)
│   ├── crest_report/
│   │   ├── 00_outline.md
│   │   ├── 01_introduction.md
│   │   ├── 02_literature_review.md
│   │   ├── 03_methodology.md
│   │   ├── 04_results.md
│   │   ├── 05_discussion.md
│   │   ├── 06_conclusion.md
│   │   ├── 07_personal_reflection.md
│   │   ├── 08_references_harvard.md
│   │   ├── appendix_a_gantt.md
│   │   ├── appendix_b_risk_assessment.md
│   │   ├── appendix_c_ai_use_disclosure.md
│   │   ├── appendix_d_raw_data.md
│   │   ├── appendix_e_farmer_feedback.md
│   │   └── appendix_f_logbook.md
│   ├── student_profile_form/
│   │   ├── part_a_criteria_evidence_index.md
│   │   └── part_b_personal_reflection.md
│   └── stakeholder_interviews/
│       ├── farmer_visit_1.md
│       ├── farmer_visit_2.md
│       ├── farmer_visit_3.md
│       ├── fpo_officer_1.md
│       ├── fpo_officer_2.md
│       ├── exporter_1.md
│       └── exporter_2.md
│
├── src/
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── base.py                                 (Connector ABC + unified schema)
│   │   ├── fyllo.py
│   │   ├── fasal.py
│   │   ├── pessl.py
│   │   ├── imd.py
│   │   ├── plantix.py
│   │   ├── agmarknet.py
│   │   ├── dbskkv.py
│   │   ├── cropsap.py
│   │   ├── sentinel2_gee.py
│   │   └── csv_fallback.py
│   ├── normalize.py
│   ├── risk/
│   │   ├── anthracnose.py
│   │   ├── powdery_mildew.py
│   │   └── hopper.py
│   ├── recommend/
│   │   ├── mrl_loader.py                           (parse EU / Japan / FSSAI MRL PDFs)
│   │   ├── cibrc.py                                (parse CIB&RC registered list)
│   │   ├── rasff.py                                (RASFF historical rejection probabilities)
│   │   └── rank.py
│   ├── disease_detector/
│   │   ├── train.py
│   │   ├── infer.py
│   │   └── gradcam.py
│   ├── yield_price/
│   │   ├── yield_xgb.py
│   │   └── price_xgb.py
│   ├── chatbot/
│   │   ├── ingest.py
│   │   └── rag.py
│   ├── dashboard/
│   │   ├── app.py                                  (Streamlit entry-point)
│   │   ├── pages/
│   │   │   ├── 1_disease_detector.py
│   │   │   ├── 2_orchard_health.py
│   │   │   ├── 3_spray_recommender.py
│   │   │   ├── 4_yield_price.py
│   │   │   └── 5_askhapus.py
│   │   └── components/
│   └── feeds/
│       └── feeds.db                                (SQLite, .gitignore'd)
│
├── data/
│   ├── raw/                                        (.gitignore'd)
│   ├── processed/                                  (.gitignore'd)
│   ├── alphonso_visit1/                            (300–500 leaf photos)
│   ├── mrl_tables/
│   │   ├── eu.csv
│   │   ├── japan.csv
│   │   └── fssai.csv
│   ├── baseline_schedules/
│   │   ├── icar_cish_mango_2023.yaml             (canonical ICAR-CISH baseline)
│   │   └── kvk_konkan_alphonso_2025.yaml         (latest Konkan KVK advisory)
│   ├── feeds_schema.yaml                          (unified per-block-per-ts schema)
│   └── rasff_mango_rejections.csv
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_anthracnose_htr_calibration.ipynb
│   ├── 03_disease_detector_training.ipynb
│   ├── 04_yield_price_model.ipynb
│   ├── 05_recommender_evaluation.ipynb
│   └── 06_field_validation.ipynb
│
├── tests/
│   ├── connectors/
│   ├── risk/
│   ├── recommend/
│   └── e2e/
│
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

### 4.5 Tech stack and tools

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.11 | Standard for the data-science + ML + scraping work |
| Dashboard | Streamlit | JSR HS precedent (drought-prediction Streamlit app), low setup, free hosting on Streamlit Community Cloud |
| Database | SQLite (single file, `feeds.db`) | Zero-config, portable, sufficient for one orchard's worth of data |
| ML training | PyTorch 2.x | User's existing CNN experience is in PyTorch |
| ML serving | TF-Lite for the disease detector (cross-platform inference) | Mobile-friendly even though v1 is browser-only |
| Geospatial | Google Earth Engine Python API, `geemap`, `rasterio` | GEE is the standard free Sentinel-2 access path |
| LLM | Gemini 1.5 Flash free tier (15 req/min) for the chatbot + screenshot OCR | Generous free tier, multimodal (vision for Plantix screenshots), Marathi/Hindi fluent |
| Vector DB | ChromaDB local | Free, local file, no server |
| Web scraping | `requests` + `selenium` + `playwright` | Fyllo/Fasal app scraping likely needs full browser automation |
| OCR | Tesseract + Gemini Vision | Tesseract for English PDFs, Gemini for Plantix screenshot diagnosis text |
| PDF extraction | `pdfplumber` + `pymupdf` | Standard combo for layout-preserving text + scanned-page OCR |
| Tabular ML | XGBoost 2.x + SHAP for interpretability | Standard, fast, well-supported |
| Hyperparameter | None — keep it simple | Default + small grid search; we are not benchmarking models |
| Code quality | `ruff` + `pytest` | Light formatter + testing |
| Versioning | git + GitHub (private during development, public at submission) | Standard |
| Drive backups | Google Drive sync of `data/raw` | Colab session-timeout safety |
| Compute | Google Colab Pro free T4 | Sufficient for MobileNetV3-Small fine-tuning |

### 4.6 Evaluation methodology

#### 4.6.1 Disease-risk engine retrospective evaluation

- **Source data:** 2018–2024 Konkan weather archive (Open-Meteo ERA5 + IMD gridded) and 2018–2024 CROPSAP outbreak records for Ratnagiri / Sindhudurg talukas.
- **Method:** for each week 2018–2024, compute PPI from the weather alone; check whether high-PPI weeks correlate with CROPSAP-reported anthracnose / powdery-mildew / hopper outbreaks 0–14 days later.
- **Metric:** precision-recall on weekly outbreak prediction; ROC-AUC; Brier score.
- **Baselines:** (a) seasonal mean (always-predict-high in monsoon, always-low otherwise); (b) ICAR-CISH crop-calendar advisory (encoded as a deterministic spray-recommended-yes/no per ISO week).

#### 4.6.2 Disease-risk engine prospective evaluation (one farm, 12 weeks)

- **Setup:** Visit 1 establishes the GPS-bounded orchard polygon, blocks (4–8 polygons), pesticide-cabinet inventory, and any past-2-season spray records.
- **Run:** weeks 2–11, daily PPI computed and weekly summary sent via WhatsApp to the farmer.
- **Mid-trial check (Visit 2, week 6–7):** photograph all blocks; verify whether high-PPI blocks have higher visible disease incidence than low-PPI blocks. This is the *eyes-on-the-orchard* falsification step.
- **End-trial (Visit 3, week 11):** collect actual spray log; compare to model-recommended schedule; compute hypothetical-savings (number of recommended sprays not taken / number of actual sprays not recommended) + structured feedback.

#### 4.6.3 Market-conditioned MRL recommender evaluation

- **Source data:** RASFF 2010–2025 mango notifications (~150–300 records expected).
- **Method:** for each historical rejection, reconstruct the spray decision that would have been needed to avoid it (work backwards from the violating active ingredient + the export destination's MRL list). Then check: would MangoGuard's recommender for that destination + that disease pressure have produced a non-violating recommendation?
- **Metric:** counterfactual prevention rate (% of RASFF rejections that MangoGuard's recommendation would have avoided).
- **Baseline:** the canonical ICAR-CISH "Mango Production Technology" 2023 handbook spray schedule plus the latest KVK Konkan Alphonso advisory (both pinned to specific PDFs in `data/baseline_schedules/`), neither destination-conditioned.
- **Success threshold:** ≥30% relative improvement.

#### 4.6.4 Disease-detector evaluation

- **Test set:** 20% held-out from the Visit-1 Indian Alphonso dataset; *not* from MangoLeafBD (avoid lab-condition bias).
- **Metrics:** test accuracy, macro F1, per-class precision-recall, confusion matrix, Grad-CAM qualitative review by the cooperating farmer.

#### 4.6.5 Stakeholder validation

Three farmer visits + two FPO demos + two exporter interviews. Each meeting captured in `docs/stakeholder_interviews/` with:

- Date, location, attendees
- Photos with explicit consent
- SUS (System Usability Scale, 10-question Likert) for the demo
- 5 open-ended questions (what's confusing, what's missing, would-you-use-it, would-you-pay-for-it, what-would-you-change)
- 3 quotable lines marked for use in the report

### 4.7 Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Farmer cancels / unreachable | Low–Med | Critical | Identify a backup farmer (one FPO contact); pivot to "FPO field officer as user" if needed |
| Fyllo/Fasal scrape blocked by app changes | High | Low | They are 2 of 5 connectors; tool still works without them |
| IMD API whitelist denied | Med | Low | PDF agromet bulletin scrape works without API |
| Monsoon cloud blackout (July–Aug) blanks Sentinel-2 | Certain | Med | Sentinel-1 SAR fallback (explicit plan, see §4.3 Module 2) |
| MangoLeafBD → Indian Alphonso domain shift | Certain | Med | Original-data fine-tuning explicitly handles this; quantified in Module 1 evaluation |
| Visit-1 disease-photo collection compromised by bad weather | Low | High | Schedule Visit 1 in week 1–2 (dry season); collect from multiple trees per block; minimum 50 photos per class |
| RASFF data sparse for mango | Low | Med | Combine with FDA Import Refusals + Japan MHLW notifications |
| LLM rate limit hit on Gemini free tier | Low | Low | Fall back to local Llama-3-8B via Ollama; both prepared |
| Streamlit Community Cloud RAM (1 GB) too small | Med | Low | Reduce model to TF-Lite; offload disease inference to a Hugging Face Spaces free instance |
| Compute deadline pressure in week 11 | Med | Med | Front-load training and inference in weeks 5–8; week 11 is for report writing only |
| Plantix screenshot OCR unreliable | Med | Low | Diagnosis history is *enrichment* not core data; we don't depend on it for Module 3 recommendations |

---

## 5. Time Plan & Gantt *(CREST 1.5)*

Twelve weeks at ~70+ hours total. Allocation tilts toward connector engineering (~70–110 hrs is the dominant cost) and report writing (~30 hrs reserved hard in weeks 11–12).

| Week | Focus | Deliverables | CREST evidence accrued |
|---|---|---|---|
| **1** | Setup & Visit 1 logistics | Repo created, environment set up, MRL tables scraped (EU + Japan + FSSAI), CIB&RC list scraped, IMD API whitelist applied, farmer contacted, Visit 1 scheduled, RASFF historical pull initiated | 1.5, 2.1, 2.2, 4.2 |
| **2** | Visit 1 + connectors batch A | Visit 1 executed: 300–500 leaf photos collected & labeled, GPS polygon recorded, spray records / cabinet inventory captured, monitoring-stack confirmed. Connectors: AGMARKNET + DBSKKV + IMD all running | 2.1, 4.4 |
| **3** | Connectors batch B + disease-risk engine | Connectors: CROPSAP + Sentinel-2/GEE + Pessl (demo data). Anthracnose HTR + powdery mildew threshold rules coded; per-block-per-day PPI pipeline runs end-to-end on free public data | 4.1, 4.4 |
| **4** | Connectors batch C + disease detector training | Connectors: Fyllo speculative scrape + Fasal speculative scrape + Plantix screenshot OCR. Disease detector Phase 1 + Phase 2 training on MangoLeafBD, fine-tuning on Visit-1 Indian Alphonso set | 4.1, 4.3 |
| **5** | Retrospective evaluation + recommender v1 | Retrospective PPI vs CROPSAP 2018–2024; first version of MRL recommender with EU MRL filter; CIB&RC integration done | 3.2, 4.1 |
| **6** | RASFF counterfactual evaluation + yield/price | RASFF prevention-rate evaluation; XGBoost yield + price models trained and validated | 3.2, 4.1, 4.3 |
| **7** | Visit 2 (mid-trial) + chatbot | Visit 2 executed: mid-trial photographs, verify PPI-flagged blocks have higher visible disease incidence than control blocks. AskHapus RAG chatbot working end-to-end with source citations | 2.1, 4.3, 4.4 |
| **8** | Orchard-health dashboard + integration | Sentinel-2 NDVI/NDRE/NDMI per-block time-series ingested; Module 2 dashboard panel done; all 5 modules wired into Streamlit app | 4.1, 4.5 |
| **9** | FPO demos + exporter interviews | Two FPO officer demos (Devgad / Ratnagiri cooperatives); two APEDA-registered exporter interviews. SUS surveys captured. Open-ended feedback logged | 2.1, 3.1, 3.3 |
| **10** | Visit 3 (final) + iteration | Visit 3 executed: final harvest inspection, actual spray log collected, hypothetical-savings computed, farmer's structured feedback captured. Bug-fixes from FPO/exporter feedback merged | 2.1, 3.1, 3.2, 3.3 |
| **11** | Report writing (focal week) | Sections 1–4 of the CREST report drafted (Introduction, Literature Review, Methodology, Results); all 10 figures and Table 1 generated | 4.5 |
| **12** | Final report + submission | Sections 5–7 drafted (Discussion, Conclusion, Personal Reflection); Student Profile Form Part A + Part B completed; AI Use Statement finalized; final PDF generated; submitted via apply.crestawards.org | 3.3, 4.5 |

A planned-vs-actual Gantt chart (Appendix A of the final report) will track real progress against this plan with at least one documented slippage per CREST best practice.

---

## 6. CREST Gold Criteria Evidence Map *(CREST 4.5)*

Mapping the 15 criteria to the artifact that evidences each (also goes verbatim into the Student Profile Form Part A).

| # | Criterion | Where in the deliverables | Acceptable→Excellent move |
|---|---|---|---|
| 1.1 | Clear aim + objectives | §1.1 one-sentence aim + §1.2 six numbered sub-objectives, each with a measurable success metric | Excellent: each objective has a success metric *and* maps to a downstream module + CREST criterion |
| 1.2 | Wider purpose | §2 names specific stakeholders (Konkan FPOs, APEDA exporters, ICAR-CISH), real statistics (RASFF #1 source country, 18.1%), specific blacklisted residues | Excellent: stakeholders are named (Devgad Mango Growers, specific exporters interviewed) not generic |
| 1.3 | Range of approaches | §3 explicitly compares Approach A (pure CV), B (rule-based), C (chosen hybrid). Also includes the hardware-vs-software sub-choice within Approach C | Excellent: rejected approaches have written trade-off tables |
| 1.4 | Plan description | §4 contains module-level architecture, data flow, repo tree, tech stack, evaluation methodology | Excellent: every design choice (e.g., MobileNetV3-Small over DenseNet201) is justified in writing |
| 1.5 | Time organization | §5 week-by-week table; Appendix A of report = planned-vs-actual Gantt with at least one documented slippage | Excellent: real slippage shown (one inevitable delay, e.g., Visit 2 rescheduled due to monsoon) |
| 2.1 | Materials & people | §4.5 lists every API, library, dataset by name; §4.6.5 lists stakeholder interviews; Appendix D of report logs every data source | Excellent: farmer name + FPO names + ICAR-CISH paper authors all credited |
| 2.2 | Background research | §2.2 + Literature Review section of report; draws from `CREST_Precedents_And_Patterns.md` (16 mined papers) | Excellent: paragraph-of-synthesis with critical evaluation, gap identification at the end (per CREST_Official_Guidelines_Research.md Section 4) |
| 3.1 | Conclusions + wider implications | Discussion section of report explicitly addresses: implications for Konkan growers, FPO scaling, APEDA policy on MRL gating, FSSAI domestic enforcement | Excellent: implications are concrete (named stakeholder + specific action), not general |
| 3.2 | Method ↔ result link | Three explicit method→result connections in Discussion §5.4: (a) connector-coverage tier vs disease-risk precision; (b) RASFF counterfactual prevention rate; (c) Visit-2 PPI-vs-visible-disease correlation | Excellent: connections are quantified, not just asserted |
| 3.3 | Learning + reflection | Personal Reflection section (~400 words, written individually) + 3 future-work directions | Excellent: reflection is specific (which exact bug taught what), not generic |
| 4.1 | Scientific understanding | Methodology section explains: HTR for anthracnose, NDVI/NDRE biophysics, transfer learning, MRL pharmacology (residue half-life, PHI), Grad-CAM++ math reference | Excellent: equations/mechanisms not just labels |
| 4.2 | Ethics & safety | Appendix B Risk Assessment (pesticide safety, data privacy of farmer photos, dual-use concerns, AI-fabrication risk, recommendation-error harm); Appendix C AI Use Statement | Excellent: at least 5 hazards, each with likelihood × severity × mitigation |
| 4.3 | Creativity | The interoperability-layer framing itself (no commercial mango tool does this); market-conditioned recommender (novel for student work); the connector-coverage tier analysis | Excellent: "no existing tool does X" is justified with citations to the realism audit |
| 4.4 | Problems overcome | At least 5 distinct documented problems with root cause + fix + verification: (a) MangoLeafBD region shift to Indian Alphonso; (b) monsoon Sentinel-2 blackout solved with Sentinel-1 SAR; (c) Fyllo/Fasal no-public-API solved with app-login scrape; (d) Plantix Vision-API B2B-gated solved with screenshot OCR; (e) tf-keras-vis API breakage solved with GradientTape fallback | Excellent: each with what-happened / why / fix / verification |
| 4.5 | Clear writing | Numbered sections, captioned figures, abstract written last (5-sentence structure per Paper Writing Guide), all acronyms expanded on first use, plain-English glossary | Excellent: abstract understandable to a non-specialist; conclusions readable without the full paper |

Target: 14–15 of 15 criteria at "excellent" band. Floor: 11 of 15 at "acceptable" (the CREST minimum).

---

## 7. Ethics, Safety, and AI Disclosure *(CREST 4.2)*

### 7.1 Pesticide-safety considerations

- The recommender will *never* suggest a pesticide outside the CIB&RC registered list for mango.
- Recommendations always include PHI (pre-harvest interval) and an explicit "no harvest before" date.
- The dashboard surfaces a "this is a research prototype — verify with a registered agronomist before applying" notice on every recommendation.
- Recommendations are advisory only; the system does not auto-trigger any action.

### 7.2 Data privacy

- The cooperating farmer's identity will be anonymized in the public report unless he provides written consent to be named.
- GPS coordinates of the orchard will be obfuscated (rounded to district centroid) in public artifacts.
- Photos of his orchard will be used in the report only with written photo-release consent.
- Plantix screenshots / spray records / cabinet inventory will be locally encrypted in `data/raw/` and excluded from the git repo via `.gitignore`.
- The dashboard does not transmit farmer-uploaded photos to any third-party service unless explicitly configured to (Gemini API for OCR is gated by a per-session opt-in).

### 7.3 Dual-use considerations

- The MRL-evasion direction (e.g., "which pesticide is below the test threshold of method X") is *explicitly out of scope*. The tool recommends *compliant* sprays; it does not help evade detection.
- This is documented in the Ethics subsection of the report and in this spec.

### 7.4 AI use disclosure (per CREST AI policy)

This project is developed with substantial use of Claude (Anthropic) for:
- Strategic project scoping and design (this document was drafted with Claude assistance)
- Literature research synthesis (four research dossiers in the project root)
- Code scaffolding and debugging
- Draft writing and editing (subject to full student review and rewriting)

The final report's Appendix C will contain a detailed AI Use Statement listing:
- Each AI tool used (Claude Code, Gemini for OCR, possibly Copilot in-IDE)
- The task each was used for
- Approximate dates and a representative prompt sample
- The post-editing the student performed

The student understands all submitted work and can defend any technical claim in a viva-style conversation.

---

## 8. Open Decisions Deferred to Build Phase

These were considered and explicitly deferred, not unresolved:

1. **Project final name** — "MangoGuard" used throughout build; rename in Week 11 once results justify a specific narrative. Candidates parked: Hapus.ai, KonkanCrop, AlphonsoIQ.
2. **Cooperating-farmer monitoring stack** — confirmed at Visit 1. Spec accommodates all 5 connectors equally; design is independent of which the farmer uses.
3. **Backup farmer** — to be identified in Week 1 via the cooperating farmer's FPO contacts. Insurance against the primary farmer becoming unreachable.
4. **Streamlit deployment URL** — Streamlit Community Cloud during development; Hugging Face Spaces if RAM is constrained.

---

## 9. Acceptance Criteria for Spec Approval

For this spec to be considered approved and unlock the next step (writing the implementation plan via `superpowers:writing-plans`), the user must explicitly confirm:

- [ ] Aim and six sub-objectives are the right scope.
- [ ] Module architecture (5 modules, focal = Module 3) is the right shape.
- [ ] Connector set (5 commercial + 4 free public + manual CSV) is the right coverage.
- [ ] 12-week plan is realistic and the 3-visit constraint is respected.
- [ ] CREST evidence map covers the right criteria with the right artifacts.
- [ ] Ethics + AI-disclosure plan is acceptable.
- [ ] No critical decision is missing.

User feedback / changes will be applied inline; the spec will then be re-self-reviewed and resubmitted for approval. Only after explicit approval does the brainstorming-skill terminal state (invoke `superpowers:writing-plans`) execute.
