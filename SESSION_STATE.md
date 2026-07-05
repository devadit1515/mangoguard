# SESSION_STATE — running memory for the CREST Gold sample rebuild

> **Purpose.** Anti-amnesia anchor for this conversation. Read this at the top of every working
> session so I don't lose track, contradict earlier decisions, or hallucinate numbers. Update it
> when a decision is made or a fact is verified. It is *internal working memory*, not a deliverable.
> Do NOT overwrite the real `CLAUDE.md` (project instructions) — this is a separate file.

Last updated: 2026-07-04 (during the "rethink from scratch" turn, right after verifying the dataset).

---

## 0. The mission (why this exists)

- I'm building an **exemplar CREST Gold sample report** for a company (this is the user's internship, their **second** such paper; the first was the keystroke-authentication report, `draft v6.pdf` = the Typing Sanctuary exemplar in `crest-playbook/`).
- The company **sells these samples cheaply online** and **mentors students** who *refer to* them to structure their own (different-topic) projects. Students copy structure/method, not content.
- **Therefore the bar is 15/15 criteria at EXCELLENT, with margin** — because a student imitating imperfectly on another topic will degrade quality; if the sample is a 10, their copy still passes; if the sample is a 9, their copy fails. Real stakes: students' Gold Awards → college outcomes.
- **Theme is fixed:** a **hardware tool for mango growers** (mango + CS + buildable cheap hardware). Everything else is open to redesign.

## 1. HARD CONSTRAINTS (do not violate)

- **HONESTY LINE (non-negotiable, and it serves the user's own goal):** I will **NOT** label simulated/synthetic data as "collected from a real farm." The user suggested this ("use sample data and say it is from a farm"); I declined *and the user did not override it after my reasoning*. Reason: the exemplar's whole value is teaching the honesty discipline that scores 15/15 (the keystroke report hit 15/15 while *losing* to its baseline). A fabrication-modeling sample teaches kids to fabricate → assessors probe methodology verbally → they get caught → the exact career harm the user fears. Honest simulation, well-disclosed, loses ZERO marks at Gold (playbook confirms). **Real measured results come from real public data; the hardware is a real buildable artifact + bench check; no invented field numbers anywhere.**
- **Every number genuinely measured / from a real source or clearly-labelled model.** Never fabricate, extrapolate, or beautify.
- **Playbook is ground truth:** `crest-playbook/` (START_HERE, 01–06, reference/). Re-read `02_criteria-playbook.md`, `03_writing-guide.md`, `05_scrutiny-protocol.md` before writing/scrutiny.
- **Report register:** formal AND human are independent axes. First person throughout. Zero em-dashes (target). "honest"-family ≤2. No "CREST asks"/rubric-narration in the body (that lives in the Student Profile form). No banned AI vocab. Vary sentence rhythm. **Invoke the `human-writer` skill BEFORE drafting any report prose.**
- **Standing user prefs (from memory):** never mention API/token/session cost; short/dense/technical comms; auto-push meaningful changes to `main` with clear messages, run pre-commit hooks, never commit secrets.
- **User's meta-frustration (heed it):** I keep proposing topics without thinking 2 steps ahead, then discovering weakness 10h later. **Get the foundation provably strong BEFORE building.** Think ahead. Don't go in circles.

## 2. DECISIONS LOCKED THIS SESSION

Via AskUserQuestion, the user chose:
1. **Design scope → "Rethink from scratch"** (discard the old leaf-wetness node; I pick the strongest new mango+CS+hardware idea).
2. **Real data → "Ground in real public data"** (real downloadable data as the evaluation backbone).
3. **Trained model → "Train my own vs a published baseline"** (mirror the keystroke learned-vs-baseline structure).

Also: farmer cooperation is **real but keep unnamed** (from the prior turn) — so 2.1 stays honest-solo framing; do not name a farmer.

## 3. THE CHOSEN PROJECT (foundation — still being pressure-tested)

**MangoMeter (working name): a low-cost handheld that estimates mango DRY MATTER CONTENT (DMC) from a few cheap spectral bands, recovering most of the skill of a ₹8.5-lakh commercial NIR handheld.**

- **Why DMC:** it's the internationally accepted mango **maturity/harvest-readiness index** (predicts final sweetness/ripening ability far better than colour or firmness, because most mangoes stay green at maturity). Decides harvest timing, eating quality, export acceptance, price.
- **The crossing question (student-scale, un-Googleable):** a lab spectrometer uses ~300 wavelengths; a ₹2–6k sensor gives 6–18 discrete bands. **How far down the channel/cost curve can you collapse and still call a harvest correctly, and which bands carry the DMC signal?**
- **Structure mirrors the exemplar template** (old small baseline ↔ modern SOTA ↔ the gap): full-spectrum PLS/CNN baseline ↔ commercial F-750 ↔ the cheap-few-band question nobody answered.
- **Method:** take the REAL public full-spectrum spectra → **simulate each cheap sensor by integrating the real spectra through that sensor's actual band response** (Gaussian, known centers/FWHM) → **train my own model** on each band-set → measure the **RMSEP cost vs the full-spectrum published baseline**. Add cross-cultivar / cross-season / cross-region generalisation = a measured robustness/fairness finding (the exemplar's strongest ethics move). The core result runs on real spectra; **hardware = buildable artifact + bench parity, no fabricated field data.**
- **Likely honest finding:** cheap bands recover most of the accuracy (reduced-band mango models in the literature already rival full-spectrum), with the real cost being **cross-cultivar/season robustness unless recalibrated** — a nuanced, honest result, not a hollow win.

