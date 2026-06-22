# CLAUDE.md — MangoGuard CREST Project

> **Auto-loaded context for every Claude session in this directory.** This file is the single source of truth for the project's design decisions, locked choices, open questions, and rationale. It is updated after every meaningful conversation turn. Read this first; do not re-derive decisions already recorded here.

> **🔁 STANDING INSTRUCTION (user directive, 2026-06-22): auto-push every change.** After every meaningful change to this repo, commit it with a clear message and `git push origin main` — without being asked. Commit directly to `main` (the user's established solo workflow). Do not batch or wait for permission to push. Always run the pre-commit hooks (do not bypass). Exception: never commit secrets/keys.

---

## SESSION HANDOFF — read this first if you are a fresh Claude session

**Where the project stands (updated 2026-05-30):**

- All strategic decisions are locked. **Design spec written + user-approved + decomposed into 6 implementation plans.**
- **Do NOT re-brainstorm any of these:** project identity (§1), goals (§2), target users (§4), focal research claim (§5), 5-module architecture (§6), 5 commercial connectors + free public baselines (§6), YAGNI list (§7), single-submission strategy (§8).
- **The next concrete action** is **executing the plans** via `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` (inline). Start with Plan 1 (foundation) at `docs/superpowers/plans/00-INDEX.md`.
- **Three deferred inputs to confirm with the user before farmer Visit 1 (Week 2):**
  1. Which of the 5 monitoring systems (Fyllo, Fasal, Pessl, IMD, Plantix) does the cooperating farmer already use?
  2. Confirm "MangoGuard" as the final name (deferred to Week 11 by default).
  3. Any constraint or priority change since 2026-05-30?
- **Style guidance the user reinforced during scoping:** be short and crisp, avoid 500-word essays. Match response length to question length. Technical depth welcome; skip basic anecdotes. Auto-memory at `~/.claude/projects/.../memory/` carries this across sessions.
- **Cost rule (auto-memory):** never mention API/token/session cost; the user has banned all cost commentary.

**Files to skim after this one (in order):**
1. `docs/superpowers/specs/2026-05-30-mangoguard-design.md` — canonical design spec (user-approved)
2. `docs/superpowers/plans/00-INDEX.md` — implementation plans index (6 plans, 73 tasks)
3. `Monitoring_System_Integration_Options.md` — locks the 5 connectors
4. `CREST_Official_Guidelines_Research.md` — 15 criteria, AI policy
5. `CREST_Precedents_And_Patterns.md` — past papers, what good CREST looks like
6. `Mango_Farm_Monitoring_Landscape.md` — superseded but useful background

---

## 0. How to use this file

- **Every Claude session reads this on start.** Lean on it; don't re-ask the user things already locked here.
- **Update on every meaningful user message.** Append decisions, change locked entries, add open questions. Keep dated change log at bottom.
- **If a section says "LOCKED",** don't re-debate unless the user explicitly reopens it.
- **If a section says "OPEN",** that's a live question awaiting user input.
- **Brevity matters.** This file is loaded into context every session — keep it information-dense, not chatty.

---

## 1. Project identity

**Working name:** MangoGuard
**Tagline:** A personal AI orchard manager for mid-sized Indian mango growers. Catches disease early, audits spray decisions, predicts yield and price, and tells you what's safe to spray for the market your fruit is going to.
**Student:** Grade 11 (Indian board), summer break
**Duration:** 12 weeks
**Hardware budget:** ₹0 — **MangoGuard does NOT install new hardware.** Instead, it acts as an **interoperability + intelligence layer** that ingests data from monitoring systems already deployed on the farm (Fyllo, Fasal, CropIn, IMD, CROPSAP, Plantix, etc.)
**Software/data budget:** ₹0 — all free-tier or open data

---

## 2. The student's goals (priority order)

1. **CREST Gold award** — the **sole** deliverable (~70 hours, 11+ of 15 criteria, "excellent" band where possible)
2. **College application leverage** — MIT, Caltech, top engineering schools. Project must show original work, real-world impact, and intellectual character; not look like "ran a Kaggle notebook"
3. **Real-world deployment** — pilot with the cooperating farmer's orchard during the 2026 Alphonso season

**Explicit non-goal:** peer-reviewed publication (JSR / JEI / arXiv). The project is optimized for CREST Gold and college portfolio impact only. Publication is OPTIONAL future work the student may pursue after the award is submitted — not a parallel design target.

---

## 3. The cooperating farmer

- **Variety:** Alphonso (Hapus)
- **Region:** Konkan (Maharashtra) — Ratnagiri / Sindhudurg / Raigad
- **Size:** Mid-sized (5-20 acres), assumed ~10 acres
- **Owner profile:** Rich, partially absentee, smartphone user, makes own spray decisions or follows known schedule, sorts fruit by grade at harvest (export / processor / mandi channels)
- **Existing IoT:** None assumed
- **Access:** **2-3 visits total** over 12 weeks (this is a hard constraint shaping all data-collection design)
- **Spray records:** Unknown — plan handles all three cases (written notebook, pesticide-shop bills, memory-only)

---

## 4. Target users (LOCKED)

| Tier | User | Role in project |
|---|---|---|
| **Primary user** | Mid-sized Konkan Alphonso owner (the farmer himself, like the cooperating farmer) | Direct tool user; runs MangoGuard on his phone to monitor orchard, audit manager, decide what to spray |
| **Secondary user** | FPO / cooperative field officers (Devgad Mango Growers, Ratnagiri cooperatives, etc.) | Force multiplier — 1 officer reaches 100-500 small farmers; also a structured-feedback source for the paper |
| **Indirect beneficiaries** | ~30k-50k Konkan smallholder Alphonso growers served by these FPOs | Frame honestly as downstream beneficiaries; not direct users in v1 |
| **Validation cohort for the study** | The cooperating farmer (Visit 1, 2, 3) + 2-3 FPO officer demos + 2-3 APEDA-registered exporter interviews | Stakeholder evidence for CREST 2.1 and the paper |

---

## 5. The focal research claim (LOCKED, may refine wording)

> **A spray-audit-and-recommender that combines disease pressure (weather-driven infection-risk models + satellite block-level canopy stress + data from whichever existing on-farm monitoring system the grower already runs), market-conditioned MRL constraints, and historical export-rejection patterns produces pesticide schedules whose predicted residue-noncompliance risk and per-acre cost are both lower than the schedules currently followed by mid-sized Konkan Alphonso growers, evaluated against historical RASFF data (export segments), CROPSAP outbreak records (Maharashtra), and a structured comparison with one cooperating farmer's 2026 season log.**

Secondary headline benchmark (from §6 design):

> **A system-agnostic interoperability layer that fuses data from existing monitoring systems (Fyllo, Fasal, Pessl iMETOS, IMD Mausam+Meghdoot, Plantix) plus free public baselines (AGMARKNET, DBSKKV, CROPSAP, Sentinel-2) produces disease-risk predictions whose accuracy on Konkan Alphonso scales monotonically with the number of integrated systems, demonstrating that "intelligence-layer" decision-support is deployable across heterogeneous farm IT without new hardware investment.**

---

## 6. Architecture: MangoGuard system (LOCKED)

**Web-based Streamlit dashboard, single Python app, 5 modules:**

### Module 1 — Disease Detector *(supporting)*
- Upload mango leaf / fruit photo → disease prediction + Grad-CAM heatmap
- Backbone: MobileNetV3-Small (efficient, deployable) trained on MangoLeafBD (Bangladesh public dataset)
- Calibrated to Indian Alphonso via small original dataset (300-500 photos from Visit 1, labeled across 4-6 disease classes)
- **NOT the focal research contribution** — leverages saturated leaderboard (DenseNet201 already hits 99.33% on MangoLeafBD)

### Module 2 — Orchard Health Dashboard *(supporting)*
- Block-by-block / tree-by-tree visualization of NDVI, NDRE, NDMI from Sentinel-2 (via Google Earth Engine)
- Historical trends across seasons
- Serves the "absentee owner wants to verify farm health remotely" use case
- Also the "show off to friends" lens

### Module 3 — Spray Audit & Recommender ⭐ *(FOCAL research module)*

**Design philosophy: MangoGuard is the intelligence layer, not the sensor layer.** It ingests from whichever monitoring system the farm already runs, normalizes into a unified schema, and produces decisions. **Zero new hardware required.**

**Connector layer (LOCKED — 5 commercial/institutional connectors, supporting the major monitoring tools popular Indian mango farmers actually run, source: `Monitoring_System_Integration_Options.md`):**

| # | Connector | Integration path | Effort | Why included |
|---|---|---|---|---|
| 1 | **Fyllo (AgriHawk)** | Farmer-app-login screen-scrape OR farmer-shared chart export (PNG/PDF) + OCR. No public API. | 20-30 hrs | Fastest-growing commercial agri-IoT in India (6,000+ devices, 13 states). Popular among grape/pomegranate growers expanding to mango. Soil moisture, T/RH, leaf wetness, rain, solar at ~20-min intervals. |
| 2 | **Fasal (Wolkus)** | Farmer-app-login screen-scrape OR farmer-shared CSV. No public API. | 20-30 hrs | 12-sensor station: rainfall, wind, lux, T/RH, leaf wetness, soil temp, soil tension at multiple depths. Strong horticulture footprint. Closest direct competitor to Fyllo. |
| 3 | **Pessl iMETOS / FieldClimate** | Public REST API v2 with HMAC auth; mature Python (SatAgro) and R (BASF) clients | 6-10 hrs | **The only commercial Indian agri-sensor vendor with a documented public API.** Most likely commercial system on rich export-grade Konkan Alphonso farms. Full agro-met (T, RH, leaf wetness, rain, solar, wind, soil moisture profiles) at 5-15 min. |
| 4 | **IMD Mausam + Meghdoot agromet** | Free public REST API + scrapable PDF bulletins (email-gated whitelist) | 8-12 hrs | Government baseline. District 5-day forecast + twice-weekly block-level agromet advisory in Marathi. Ships for every Konkan user regardless of what else they have. |
| 5 | **Plantix screenshot/history** | Farmer-shared screenshots + Vision-LLM OCR parse | 15-25 hrs | Most-installed plant-disease app in India. Disease/pest diagnosis leg of the data stack. Vision API is B2B-gated, but per-user history is screenshot-extractable. |

**Total connector build budget: ~70-110 hrs.** Realistic in 12 weeks at ~6-9 hrs/week of connector work.

**Free supplementary public layers (always-on baseline for every user, lightweight scrape integration, NOT counted in the 5 commercial/institutional connectors):**
- **AGMARKNET / data.gov.in** — daily mango mandi prices across Vashi, Ratnagiri, Devgad, Vengurla (free API key)
- **DBSKKV Dapoli** — Konkan-tuned microclimate + climate-trend PDFs (Konkan domain authority)
- **Maharashtra CROPSAP** — taluka pest surveillance (free, HTML scrape)
- **Sentinel-2 NDVI/NDRE block-level via Google Earth Engine** (free) — seasonal canopy stress, with Sentinel-1 SAR fallback for July-August monsoon (Western Ghats 90-92% cloud cover)

**Explicit NON-connectors (researched, rejected):**
- ❌ **CropIn** — B2B-only, exporter-owned, individual farmer can't share access
- ❌ **AgNext** — wrong tier of value chain (procurement, not farm)
- ❌ **BharatRohan** — drone-as-service, no structured machine-readable output; no documented Konkan Alphonso footprint
- ❌ **Digital Green, Avanijal** — wrong type of system (extension content, irrigation controllers)

**Manual/CSV upload fallback:** for any vendor without a connector, MangoGuard accepts farmer-uploaded CSVs in a documented schema.

**Defensibility for CREST creativity (4.3) and 4.1 (scientific understanding):** The 5-connector universal-compatibility architecture is genuinely novel for Indian mango — no commercial product or prior student work integrates this combination. The mix is deliberately heterogeneous: 1 with REST API (Pessl), 1 with government API (IMD), 2 with app-login scrape (Fyllo, Fasal), 1 with screenshot OCR (Plantix). Each integration teaches different engineering — strong evidence for criterion 4.1 (depth + breadth of understanding) and 4.4 (problems overcome).

**Expected disease-risk precision tiers:**
- Free-feeds-only: ~70-75% (district-level)
- + One commercial system (Fyllo/Fasal class): ~85-90%
- Multi-system fusion: ~88-92%

**Why this framing wins:**
- **No hardware risk** (no ₹13k spend, no install, no battery failures during monsoon)
- **More deployable** — any farm with any system can use MangoGuard immediately
- **Novel research claim** — "first interoperability layer for Indian mango decision-support" (no existing student paper, no commercial product does this for mango)
- **Stronger essay story** — "MangoGuard is system-agnostic; it works with what the farmer already has"
- **Better for FPO scaling** — different member-farms have different setups; MangoGuard normalizes them all

**Disease risk engines (operationalized, not invented):**
- **Anthracnose:** HTR-based logistic regression (Akem 2006, R² = 0.93 published); inputs T, RH, wind, sunshine, leaf-wetness duration
- **Powdery mildew:** temperature-RH window thresholds from NHB technical bulletin + ICAR forewarning regression
- **Mango hopper:** CROPSAP-reported regional pressure × local microclimate multiplier

**Recommender layer:**
- When PPI(block, day) > threshold → suggest spray *that block only*
- Pull effective pesticide list from CIB&RC registered list
- Filter by target market MRL (EU / Japan / FSSAI / buyer-specific from public PDFs)
- Rank by (efficacy × residue half-life × days-to-harvest)
- Output: "Block 3 anthracnose risk 87/100. Spray Hexaconazole 5 EC, 2 ml/L. PHI 30 days. EU-MRL compliant if harvest > 30 days away."

**Market segmentation (the user picks per block per season):**
| Segment | Share of Indian mango | MRL profile |
|---|---|---|
| Export — EU/Japan/US | ~1-2% | Strictest (EU MRL often 0.01 mg/kg) |
| Export — Gulf/ME/SE Asia | ~2-3% | Moderate (Codex MRLs) |
| Domestic — organized retail & processors (Reliance, DMart, Maaza, Frooti, Slice) | ~25-30% | FSSAI + buyer-specific stricter |
| Domestic — traditional mandi / wholesale | ~60-65% | FSSAI MRL floor |

### Module 4 — Yield & Mandi-Price Estimator *(supporting)*
- XGBoost on tabular features: acreage, age, NDVI integral, weather aggregates, soil indices
- Output: block-level yield forecast + expected AGMARKNET mandi price for harvest week
- Data: AGMARKNET via data.gov.in (free), 2001-2025 historical mango prices

### Module 5 — AskHapus Chatbot *(supporting)*
- RAG over ICAR-CISH bulletins, KVK pamphlets, DBSKKV Dapoli technical guides, NHB mango handbook
- Vector store: ChromaDB (local, free)
- LLM: Gemini 1.5 Flash free tier (15 req/min) OR local Llama-3-8B via Ollama
- Languages: English, Marathi, Hindi
- Cites sources in answers (no hallucinated agronomy)

---

## 7. Deliberate YAGNI (LOCKED — do not build in v1)

- Any new IoT hardware. MangoGuard is software-only; it integrates with monitoring systems the farmer already runs (see §6)
- Native mobile app (browser-only Streamlit; on-device inference is future work)
- Marketplace / buyer-connection platform (mention as future work)
- Multi-crop or multi-variety in v1 (Alphonso-only; Kesar/Dasheri = future work)
- Drone integration (BharatRohan-style hyperspectral) — out of scope, no DGCA permission, no budget
- Peer-reviewed publication during the 12 weeks (see §8; optional post-submission work only)

---

## 8. Submission strategy (LOCKED — single submission)

**Sole submission target: CREST Gold Award.** No journal submission, no arXiv preprint, no competition track during the 12 weeks.

**Why single-target:**
- Designing for two venues at once (CREST + JSR) creates friction. CREST wants planning/reflection/process artifacts; JSR wants a tight method+result paper. Optimizing for one removes constant tension.
- Removes the JEI March-2026 rule constraint (hypothesis-driven study no longer required for venue eligibility).
- Frees design budget toward CREST 4.3 (creativity) and 3.1 (wider-world implications) — the criteria that most help college applications.

**Optional future work (after CREST submission, outside 12-week window):**
- Reframe CREST report as JSR HS manuscript (~30 hours of rework). The CREST artifact + the CREST report contain all the substance JSR needs.
- arXiv preprint deposit for timestamp/visibility.

**Implications for design:**
- No need to hold back on tool/scope decisions to satisfy a journal's framing.
- Report can lean into the CREST "process narrative" style (planning, problems, reflection) without worrying it dilutes a research paper.
- Stakeholder engagement (farmer, FPO, exporter quotes) is valuable for CREST 2.1 / 3.1 but not gated by user-study formalism.

---

## 9. CREST Gold criteria — verbatim guidance + how MangoGuard satisfies each

> **Source pulled in full 2026-06-09 from https://www.crestawards.org/help-centre/gold-criteria-guidance/.** Each criterion below has: (a) the CREST criterion statement, verbatim; (b) any tip/note CREST appended; (c) the *exemplar evidence pattern* CREST cited (paraphrased structurally — quote it loosely in our report, do not copy); (d) how MangoGuard will satisfy it.

**Assessment rules (from CREST):**
- 15 criteria across 4 sections (Planning / Throughout / Finalising / Project-wide). **Meet at least 11 of 15** at Gold standard.
- CREST gives **no layered bands** (no "developing / good / very good / excellent" — that's our earlier misreading). Each criterion is binary at Gold: *met* or *not met*, plus one example showing what "met" looks like. Aim to meet all 15 — the binary cut at 11 is the floor, not the target.
- Submission = (i) the project report + (ii) the completed Gold Student Profile form. Both go in.
- Report formats allowed: written, slide deck, video, blog series. **We're submitting written.** Page numbers required. No verbatim internet copy. "Use your own words."
- 4.1 expects subject knowledge at **Key Stage 5 / Level 3 / S6 / IB Diploma** depth. Grade-11 Indian board is *below* KS5 nominally — so the report must over-deliver on technical depth to compensate. The Akem 2006 logistic regression derivation, NDRE biophysics, ROC-AUC calibration, Beta-prior smoothing math: all of this is the answer to 4.1.
- 4.3 explicitly invokes **Bloom's taxonomy "analysing to creating"** as the Gold bar. Descriptive work doesn't earn 4.3 — synthesis or novel construction does. The market-conditioned recommender (no commercial tool does this) is our 4.3 anchor.
- 4.4: *"It is highly unlikely a project was problem free. If no problems were encountered, the student should describe problems that could have occurred and how they were avoided."* So even our smooth-path tasks need a documented "problem-considered-and-mitigated" entry.

### Section 1 — Planning (criteria 1.1–1.5)

**1.1** *"The student set a clear aim for the project and broke it down into smaller objectives."*
- **CREST exemplar pattern:** State the aim in broad terms. Then state how you'll know you've succeeded ("I will have achieved my aim if: …"). Then a numbered objectives list — research X, design Y, gather Z data, analyse, conclude.
- **MangoGuard:** §1 of the report opens with the focal claim (§5 of this file), then a "I will have succeeded if:" block with 4 measurable success conditions (multi-connector tier improves AUC monotonically; recommender prevents ≥30% of RASFF-class rejections in counterfactual; cooperating farmer accepts ≥50% of recommendations; ≥2 FPO officers/exporters validate utility). Then a 6-objective numbered list, one per spec section.

**1.2** *"The student explained a wider purpose for the project."*
- **CREST exemplar pattern:** Why this matters to society. Who is affected. What the downstream consequence is (e.g., "reducing childhood obesity rates").
- **MangoGuard:** 96% domestic + 4% export framing; FSSAI MRL enforcement gaps; ~30k–50k Konkan smallholders served by Devgad/Ratnagiri FPOs; farmer-health exposure from over-spraying; consumer pesticide-residue exposure; ₹4,000-crore/year Alphonso economy. Named stakeholders: cooperating farmer, FPO officers, APEDA exporters, ICAR-CISH, DBSKKV Dapoli.

**1.3** *"The student identified a range of approaches to the project."*
- **CREST tip:** *"This criterion is about how the project as a whole will be achieved and not just the method for any experiments undertaken."*
- **CREST exemplar pattern:** Multiple methods compared in a table; each with explicit positives + negatives.
- **MangoGuard:** §1.3 of the report compares three project-level architectures: (A) pure-CV / disease-photo-only, (B) rule-based MRL-only with no risk engine, (C) hybrid risk-engine + MRL recommender (chosen). Plus the prior hardware-vs-interoperability tradeoff (recorded in §13 change log 2026-05-30). Each gets a positives/negatives bullet block, mirroring CREST's exemplar structure.

**1.4** *"The student described their plan for the project and why they chose that approach."*
- **CREST tip:** *"This criterion is about stating the plan for the project at a high-level with students reflecting on and justifying their choices."*
- **CREST exemplar pattern:** A 5-step plan list with a final "rationale for this approach" paragraph linking each choice to a constraint (mentor access, school programme, data partner).
- **MangoGuard:** 6 numbered objectives (one per spec section) with a rationale paragraph tying choices to the cooperating-farmer access window (2-3 visits), the no-hardware constraint, the 12-week budget, and the FPO scaling story.

**1.5** *"The student planned and organised their time well."*
- **CREST tip:** *"For this criterion we want to see something explicit like a breakdown of timings and dates or a timeline or Gantt chart. … the plan should cover the whole project, from planning and researching; to gathering data; to analysing results and drawing conclusions; to reflecting and presenting the project."*
- **CREST exemplar pattern:** Gantt chart in an appendix with tasks, durations, start/end dates, dependencies, owner, contingency time (e.g., "2 weeks buffer").
- **MangoGuard:** 12-week Gantt in Appendix 1 with planned-vs-actual columns. Buffer week built into Week 11 (report writing) and Week 12 (revision). Tasks broken out for every plan (Plans 1–6) plus fieldwork visits, FPO calls, exporter interviews.

### Section 2 — Throughout the project (2.1–2.2)

**2.1** *"The student made good use of the materials and people available."*
- **CREST exemplar pattern:** Names a specific external resource (university 3D printer + outreach staff), explains the alternative considered (buying raw materials), and quantifies the benefit ("able to test designs to destruction multiple times").
- **MangoGuard:** Document the cooperating farmer (3 visits, orchard access, spray log), FPO officer demos (≥2), APEDA exporter interviews (≥2), ICAR-CISH bulletins, DBSKKV Dapoli microclimate PDFs, the Pessl FieldClimate demo station as dev fallback, the IMD API whitelist application via sankar.nath@imd.gov.in, vendor email correspondence (Fyllo sales@fyllo.in, Fasal connect@wolkus.com), Google Earth Engine free Sentinel-2 access. Each gets a "what alternative I considered" line.

**2.2** *"The student researched the background to the project and acknowledged their sources appropriately."*
- **CREST exemplar pattern:** Inline citations in *Author Year* style with the actual references appearing in a reference list. *"Consistent referencing style. … Most references are from primary sources."* No specific style required — pick one and stay with it.
- **MangoGuard:** Pick Harvard / *Author Year* (already used in `CREST_Precedents_And_Patterns.md`). Primary sources: Akem (2006) — anthracnose HTR; Sharma et al. (NHB Bulletin 31) — powdery mildew; CROPSAP datasets (Maharashtra); RASFF portal (EU 2015–2024); FSSAI Notification 2.3.1; CIB&RC mango registration list; ICAR-CISH technical bulletins; DBSKKV Dapoli climate trend PDFs. ≥25 references, ≥70% primary. Synthesis-not-summary style (already locked).

### Section 3 — Finalising (3.1–3.3)

**3.1** *"The student made logical conclusions and explained the implications for the wider world."*
- **CREST exemplar pattern:** Conclusions tied directly back to the aim; quantifies the affected population ("the table … shows figures on the number of people in the UK who suffer from … cancers"); names the downstream artifact ("My mentor will submit the new compounds to chemical databases such as ChEMBL and PubChem").
- **MangoGuard:** §6 of report ties each module's result to (i) the cooperating farmer's measured outcome (acceptance rate, predicted cost saving, predicted rejection-rate reduction), (ii) the FPO-scaled affected population (~30k–50k farmers across Devgad/Ratnagiri), (iii) the downstream artifact (open-source Streamlit app + GitHub repo; CIB&RC + MRL data schema deposited as a reusable resource). Implications block addresses APEDA, FSSAI, exporter, and consumer angles separately.

**3.2** *"The student explained how their actions and decisions affected the project's outcome."*
- **CREST tip:** *"'I decided to do X and this changed my project in the following ways…'"*
- **CREST exemplar pattern:** Names the chosen method (CRISPR), names the rejected alternative (zinc-finger nucleases), quantifies the tradeoff (speed vs reliability vs error rate).
- **MangoGuard:** Already structurally locked. Examples: (i) chose hybrid risk-engine + MRL filter over pure-CV → enables market-conditioned recommendation; (ii) chose MobileNetV3-Small over DenseNet201 → on-phone inference for absentee owners despite -2% accuracy; (iii) chose Sentinel-1 SAR fallback over interpolation → monsoon cloud-blackout robustness; (iv) chose Beta-prior smoothing (α=1, β=9) over raw frequency → prevents 1/1 → p=1.0 overfitting on sparse RASFF data. Each gets a "decided X / changed project by Y / alternative would have caused Z" sentence.

**3.3** *"The student explained what they have learnt and reflected on what they could improve."*
- **CREST exemplar pattern:** Mixes (i) skills gained, (ii) what went well and why, (iii) what went badly and why ("Because of my impatience, I ended up making silly mistakes"), (iv) "if we were to repeat this project we would …", (v) concrete next-iteration improvements with the resources/time they'd require.
- **MangoGuard:** Reflection section structured exactly as above. Skills gained: connector engineering across heterogeneous APIs, agronomic epidemiology, ROC-AUC calibration, stakeholder interviewing, Streamlit deployment. What went well: 5-connector parity even before farmer's stack was known. What went badly: be honest — likely candidates are placeholder data for MRL/CIB&RC/RASFF tables and the single-farmer pilot N=1 limitation. Repeat-improvements: (a) multi-farmer pilot, (b) live Pessl HMAC keys, (c) replace placeholder tables with curated extracts. Future-work: drone integration, multi-cultivar (Kesar/Dasheri), exporter-buyer marketplace.

### Section 4 — Project-wide (4.1–4.5)

**4.1** *"The student showed understanding of the science behind their project, appropriate to their level."*
- **CREST descriptor:** *"Subject knowledge and complexity at Key Stage 5 / Level 3 / S6 / IB Diploma."* No exemplar text given.
- **MangoGuard:** Derive Akem (2006) HTR logistic regression mathematically; derive NDRE biophysics from chlorophyll-a/b absorption; explain triangular degree-day modelling for hopper; explain ROC-AUC mechanically (TPR vs FPR over thresholds); explain why Beta-prior smoothing is the correct conjugate prior; explain transfer learning for MobileNetV3 fine-tuning (cross-entropy + frozen-base backprop). One derived equation per module, all referenced.

**4.2** *"The student made decisions to direct the project, taking account of ethical and safety issues."*
- **CREST descriptor:** *"Risk assessments are a good form of evidence … project largely self-directed … educators/mentors consulted on technical or subject knowledge matters."*
- **CREST exemplar pattern:** A risk-assessment table in an appendix; consent forms for human-data collection; legislation references (Data Protection Act 2018, MRC guidance).
- **MangoGuard:** §7 of report covers — (i) **risk-assessment table** for orchard visits (heat, pesticide exposure, snake/insect risk, vehicle); (ii) **farmer consent form** (English + Marathi) for spray log + photo collection, naming what data is collected and how it's used; (iii) Indian data-protection compliance (DPDP Act 2023); (iv) **pesticide-recommendation safety disclaimer** (recommendations are advisory, not a prescription; final responsibility rests with farmer; PHI compliance is critical); (v) **AI use disclosure** per CREST AI policy (already drafted in §12).

**4.3** *"The student showed creative thinking."*
- **CREST tip:** *"At Gold level the student showed evidence of working at the, 'analysing to creating' levels of cognition."* (Bloom's taxonomy.)
- **CREST exemplar pattern:** Combining quantitative experimental data with open-source data via student-written code that "analysed the results and created a single output file." Original synthesis across sources.
- **MangoGuard:** Two anchors. (i) **Market-conditioned recommender** — no existing commercial mango tool combines disease-risk + MRL + RASFF in a per-block per-segment decision. (ii) **Interoperability-tier benchmark study** — quantifying that disease-risk AUC scales monotonically with the number of integrated systems is a genuinely novel research contribution. Both are creating-level (Bloom), not analysing-level.

**4.4** *"The student identified and overcame problems successfully."*
- **CREST tip:** *"It is highly unlikely a project was problem free. If no problems were encountered, the student should describe problems that could have occurred and how they were avoided."*
- **CREST exemplar pattern:** Narrative arc — problem encountered (hot-glue gun melted acrylic), tried workarounds (lowered temperature, cooled before contact), final solution (returned to research, switched to contact adhesive). All three stages visible.
- **MangoGuard:** ≥5 problems with full 3-stage narratives. (i) Monsoon cloud blackout for Sentinel-2 → tried temporal interpolation → final: Sentinel-1 SAR fallback. (ii) MangoLeafBD region mismatch with Indian Alphonso → tried direct transfer → final: small-N original dataset fine-tune. (iii) No public API for Fyllo/Fasal → tried vendor outreach → final: app-login screen-scrape with documented schema. (iv) Placeholder MRL/CIB&RC/RASFF data risk → tried full pre-curation → final: PLACEHOLDER marker in CSV + refresh-before-submission protocol. (v) Plantix Vision API B2B-gated → considered Gemini Vision → final: dropped from connectors, covered by Plan 5 MobileNetV3 + CROPSAP. Each gets the problem → workaround → root-cause-fix arc.

**4.5** *"The student explained their project clearly, in writing or conversation."*
- **CREST exemplar pattern (verbatim sub-bullets):** "Thought about their intended audience"; "Explained abbreviations … with the abbreviation in brackets"; "Organised the project into a logical structure"; "Used concise language where possible"; "Used examples and evidence to back up their points"; "Proofread"; "Made use of images, graphs and tables where appropriate."
- **MangoGuard:** Abstract first. Numbered sections (1–10). Plain-English glossary appendix (MRL, PHI, NDRE, NDVI, RASFF, HTR, ROC-AUC, CIB&RC, FSSAI, FPO, APEDA). Every abbreviation expanded on first use *with abbreviation in brackets*. Captioned figures. ≥6 figures, ≥3 tables (Gantt, MRL profile, results table). Proofread by mentor + at least one non-STEM reader. Audience target: "someone with a good amount of scientific literacy but no background or specialist knowledge of the topic" (verbatim CREST phrasing).

---

## 9.5 Writing patterns to emulate (extracted from CREST exemplars)

Direct stylistic lessons from the *content* of CREST's published exemplar evidence — these are what their assessors visibly reward. Mimic the structure; do not copy phrases.

1. **"I will have achieved my aim if:" block.** Three bulleted success conditions. Each is measurable. This pattern appears in the 1.1 exemplar — use it verbatim as a structural template.
2. **Method-comparison with positives/negatives bullets.** The 1.3 exemplar runs *Method | Positive | Negative* for each option. Use exactly this format for the §1.3 architectural-alternatives discussion.
3. **Rationale-paragraph at the end of the plan.** The 1.4 exemplar's plan is a numbered list followed by one paragraph beginning *"Our rationale for this approach is …"* — adopt this two-part shape.
4. **Gantt with contingency note.** The 1.5 exemplar literally says *"I have allowed a good amount of extra time (2 weeks) as a contingency."* Replicate this — name the buffer weeks explicitly.
5. **External-resource paragraphs in 2.1.** The exemplar names the resource (3D printer), the access route (university outreach), the alternative considered (raw materials), and the benefit it enabled (multiple test cycles). Four-part shape — use for each external resource in §2.1.
6. **Inline citation format.** *(Author, Year)* directly in the prose body. References list at the end. Match the 2.2 exemplar style.
7. **Wider-implications quantification.** The 3.1 exemplar references *"table 2 (in the background information section) for figures on the number of people in the UK who suffer from … cancers."* Mirror this — quantify affected populations in a numbered table in the background section, then reference back from §6 conclusions.
8. **"If I had used X instead of Y" sentences.** The 3.2 exemplar names the rejected alternative. Every methodology decision in our §3.2 section gets this counterfactual sentence.
9. **5-part reflection.** The 3.3 exemplar reflection covers (i) skills gained, (ii) team/individual successes, (iii) honest failures with root cause, (iv) "if we were to repeat", (v) concrete next-iteration improvements. Match exactly.
10. **Consent-form + risk-assessment appendix.** The 4.2 exemplar names a consent form and risk-assessment table in appendices. Replicate.
11. **Plain-language abbreviation rule.** First use spelled out, abbreviation in brackets. Then abbreviation thereafter. This is *the* 4.5 marker.
12. **Audience targeting paragraph.** The 4.5 exemplar opens with audience consideration. Add an explicit "Intended audience" sentence to the report's introduction.

---

## 9.6 Report structure (LOCKED — built from 9.5 + verbatim CREST guidance)

The report uses this fixed structure. Each section's heading and intent is locked; word counts are guidance for budgeting, not hard limits.

| § | Title | Target words | Maps to criteria |
|---|---|---|---|
| 0 | Abstract | 250 | 4.5 |
| 1 | Aim, success conditions, and objectives | 800 | 1.1, 1.2, 4.5 |
| 2 | Wider purpose and affected populations | 800 | 1.2, 3.1 |
| 3 | Range of approaches considered | 1,200 | 1.3, 3.2 |
| 4 | Plan and rationale | 600 | 1.4 |
| 5 | Background research and literature review | 2,000 | 2.2, 4.1 |
| 6 | Methodology — module-by-module | 3,500 | 1.4, 2.1, 4.1, 4.3 |
| 7 | Ethics, safety, and AI use | 800 | 4.2 |
| 8 | Results and findings | 2,000 | 3.1, 3.2, 4.1 |
| 9 | Problems encountered and how they were overcome | 1,200 | 4.4 |
| 10 | Conclusions and wider-world implications | 1,500 | 3.1 |
| 11 | Reflection and future work | 1,200 | 3.3 |
| 12 | References | – | 2.2 |
| App. A | Gantt chart (planned vs actual) | – | 1.5 |
| App. B | Risk assessment + farmer consent form | – | 4.2 |
| App. C | Code samples + open-source data manifest | – | 4.3 |
| App. D | Plain-English glossary | – | 4.5 |
| App. E | AI use statement (per CREST AI policy) | – | 4.2, 4.5 |

**Total body target: ~16,000 words.** Submitted alongside the **Gold Student Profile form** (per CREST submission rules).

Required figures (minimum): system architecture diagram, connector-tier AUC chart, NDVI/NDRE/NDMI time-series for the pilot orchard, ROC curve for the calibrated PPI, RASFF-counterfactual prevention-rate bar chart, recommender decision-flow diagram.

Required tables (minimum): MRL profile by market segment (§5/§6), Gantt planned-vs-actual (App. A), risk-assessment matrix (App. B), affected-population quantification (§2), method-comparison table (§3), references summary by source type (§5).

---

## 10. Open decisions (currently waiting on user)

- **Hardware decision:** ❌ **LOCKED: NO new hardware.** MangoGuard is an interoperability + intelligence layer. Pivot made 2026-05-30.
- ✅ **Which 5 monitoring systems to support:** LOCKED — Fyllo, Fasal, Pessl iMETOS, IMD Mausam+Meghdoot, Plantix. (See §6 Module 3 table.) AGMARKNET, DBSKKV, CROPSAP, Sentinel-2 also integrated but as free public baseline layers, not commercial connectors.
- **Per-connector test data:** for each of the 5, we need at least one real sample dataset to develop and test against. Strategy:
  - **Fyllo, Fasal:** reach out to vendors directly (sales@fyllo.in, connect@wolkus.com) for a demo/student data dump; in parallel, build the screen-scrape adapter speculatively against publicly available app screenshots
  - **Pessl:** use the public FieldClimate demo station data while developing; the cooperating farmer's HMAC keys (if he owns one) are bonus
  - **IMD:** apply for the API whitelist via sankar.nath@imd.gov.in early in Week 1
  - **Plantix:** ask the cooperating farmer for screenshot history; collect synthetic test screenshots from public Plantix marketing material
- **Cooperating-farmer monitoring stack:** ⏸ DEFERRED to first farmer contact (Week 1-2). Student will find out which (if any) of the 5 systems he uses. Spec must accommodate all 5 connectors equally; experimental design has a branch point at Visit 1.
- **Project name:** ⏸ DEFERRED. "MangoGuard" is the working name throughout the design + build phase. Decision postponed; can be renamed in Week 11 once results exist. Candidates parked: Hapus.ai, KonkanCrop, AlphonsoIQ.
- ❌ ~~Email CREST about dual-submission policy~~ — N/A, single submission only
- ❌ ~~OSF pre-registration~~ — N/A, no longer pursuing JEI hypothesis-study framing
- **Does the cooperating farmer own a Pessl iMETOS station?** (determines whether connector #4 is real-time pilot data or reference implementation)
- **Does the cooperating farmer use Plantix?** (determines whether 6-month diagnosis history is collectable in Visit 1)

---

## 11. Repo files (reference)

- `CLAUDE.md` — this file
- `docs/superpowers/specs/2026-05-30-mangoguard-design.md` — **CANONICAL DESIGN SPEC** (~7k words). USER-APPROVED 2026-05-30.
- `docs/superpowers/plans/00-INDEX.md` — implementation-plans index (6 plans, 73 tasks, ~328 atomic steps)
- `docs/superpowers/plans/2026-05-30-01-foundation.md` — Plan 1: repo + schema + Connector ABC -> `v0.1.0`
- `docs/superpowers/plans/2026-05-30-02-free-public-connectors.md` — Plan 2: AGMARKNET/IMD/DBSKKV/CROPSAP/Sentinel-2 -> `v0.2.0`
- `docs/superpowers/plans/2026-05-30-03-commercial-connectors.md` — Plan 3: Pessl/Fyllo/Fasal/Plantix/CSV -> `v0.3.0`
- `docs/superpowers/plans/2026-05-30-04-risk-engine-recommender.md` — Plan 4 (FOCAL): disease-risk engine + MRL recommender + RASFF counterfactual eval -> `v0.4.0`
- `docs/superpowers/plans/2026-05-30-05-supporting-modules.md` — Plan 5: disease detector + dashboard data + yield/price + chatbot -> `v0.5.0`
- `docs/superpowers/plans/2026-05-30-06-dashboard-fieldwork-report.md` — Plan 6: Streamlit integration + stakeholder logbook + CREST report scaffold -> `v1.0.0-rc1`
- `CREST_Official_Guidelines_Research.md` — 15 criteria, AI policy, dual-submission rules, case studies
- `CREST_Precedents_And_Patterns.md` — 16 mined papers, JEI rule change, mango SOTA, 15 patterns of excellence
- `Mango_Farm_Monitoring_Landscape.md` — Fyllo/Fasal pricing, IMD/CROPSAP, sensor BOM, accuracy tiers (now historical reference; hardware path abandoned)
- `Monitoring_System_Integration_Options.md` — realism audit of 12 systems for API access; locks the 5 connectors used in Module 3
- `CREST_Paper_Writing_Guide.md` — *original draft, partially obsolete — needs rewrite after design is final*
- `CREST_Student_Profile_Checklist.md` — *original draft, partially obsolete*
- `CREST_Reference_List.md` — *original draft, partially obsolete*
- `CREST_Crop_Disease_Detection.ipynb` — *original notebook, OBSOLETE — to be replaced*

---

## 12. AI use disclosure (in-progress, for the final report)

This project is developed with substantial use of Claude (Anthropic) for:
- Strategic project scoping and design
- Literature research synthesis
- Code scaffolding and debugging
- Draft writing and editing (subject to student review and rewriting)

Per CREST AI policy (https://www.crestawards.org/help-centre/crest-guidelines-on-use-of-ai-for-students/):
- All AI-generated content will be referenced in the final report
- A dedicated AI Use Statement will list each tool, task, date, prompt sample, and post-editing performed
- The student understands all submitted work and can defend it in conversation
- No AI-generated prose is submitted verbatim as report body

---

## 13. Change log

| Date | Change |
|---|---|
| 2026-05-30 | Initial file created; all decisions to date locked from session 1 |
| 2026-05-30 | **Major pivot:** removed all hardware. MangoGuard is now an **interoperability + intelligence layer** that ingests from 4-5 existing monitoring systems (Fyllo, Fasal, CropIn, IMD/CROPSAP, Plantix, etc.) already deployed on farms. No new sensors. Hardware budget → ₹0. Research agent dispatched to enumerate API access for each system; output will land in `Monitoring_System_Integration_Options.md`. |
| 2026-05-30 | **5 connectors LOCKED** after API research: (1) AGMARKNET/data.gov.in, (2) IMD Mausam+Meghdoot, (3) DBSKKV Dapoli, (4) Pessl iMETOS/FieldClimate, (5) Plantix screenshot/OCR. Total integration budget ~40-60 hrs. Fyllo/Fasal/CropIn/AgNext/BharatRohan explicitly rejected — no public API or wrong tier. Defensibility win: 3/5 connectors are open-government primary sources; 2/5 commercial connectors are the only Indian agri systems with documented public REST API or user-exportable trail. |
| 2026-05-30 | **Submission strategy narrowed to SINGLE target: CREST Gold only.** Journal/arXiv/competition tracks dropped from 12-week scope. Removes JEI March-2026 rule constraint and dual-venue design tension. §2 Goals, §8 Submission Strategy, §10 Open Decisions all updated. Optional future work (post-submission JSR reframe) documented. |
| 2026-05-30 | **Connector universe expanded to support all major popular Indian mango farm monitoring tools (5 commercial/institutional connectors LOCKED):** Fyllo, Fasal, Pessl iMETOS, IMD Mausam+Meghdoot, Plantix. AGMARKNET/DBSKKV/CROPSAP/Sentinel-2 reclassified from "primary connectors" to "free public baseline layers" (always-on, lightweight). MangoGuard's positioning shifts from "opportunistic connector to whatever the farmer has" to "universal compatibility layer — bring whatever you have." §6 Module 3 table rewritten. Total connector build budget: ~70-110 hrs (vs. ~40-60 in the narrower design). |
| 2026-05-30 | **Session-end handoff audit.** Added top-of-file SESSION HANDOFF block for next-session pickup. Fixed three stale references inconsistent with locked decisions: §5 secondary claim (removed "leaf-wetness sensor" and stale "CropIn" connector list), §7 YAGNI (removed phantom "₹13k station" line, added explicit "no new hardware" line + "no publication during 12 weeks" line), §9 CREST criteria map rows for 1.3 / 3.2 / 4.4 (replaced Tier-1/2/3 hardware-tier language with connector-coverage / interoperability framing). File now consistent. User saving session to resume in a new conversation. |
| 2026-05-30 | **Continuing in same session (user reversed save-and-close decision).** Cooperating-farmer monitoring stack DEFERRED until Week 1-2 first contact. Project name DEFERRED — keep "MangoGuard" as working name through build phase, decide final name in Week 11. Spec drafting proceeds without these inputs. |
| 2026-05-30 | **Canonical design spec WRITTEN** at `docs/superpowers/specs/2026-05-30-mangoguard-design.md` (~7k words, 9 sections). Covers: aim + 6 sub-objectives, wider purpose, range of approaches (3 evaluated, hybrid C chosen), full methodology with module-level architecture diagram + data flow + repo tree + tech stack table, evaluation methodology for all 5 objectives, risk register (11 risks), 12-week Gantt, CREST 15-criteria evidence map, ethics + AI disclosure, deferred open decisions, approval checklist. Self-review pass completed: 5 fixes applied inline (aim baseline clarified, schema file renamed, ranking formula bug fixed, ICAR-CISH/KVK baseline pinned, chatbot descope-first rule added). Spec now awaits explicit user approval before `superpowers:writing-plans` skill is invoked to produce the week-by-week implementation plan. |
| 2026-05-30 | **Project auto-memory saved** to `~/.claude/projects/c--Users-devad-.../memory/`: `user_profile.md`, `feedback_no_cost_mentions.md`, `feedback_communication_style.md`, plus `MEMORY.md` index. Locks user style preferences and the no-cost-mentions rule across all future sessions in this project, independent of CLAUDE.md. |
| 2026-05-30 | **User APPROVED the design spec.** `superpowers:writing-plans` skill invoked. Spec decomposed into 6 sub-plans + index under `docs/superpowers/plans/`. Total: 73 atomic tasks, ~328 testable steps. Each plan terminates in a semver tag (Plan 1 -> `v0.1.0`, Plan 6 -> `v1.0.0-rc1`). Plans 2 + 3 parallelizable; Plans 4 + 5 parallelizable; Plan 6 must run last. Self-review pass complete: spec coverage 100% (one gap found — notebooks 01/02/05/06 unassigned — fixed inline by adding Task 17 to Plan 4 and Task 13 to Plan 6); no placeholder red flags; type/name consistency verified across plans (`ConnectorSource`, `MarketSegment`, `count_by_source`, `compute_ppi`, `Recommendation` all defined-once-used-consistently). Ready for execution handoff. |
| 2026-06-09 | **§9 rewritten with verbatim CREST Gold guidance.** Pulled the full criteria page (https://www.crestawards.org/help-centre/gold-criteria-guidance/) directly. Each of the 15 criteria now has: CREST statement, CREST tip (where present), CREST exemplar evidence pattern, MangoGuard satisfaction plan. **Corrected an earlier misreading: CREST does NOT use developing/good/very good/excellent bands at Gold.** Each criterion is binary at Gold (met or not) with a single illustrative exemplar; the threshold is 11-of-15. Added §9.5 (12 writing patterns extracted from CREST exemplars, with structural templates to mimic), §9.6 (locked report structure: 12 sections + 5 appendices, ~16k words, mapped to criteria). 4.1 KS5/Level3/S6/IB depth target noted explicitly — Grade-11 Indian board is below KS5 nominally, so technical-depth over-delivery is required (Akem derivation, ROC-AUC mechanics, Beta-prior conjugacy, NDRE biophysics). 4.3 Bloom's "analysing-to-creating" bar pinned to two anchors: market-conditioned recommender + interoperability-tier benchmark study. |

---

*End of CLAUDE.md. Next user message will trigger an update.*
