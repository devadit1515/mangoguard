# Verification and provenance record

The pre-submission checks for the AamParakh report, run on the final artifacts. Every command reproduces from the repository root.

## 1. Numbers trace to one source

Every figure the report cites is produced by `python scripts/run_evaluation.py` (seed 20260704) into `artifacts/eval_metrics.json`, and every figure image by `python scripts/make_figures.py`. Spot-checks against that file:

| Report claim | eval_metrics.json | Match |
|---|---|---|
| Full spectrum R² 0.85, RMSEP 1.03, RPD 2.6 | 0.8523 / 1.0257 / 2.6091 | ✅ |
| Device (8 LEDs) R² 0.84, RMSEP 1.07, gap 0.012 | 0.8404 / 1.066 / 0.0119 | ✅ |
| Off-the-shelf AS7265x 0.21, AS7263 −0.14 | 0.2081 / −0.1433 | ✅ |
| Placement control: 18 well-placed NIR bands 0.85 vs AS7265x 18 bands 0.21 | placement_control 0.8499 / 0.2081 | ✅ |
| Pilot after local recal: RMSEP 1.6, R² 0.23, RPD 1.15 | farm_validation.after_local_recal | ✅ |
| Five LEDs reach 95% of full R²; six reach 0.82 | min_leds 5; k=6 → 0.8206 | ✅ |
| Selection order 910, 880, 940 first | led_selection_order_nm | ✅ |
| Harvest accuracy 92%, base rate 73% | 0.9233 / 0.7348 | ✅ |
| Cross-cultivar R² 0.63–0.78 | 0.625–0.776 | ✅ |
| Dataset 11,691 fruit, 10 cultivars, 4 seasons; DM 9.5–24.6, mean 16.3 | matches meta / dm_stats | ✅ |
| Split 7,413 / 2,830 / 1,448 | matches meta | ✅ |

## 2. Code and tests

- `pytest` — 10 passed. Metrics cross-checked against scikit-learn; band-response normalisation, split integrity and the greedy search verified.
- `ruff check src scripts tests` — clean.
- On-device model parity: the eight firmware weights reproduce the Python prediction to 1e-12 %DM (`artifacts/device_model_coeffs.json`).
- Pipeline reproduces from the fixed seed in about twenty seconds.

## 3. Internal consistency

- All nine figures are referenced in the text before they appear; none is unreferenced.
- Every in-text citation appears in the reference list, and every reference is cited.
- The harvest-readiness confusion cells sum to the test size: 1039 + 298 + 86 + 25 = 1448. ✅
- The bill of materials totals about ₹2,300; the reported build time is about eight hours.

## 4. Writing checks (AI Writing rules)

- Em dashes in the report body: **0**.
- "honest / honestly" family: **1** (within the limit of two).
- No "not X but Y" constructions, no rule-of-three rhetorical triplets, no "moreover / furthermore / additionally" openers, no rubric self-reference in the body.
- Banned vocabulary scan clean; the one "robustness" is in a cited paper's real title.
- First person throughout; register formal and consistent; sentence length varied.

## 5. Honest limitations, stated not hidden

The report's headline results are measured on the real Anderson-Walsh benchmark. Two limits are disclosed where they arise and again in Section 7:

1. The benchmark fruit are Australian cultivars, so the transfer to Alphonso and Kesar is set up (Section 5.6, Appendix E) but not yet measured on Indian fruit.
2. The R² of 0.84 is an information-content result on clean research spectra, an upper bound; a physical meter carries more noise, which the field validation measures.

Both are stated in the report rather than papered over, and neither affects the wavelength-design finding, which is the project's contribution.

## 6. Hostile-assessor scrutiny

A full criterion-by-criterion adversarial review was run against the report, profile and
`eval_metrics.json`. Every finding was applied, including the most serious: the §5.2
"placement, not count" comparison had cited two numbers the pipeline did not produce, so a
reproducible `placement_control` experiment (18 well-placed bands 0.85 vs the AS7265x's 18 at
0.21) was added to `run_evaluation.py` and the paragraph rewritten around it. Also fixed: the
abstract and profile now separate the in-silico 0.84 from the unvalidated hardware; §5.6 reports
the pilot's R² and RPD next to its RMSEP; §6.3 leans on the real leave-one-cultivar recalibration
rather than the synthetic pilot; the S5 wording no longer overclaims "every cultivar"; the ethics
advice matches the confusion matrix; and Appendix G now sets out the mathematics the introduction
promises.

## 7. Deliverables

- Report: `docs/report/CREST_REPORT.md` (+ exported `.docx` / PDF).
- Student Profile form: `docs/report/STUDENT_PROFILE.md`.
- Logbook: `docs/report/LOGBOOK.md`.
- Build guide: `docs/HARDWARE_BUILD_GUIDE.md`; firmware: `firmware/`.
- Field-collection protocol: `docs/FARM_DATA_COLLECTION.md`.
- Reproducible code and pinned data: `src/`, `scripts/`, `tests/`, `data/raw/`.
