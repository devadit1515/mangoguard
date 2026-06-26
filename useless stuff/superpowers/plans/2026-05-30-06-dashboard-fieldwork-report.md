# MangoGuard Plan 6: Streamlit Dashboard Integration + Field-Validation Logbook + Report Scaffolding

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. **Prerequisites:** Plans 1-5 (`v0.5.0`).

**Goal:** Wire all 5 modules into a single Streamlit dashboard; build the field-validation logbook for 3 farmer visits + 2 FPO demos + 2 exporter interviews; scaffold the CREST report + Student Profile Form so weeks 11-12 are filling templates, not building structure.

**Architecture:** Multipage Streamlit app under `src/mangoguard/dashboard/`. Each page imports its module's public API. Field logbook is structured markdown templates. Report scaffold is 7 sections + 6 appendices with paragraph-level outlines.

**Tech Stack:** Streamlit 1.34+, Altair, Pillow, pyyaml.

---

## File Structure

```
src/mangoguard/dashboard/
├── __init__.py
├── app.py                 # Streamlit entry-point (Home)
├── pages/
│   ├── 1_Disease_Detector.py
│   ├── 2_Orchard_Health.py
│   ├── 3_Spray_Recommender.py
│   ├── 4_Yield_and_Price.py
│   ├── 5_AskHapus.py
│   └── 6_Connector_Status.py
├── components/
│   ├── connector_status_panel.py
│   ├── ppi_gauge.py
│   ├── recommendation_card.py
│   ├── market_segment_picker.py
│   └── citation_renderer.py
└── state.py               # session-state helpers

docs/stakeholder_interviews/
├── _template_visit.md
├── _template_fpo_demo.md
├── _template_exporter_interview.md
├── farmer_visit_1.md   farmer_visit_2.md   farmer_visit_3.md
├── fpo_officer_1.md    fpo_officer_2.md
├── exporter_1.md       exporter_2.md
└── sus_scoring_template.yaml

docs/crest_report/
├── 00_outline.md
├── 01_introduction.md   02_literature_review.md   03_methodology.md
├── 04_results.md        05_discussion.md          06_conclusion.md
├── 07_personal_reflection.md
├── 08_references_harvard.md
├── appendix_a_gantt.md  appendix_b_risk_assessment.md  appendix_c_ai_use_disclosure.md
├── appendix_d_raw_data.md  appendix_e_farmer_feedback.md  appendix_f_logbook.md

docs/student_profile_form/
├── part_a_criteria_evidence_index.md
└── part_b_personal_reflection.md

tests/dashboard/
├── test_app_smoke.py
├── test_pages_smoke.py
└── test_components.py
```

---

## Task 1: Streamlit app entry-point + Home

**Files:** `src/mangoguard/dashboard/app.py` + `tests/dashboard/test_app_smoke.py`.

Home page: project description, block picker (loads `data/orchard_blocks.geojson`), market segment picker (MarketSegment enum), connector-status tile.

- [ ] **Step 1: Write smoke test** using `streamlit.testing.v1.AppTest` — `test_app_loads_without_error`, `test_block_picker_lists_blocks_from_geojson`, `test_market_segment_picker_has_4_options`.
- [ ] **Step 2: Implement `app.py`** with `st.set_page_config(page_title="MangoGuard", layout="wide")`, sidebar pickers, connector-status tile.
- [ ] **Step 3: Verify smoke tests pass.**
- [ ] **Step 4: Commit:** `feat(dashboard): Streamlit app entry-point + home page`

---

## Task 2: Connector status panel

**Files:** `src/mangoguard/dashboard/components/connector_status_panel.py` + `tests/dashboard/test_components.py`.

Reads `FeedStore.count_by_source()`. Grid: green if rows in last 7 days, yellow if last 30, red if no rows ever. Shows last-update timestamp per connector.