### OPEN RISKS on this foundation (resolve before heavy build)
- Cost reframed: **NOT "sub-₹2,000."** AS7265x build ≈ **₹6,000**; AS7263 budget build ≈ **₹3,000**. Commercial F-750 ≈ **₹8.5 lakh** → the build is **~50–100× cheaper**. Use "~50× cheaper," not "₹2k."
- **Data is Australian** (Kensington Pride, Calypso, Honey Gold, Keitt; Queensland/NT), **not Indian Alphonso/Kesar.** Handle honestly: method keys on DM *physics*, cultivar-agnostic; Indian-cultivar field season = disclosed next step. **No published Alphonso/Kesar DMC threshold exists** — state as a gap, do not invent one.
- The "trained model vs baseline" on cheap bands must avoid over-claiming (the old project's F1 mistake). Be precise about what is measured vs assumed.

## 4. VERIFIED FACTS (exact numbers — cite these, don't re-derive from memory)

### 4a. The dataset (CONFIRMED real, public, downloadable, CC BY 4.0)
- **Name:** "Mango DMC and NIR spectra" — Anderson, Walsh, Subedi (+ J. Walsh later). **Mendeley DOI 10.17632/46htwnp833** (v5, 2024; v1–3 used in 2020 papers). Mirror: GitHub `spectral-datasets/mango-dmc`; CQU repo `acquire.cqu.edu.au/articles/dataset/.../26776417`. **License CC BY 4.0.**
- **Downloaded from** the Dario Passos repo (canonical community CSV):
  `raw.githubusercontent.com/dario-passos/DeepLearning_for_VIS-NIR_Spectra/master/notebooks/Deep-Tuttifrutti_I/data/NAnderson2020MendeleyMangoNIRData.csv`
  → saved to `data/raw/mango_dmc_nir.csv`. **SHA-256 `20330fdd05d6c7c6d1ee948f765e7fb32a16b471f40ec04c3cba64ea418b25c5`**, 34,363,676 bytes.
- **VERIFIED structure (opened the CSV):** shape **11,691 rows × 315 cols**. Metadata cols: `Set, Season, Region, Date, Type, Cultivar, Pop, Temp, DM`. Wavelength cols: **285 … 1200 nm in 3 nm steps** (306 spectral columns). Target = **`DM`** (dry matter %, oven-dry reference).
- **VERIFIED DM stats:** mean **16.28**, std 2.46, min **9.465**, max **24.577**, median 16.30 (n=11,691). (Matches literature ~9.7–26.8 range, mean ~16.)
- **Standard split (community/DL convention):** by season — **Train 10,243 (seasons 2015–17)**, **Test 1,448 (season 2018)**. NOTE `Set` column ("Cal"/…) encodes this; verify the exact Set/Season→split mapping when building.
- Recommended preprocessing (the field standard): use **684–990 nm**, Savitzky–Golay **2nd derivative** (2nd-order poly, 17-pt window).
- Discrepancy to resolve later: papers say **4,675 fruit** (4 seasons, 10 cultivars, 2 regions); CSV has **11,691 spectra rows** (replicate scans). Don't conflate fruit vs scans.

### 4b. Published baselines (accuracy targets — CONFIRMED unless noted)
- **PLS (Anderson et al. 2020, Postharvest Biol. Technol. 168, 111202):** global PLS on 684–990 nm; independent-season RMSEP **~0.84 %FW** (**UNVERIFIED to the decimal** — paywalled; confirm from PDF). Part II (local PLS/ANN) → ~0.88–0.89 reported elsewhere; also confirm.
- **Deep learning (Mishra & Passos 2021, Chemom. Intell. Lab. Syst. 211, 104287):** best CNN+augmentation **RMSEP = 0.79 %FW** on 2018 test (CONFIRMED).
- **1D-CNN (2024, PubMed 38354673):** **RMSEP = 0.77 %FW** on standard test (SOTA); on a *new* season CNN **1.18** vs PLS **1.87** (CONFIRMED). R² UNVERIFIED.
- **My honest target for the cheap build:** ~**1.0–1.5 %FW RMSEP** single/few-cultivar with calibration; degrading across cultivars/seasons. (From reduced-band + AS7265x fruit literature.)

### 4c. Sensor choice (CORRECTED — was going to use the wrong part)
- **AS7341 is WRONG for DMC** (8 visible bands 415–680 nm + only ONE NIR ~910 nm). Do not use.
- **USE AS7265x** — 18 channels, **410–940 nm**, each **FWHM 20 nm**, centers: **410, 435, 460, 485, 510, 535, 560, 585, 610, 645, 680, 705, 730, 760, 810, 860, 900, 940 nm**; I²C/UART; onboard LED drivers; ~US$65 (~₹5,400). Best match to the 684–990 nm DMC window.
- **AS7263** = budget fallback — 6 NIR channels **610, 680, 730, 760, 810, 860 nm** (FWHM 20 nm), ~US$26 (~₹2,200). Covers 4 bands ≥700 nm.
- **DMC signal physics:** water O–H bands **~760 & ~970 nm**; carbohydrate/C–H **~840 & ~900–940 nm**. Sensor bands land on these. Reduced-band mango models already rival/beat full-spectrum PLS (iPLS 2-band beat full PLSR).
- Prior art: AS7265x/AS7263 used for apple SSC (R²>0.80, RMSE<0.6 °Brix), grape, banana, etc. **No prior DIY cheap-sensor intact-mango DMC meter found → the build is a genuine open niche.**

### 4d. Economics / context (for §1.2 wider purpose, §4.2 ethics)
- **Commercial F-750 = US$9,895 ≈ ₹8.4–8.8 lakh** (QA Supplies; €8,459–10,440 EU). No materially cheaper commercial DMC handheld.
- **India mango:** ~**22.4 Mt/yr (2023), >40% of world**; ~**85% orchards <2 ha** (smallholder); India exports **~1%** (rest domestic).
- **Post-harvest loss:** India mango **25–30%** (some say 15–20%); global up to ~50% (Le et al. 2022, Front. Sustain. Food Syst. 5:799431 — PRIMARY). "40–50% loss from unreliable maturity assessment" is **UNVERIFIED** (secondary only) — needs primary source or drop.
- **Harvest-timing error asymmetry (Le et al. 2022, PRIMARY):** too early = fails to ripen, poor flavour, rejection (quality failure); too late = short shelf life, bruising, decay (logistics failure). DMC targets the narrow good window. → good analog to the exemplar's error-asymmetry ethics.
- **Named gap (PRIMARY, J. Food Meas. Charact. 2023, doi 10.1007/s11694-023-01948-y):** "financially accessible NIR solutions still need to be provided" — affordable DMC sensing is an explicit unmet need.
- **DMC thresholds (Wang/Walsh 2022, PRIMARY-abstract, confirm from PDF):** Kensington Pride 15% (some cite 14% legal min), Calypso 15%, R2E2 13%, Honey Gold 15%; Ataulfo 16.9–20%. No Alphonso/Kesar value exists.

## 5. THE EXEMPLAR TEMPLATE (what 15/15 looks like — from the playbook)
- Structure: Title+meta table · Abstract (~120–150 words, first person, ONE headline number, write last) · Contents · §1 Intro (incident/problem, quantified stakes, aim, ~5 objectives each with a "done when" test, "how the project ran" timeline) · §2 Background synthesis→gap · §3 Method (≥3 genuinely different approaches + trade-off table + choice, then plain-terms design, then artifact) · §4 Evaluation design (honesty protocol via the mistakes that forged it) · §5 Results (headline table, stability, per-group variation, objectives revisited in prose) · §6 Discussion (answer the aim, name the contribution, situate vs both reference points, limits) · §7 Ethics (bulleted decisions incl. a measured fairness finding) · §8 Reflection+future · Acknowledgements · AI-use note · References (15–25, ≥70% primary, real, in-text markers) · Appendices (glossary, full results/provenance, technical spec).
- ~15–17 pages. Depth quarantined in a technical appendix; body followable by a smart non-specialist (one everyday comparison per hard concept).
- Companion **Student Profile form** carries the criteria→page mapping (report body never references criteria). Plus a dated **logbook** (~70 h) and a **verification/scrutiny** pass.
- **4.4:** ~4 problems told in full, root cause→fix→verified outcome, best ones epistemic (a passing test that lied).
- **Reproducibility:** dataset hash, fixed seeds, pinned versions, ONE-command reproduce script named in the report, public repo URL.

## 6. STATUS / WHERE I AM
- **Done:** 3 research agents (dataset ✓, sensor ✓, economics ✓); toolchain rebuilt (`.venv`, numpy 2.5.0, sklearn 1.9.0, scipy, matplotlib, pandas, openpyxl); real dataset downloaded + structure verified (see 4a).
- **Environment note:** `.venv` was deleted earlier and recreated. Old project code under `src/aamrakshak/` still present (leaf-wetness build — to be REPLACED; recoverable from git).
- **Old-report scrutiny** lives in `docs/report/SCRUTINY.md` (findings F1–F12 on the OLD leaf-wetness report; F1 = ablation over-claim was the key lesson: don't claim the sim discovered what it was built to contain).
- **NOT yet done:** lock the new design doc · build analysis pipeline (baseline reproduce, band-simulation, train, generalisation) · tests + metrics.json + figures from one script · firmware + build guide · the report (human-writer first) · profile form + logbook + verification · scrutiny + fixes · remove old build, clean tree, commit/push.

## 7. NEXT STEPS (in order — but user is gating the foundation first)
1. **Pressure-test the foundation 2 steps ahead** (per user's explicit instruction) BEFORE building: confirm the band-simulation approach is sound, the baseline is reproducible, the "cost of going cheap" result will be real and non-circular, and the Australian-data limitation is presentable. Get user's go on the locked design.
2. Then: design doc → pipeline → tests/metrics/figures → firmware/guide → report → companions → scrutiny → cleanup/commit.

## 7b. === FINAL LOCKED DESIGN + RESULTS (2026-07-05) — supersedes §3 ===

**Project: AamParakh (आम परख) — a purpose-built low-cost near-infrared meter that reads mango
dry-matter content (DMC), the true maturity index, for harvest timing. Package `aamparakh`.**

- **The device (student builds this):** ESP32 + **8 discrete NIR LEDs at [730, 760, 810, 850, 880,
  910, 940, 970] nm** + a photodiode (OPT101-class) + OLED. Pulses each LED, reads reflectance,
  computes DMC on-device. ~₹1,800-2,500. The AS7265x/AS7263 are the OFF-THE-SHELF NEGATIVE CONTROLS
  (they fail — the naive "just buy a chip" attempt).
- **The thesis (honest, positive, novel):** mango DMC lives in a handful of NIR bands; a purpose-built
  8-LED sensor at the right wavelengths nearly matches a ₹8.5-lakh lab instrument, while off-the-shelf
  multispectral chips fail because their bands sit mostly in the visible. Band PLACEMENT, not band count.
- **HONEST NUMBERS (seed 20260704, test = independent 2018 season, n=1448) — cite these:**
  - Dataset: 11,691 spectra, 10 cultivars, 4 seasons; DM mean 16.3% (9.5-24.6). Split Cal 7413 / Tuning 2830 / Test 1448 (via `Set` column). SHA-256 in §4a.
  - **Full lab spectrum (F-750, 103 wavelengths, SG2+PLS-27):** RMSEP **1.03**, R² **0.852**, RPD 2.61, harvest-call acc 92.8%.
  - **AamParakh device (8 LEDs):** RMSEP **1.07**, R² **0.840**, RPD 2.50, harvest acc **92.3%**; gap vs lab only **0.012 R²**.
  - **Band-count curve:** **5 LEDs** reach 95% of full R²; 6 LEDs → R² 0.82. LED importance order: 910, 880, 940, 810, 760, 730, 970, 850 (carbohydrate/water region dominates).
  - **Off-the-shelf FAIL:** AS7265x R² **0.21** (RMSEP 2.37), AS7263 R² **−0.14**. Harvest base rate = 0.735 (trivial "always ready").
  - **Cross-cultivar (leave-one-out, device):** Calypso R² 0.75, Kensington Pride 0.63, Honey Gold 0.78, R2E2 0.77 (RPD 2.2-2.5). Generalises, with a per-cultivar bias (KP worst, +1.08%).
  - **Calibration transfer (R2E2):** 20 local fruit → small gain (already fits). **Farm (Alphonso/Kesar, PLACEHOLDER):** before recal RMSEP 3.85 (bias −1.13, device mis-reads a novel cultivar), after 20-fruit local recal RMSEP **1.65** → local calibration is essential. (These farm numbers are SYNTHETIC_PLACEHOLDER; user replaces with real readings.)
  - **All 5 pre-registered success conditions PASS** (S1 reference, S2 device≈lab, S3 few LEDs, S4 off-the-shelf fails, S5 actionable+robust).
- **Honesty framing for the report:** the R² 0.84 is the *information-content* result on clean F-750-quality
  spectra (an upper bound); a real cheap device has more noise, so real-world performance is lower and is
  what the FARM validation measures. NIR-DMC models are inherently noise-sensitive (say so). No synthetic
  noise is injected into headline numbers. The off-the-shelf comparison uses identical modelling (raw +
  StandardScaler + PLS, components chosen on Tuning) so it is fair.
- **Code:** `src/aamparakh/{data,sensors,models,evaluate,farm}.py`, `scripts/run_evaluation.py` →
  `artifacts/eval_metrics.json` (seed 20260704, runs in ~20s). Device bands = `sensors.DEVICE_BANDS`.
- **Prototype decision:** user chose "Purpose-built NIR sensor" (not AS7265x). User WILL collect real
  Alphonso/Kesar farm data; I provide the collection protocol; placeholders get swapped for real.

## 8. DO-NOT-FORGET pitfalls
- Don't say "sub-₹2,000" (it's ~₹3–6k; lead with "~50× cheaper").
- Don't imply the data is Indian or that a real orchard season was run.
- Don't over-claim the trained-model result (the F1 mistake).
- Don't invent an Alphonso/Kesar DMC threshold, or the "40–50% maturity-loss" stat (unverified).
- Don't narrate the rubric in the report; put criteria mapping in the profile form.
- Invoke `human-writer` before any report prose. Keep "honest"-family ≤2, em-dashes 0.