- [ ] **Step 1: Write failing tests** — `test_renders_9_connectors`, `test_green_yellow_red_thresholds`, `test_handles_empty_store_all_red`.
- [ ] **Step 2: Implement.**
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(dashboard): connector status panel`

---

## Task 3: Disease Detector page

**Files:** `src/mangoguard/dashboard/pages/1_Disease_Detector.py`.

UI: file uploader (jpg/png) → `disease_detector.infer.predict_image` → predicted class, confidence bar, top-3 alternatives, Grad-CAM overlay side-by-side. Warning banner if confidence < 0.8. "Add to season log" button writes to `season_log.db`.

- [ ] **Step 1: Write smoke test** — `test_page_loads`, `test_upload_widget_present`.
- [ ] **Step 2: Implement the page.**
- [ ] **Step 3: Verify smoke test passes.**
- [ ] **Step 4: Commit:** `feat(dashboard): Disease Detector page`

---

## Task 4: Orchard Health page

**Files:** `src/mangoguard/dashboard/pages/2_Orchard_Health.py`.

UI: block + season pickers. Altair line chart for NDVI/NDRE/NDMI. Anomaly list from `orchard_health.queries.block_anomalies`. Multi-block heatmap (block × ISO-week, color = mean NDVI). Cross-season bar chart of NDVI integral.

- [ ] **Step 1: Write smoke test.**
- [ ] **Step 2: Implement the page.**
- [ ] **Step 3: Verify smoke test passes.**
- [ ] **Step 4: Commit:** `feat(dashboard): Orchard Health page with multi-season views`

---

## Task 5: Spray Recommender page (FOCAL module UX)

**Files:** `src/mangoguard/dashboard/pages/3_Spray_Recommender.py`.

This is the dashboard surface for the focal research module. UX conveys: PPI, primary pathogen, market-conditioned recommendation, alternatives, rationale, literature citations.

UI:
1. Block + date + market segment + days-until-harvest pickers.
2. Triggers `recommend.recommend(...)` on change.
3. `ppi_gauge` component: 0-100 dial with color band (green <30, yellow 30-70, red >70).
4. `recommendation_card` component: top recommendation (pesticide, dose, PHI, "no harvest before" date, expected RASFF rejection probability for export markets); 2-3 alternatives; rationale paragraph; disclaimer banner "Research prototype — verify with a registered agronomist."
5. "Compare with ICAR-CISH baseline" expander showing canonical schedule's recommendation for this ISO week.

- [ ] **Step 1: Write smoke test** — `test_page_loads`, `test_pickers_drive_recommendation_update`.
- [ ] **Step 2: Implement `ppi_gauge` component.**
- [ ] **Step 3: Implement `recommendation_card` component.**
- [ ] **Step 4: Implement the page.**
- [ ] **Step 5: Verify smoke test passes.**
- [ ] **Step 6: Commit:** `feat(dashboard): Spray Recommender page (FOCAL module UX)`

---

## Task 6: Yield + Price page

**Files:** `src/mangoguard/dashboard/pages/4_Yield_and_Price.py`.

UI: block + harvest week picker. Yield forecast (kg/acre + CI + previous-season comparison). Price forecast (modal price per nearby mandi at harvest week). Total expected revenue. SHAP top-5 drivers panel.

- [ ] **Step 1: Write smoke test.**
- [ ] **Step 2: Implement the page.**
- [ ] **Step 3: Verify smoke test passes.**
- [ ] **Step 4: Commit:** `feat(dashboard): Yield + Price page with SHAP explainability`

---

## Task 7: AskHapus chatbot page

**Files:** `src/mangoguard/dashboard/pages/5_AskHapus.py`.

UI: language picker (en/mr/hi), chat input, `chatbot.rag.query(...)`, response rendered with `citation_renderer` component (clickable PDF + page references), chat history in `st.session_state`.

- [ ] **Step 1: Implement `citation_renderer` component** — renders [PDF name, page N] as clickable expander showing snippet text.
- [ ] **Step 2: Write smoke test.**
- [ ] **Step 3: Implement the page.**
- [ ] **Step 4: Verify smoke test passes.**
- [ ] **Step 5: Commit:** `feat(dashboard): AskHapus chatbot page with citation rendering`

---

## Task 8: Admin connector-status page

**Files:** `src/mangoguard/dashboard/pages/6_Connector_Status.py`.

Visible only with `?admin=1` query param. Per-connector status, "Run connector now" button per connector, last-error display, CSV fallback upload widget.

- [ ] **Step 1: Implement.**
- [ ] **Step 2: Smoke test.**
- [ ] **Step 3: Commit:** `feat(dashboard): admin connector-status page`

---

## Task 9: Field-validation visit templates

**Files:** `docs/stakeholder_interviews/_template_visit.md` + `_template_fpo_demo.md` + `_template_exporter_interview.md` + `sus_scoring_template.yaml`.

`_template_visit.md` contents:

```markdown
# Visit N — [Farmer Name (or codename)], [Date], [Location]

## Logistics
- Travel: [from -> to, mode, duration]
- Photo release consent: [yes / no / pending]
- Accompanying observer: [name or "solo"]

## Data Collected
- Leaf photos collected: [N photos across {classes}]
- GPS polygon walked: [yes/no; file: data/orchard_blocks.geojson]
- Spray records reviewed: [yes/no; format: notebook / shop bills / memory only]
- Monitoring stack confirmed: [list of {Fyllo, Fasal, Pessl, Plantix, IMD, none}]

## Observations
[free-form 3-5 paragraphs]

## Structured Feedback
- SUS scores (see sus_scoring_template.yaml): [link to filled YAML]
- 5 open questions:
  1. What is confusing about MangoGuard? — [answer]
  2. What is missing? — [answer]
  3. Would you use this in your next season? — [answer]
  4. Would you pay for it? At what price? — [answer]
  5. What would you change? — [answer]

## Quotable Lines
[3 candidate quotes for the report, with consent flags]

## Follow-ups
[list of actions for next visit]
```

`sus_scoring_template.yaml` contents: standard 10-question System Usability Scale (Brooke 1996) with `score: null` placeholders, normalized to 0-100.

- [ ] **Step 1: Write the three `_template_*.md` files.**
- [ ] **Step 2: Write `sus_scoring_template.yaml`.**
- [ ] **Step 3: Create empty instances** (`farmer_visit_1.md`, etc.) by copying the template.
- [ ] **Step 4: Add test** `tests/test_stakeholder_template.py` asserting `_template_visit.md` has all required sections (Logistics, Data Collected, Observations, Structured Feedback, Quotable Lines, Follow-ups).
- [ ] **Step 5: Commit:** `docs(stakeholder): visit/demo/interview templates + SUS form`

---

## Task 10: CREST report scaffold

**Files:** 7 section files + 6 appendix files under `docs/crest_report/` + `00_outline.md`.

Each section markdown has paragraph-level outline derived from `CREST_Paper_Writing_Guide.md`. Each paragraph header includes target word count + CREST criterion, e.g.:

```markdown
## Paragraph 4: The Research Gap (Original Contribution)

**Target:** 80 words. **Criterion:** 1.1, 1.2. **Status:** [DRAFT / FINAL]

[Verbatim text from spec §2.2 about MangoGuard being the first interoperability layer for Indian mango...]
```

- [ ] **Step 1: Write `00_outline.md`** listing all 7 sections + 6 appendices with target word counts (sum 7000-8000 words).
- [ ] **Step 2: Write skeletons** `01_introduction.md` through `07_personal_reflection.md` with paragraph headers from the Paper Writing Guide.
- [ ] **Step 3: Write `08_references_harvard.md`** seeded with refs from `CREST_Reference_List.md` + 4 research dossiers.
- [ ] **Step 4: Write the 6 appendix skeletons:**
  - `appendix_a_gantt.md` — Gantt table template (planned vs actual columns, blank rows).
  - `appendix_b_risk_assessment.md` — risk table template (Hazard / Risk / Likelihood / Severity / Control Measure).
  - `appendix_c_ai_use_disclosure.md` — AI use statement template (tool, task, dates, prompt sample, post-editing).
  - `appendix_d_raw_data.md` — placeholder for `sklearn.metrics.classification_report` outputs + summary tables.
  - `appendix_e_farmer_feedback.md` — SUS scores + quotes + photo gallery (consent flags).
  - `appendix_f_logbook.md` — weekly logbook stub (12 weeks).
- [ ] **Step 5: Commit:** `docs(crest_report): 7-section + 6-appendix scaffold with paragraph-level outlines`

---

## Task 11: Student Profile Form

**Files:** `docs/student_profile_form/part_a_criteria_evidence_index.md` + `part_b_personal_reflection.md`.

**Part A:** 15-criteria checklist, columns `# | Criterion | Report section | Page | Notes`. Pre-fill `Report section` from spec §6 CREST criteria evidence map.

**Part B:** Personal reflection (~400 words), 5 prompts per spec §3.3:
1. Your role and tasks completed
2. How the project was successful (or not)
3. What you learned
4. Wider impact
5. What you would change and what next

- [ ] **Step 1: Write `part_a_criteria_evidence_index.md`** with all 15 criteria pre-mapped to spec sections.
- [ ] **Step 2: Write `part_b_personal_reflection.md`** with the 5 prompts and ~80-word target per prompt.
- [ ] **Step 3: Commit:** `docs(student_profile): Part A index + Part B reflection prompts`

---

## Task 12: End-to-end dashboard smoke

**Files:** `tests/dashboard/test_pages_smoke.py`.

Single test using `streamlit.testing.v1.AppTest`: loads every page in sequence, asserts no exceptions on default state.

- [ ] **Step 1: Write the test.**
- [ ] **Step 2: Verify PASS.**
- [ ] **Step 3: Commit:** `test(dashboard): end-to-end smoke across all pages`

---

## Task 13: Exploration + field-validation notebooks

**Files:** `notebooks/01_data_exploration.ipynb` + `notebooks/06_field_validation.ipynb`.

Spec §4.4 lists these notebooks as required deliverables.

- [ ] **Step 1: Notebook 01** — exploratory data analysis over the FeedStore after a week of running. Per-source row counts, per-block data freshness heatmap, missing-data audit per BlockObservation field, NDVI/NDRE seasonal arc plots. Produces 4 figures saved to `artifacts/figs/`.
- [ ] **Step 2: Notebook 06** — load all stakeholder feedback YAMLs (filled by farmer/FPO/exporter visits), compute average SUS scores, tabulate open-ended responses by theme, render a "what worked / what failed" summary that feeds the report Discussion section. Produces 3 figures.
- [ ] **Step 3: Commit:** `notebooks(field): data exploration + field-validation summary notebooks`

---

## Task 14: Bump version + tag

- [ ] Bump to `1.0.0-rc1`. First end-to-end MangoGuard release candidate.
- [ ] Run `pytest -v` — expect all Plans 1-6 tests pass.
- [ ] Commit + tag `v1.0.0-rc1`.

---

## Acceptance criteria for Plan 6 complete

- [ ] All 6 Streamlit pages load and render without exceptions.
- [ ] Connector status panel correctly classifies green/yellow/red.
- [ ] Disease Detector page returns prediction + Grad-CAM on any uploaded image.
- [ ] Spray Recommender page produces differentiated recommendations across the 4 MarketSegment values.
- [ ] AskHapus page returns answers with ≥1 citation per response.
- [ ] All 7 CREST report sections exist with paragraph-level outlines.
- [ ] All 6 appendix templates exist.
- [ ] Student Profile Form Part A pre-maps all 15 criteria.
- [ ] All 3 stakeholder-interview templates exist.
- [ ] Tagged `v1.0.0-rc1`.

---

## Final checklist before Week-11 report writing

- [ ] At least one farmer visit completed and logged.
- [ ] At least one FPO demo completed.
- [ ] At least one exporter interview completed.
- [ ] Retrospective backtest results saved (Plan 4 Task 14 output).
- [ ] RASFF counterfactual results saved (Plan 4 Task 15 output).
- [ ] Disease detector test accuracy saved (Plan 5 Task 6 output).
- [ ] Yield + price model MAE saved (Plan 5 Tasks 10+11 outputs).
- [ ] Chatbot 20-question acceptance results saved (Plan 5 Task 16 output).

Weeks 11-12 then become filling `docs/crest_report/*.md` with real numbers and quotes, not building structure from scratch.
