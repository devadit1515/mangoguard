# CLAUDE.md — AamParakh (flagship CREST Gold *sample* build)

> **Running project memory.** For the full session history, decisions, and exact verified
> numbers, read `SESSION_STATE.md` first. The old leaf-wetness build (AamRakshak) and an
> earlier software-only build (MangoGuard) were moved to `extra_stuff/` and are also in git
> history; the current project replaced them from scratch.

## Standing instructions (carry across sessions)
- **Auto-push every meaningful change** to `main` with a clear message; run pre-commit hooks; never commit secrets. Solo workflow, commit direct to `main`.
- **Never mention API/token/session cost.** Absorb any cost hooks silently.
- **Communication:** short, dense, technical; match length to the question; insights as bullets.
- The anti-AI-writing rules apply to **the report**, not to chat or internal docs. Invoke the `human-writer` skill before writing report prose; run `/ai-check` after.
- **Honesty line (non-negotiable):** do not label modelled/simulated data as real field data. Headline results come from real public data; the farm validation is collected by the student and swapped in for the flagged placeholder.

## What the project is
**AamParakh (आम परख, "mango assay")** — a purpose-built low-cost near-infrared meter that reads
mango **dry matter content (DMC)**, the true maturity index, for harvest timing. ESP32 + **8
discrete NIR LEDs at 730/760/810/850/880/910/940/970 nm** + an OPT101 photodiode + OLED, about
₹2,300, with the prediction model running on the device. The off-the-shelf AS7265x/AS7263 chips
are the negative controls (they fail).

**The thesis (honest, positive, novel):** mango DMC lives in a handful of NIR bands; a meter with
eight buyable LEDs at the right wavelengths nearly matches a ₹8.5-lakh lab instrument, while
off-the-shelf multispectral chips fail because their bands sit mostly in the visible. Band
*placement*, not band count, is what matters.

## Locked results (seed 20260704, test = independent 2018 season, n=1448)
- Data: Anderson-Walsh public mango NIR benchmark (Mendeley 10.17632/46htwnp833, CC BY 4.0), 11,691 scans, 10 cultivars, 4 seasons, oven-dry DMC. Split 7413/2830/1448.
- Full lab spectrum: RMSEP 1.03, R² 0.852. **Device (8 LEDs): RMSEP 1.07, R² 0.840** (gap 0.012), harvest-call acc 92.3%.
- Band-count curve: 5 LEDs reach 95% of full R². Off-the-shelf AS7265x R² 0.21, AS7263 −0.14.
- Cross-cultivar (leave-one-out): R² 0.63–0.78. Farm (Alphonso/Kesar) = flagged placeholder pending real collection; local recal cuts error from ~3.9 to ~1.6.
- All 5 pre-registered success conditions pass.

## Repo map
- `src/aamparakh/` — `data`, `sensors` (band simulation + DEVICE_BANDS), `models` (PLS, band search), `evaluate`, `farm` (placeholder + ingestion).
- `scripts/run_evaluation.py` → `artifacts/eval_metrics.json`; `scripts/make_figures.py` → `artifacts/figs/` (9 figures); `artifacts/device_model_coeffs.json` (firmware weights).
- `tests/` — 10 passing, metrics cross-checked vs scikit-learn. `firmware/aamparakh_node/` — ESP32 sketch.
- `docs/report/` — `CREST_REPORT.md` (+ .docx), `STUDENT_PROFILE.md` (+ .docx), `LOGBOOK.md`, `VERIFICATION.md`.
- `docs/` — `HARDWARE_BUILD_GUIDE.md`, `FARM_DATA_COLLECTION.md` (the student's task), `PROJECT_README.md`.
- `data/raw/mango_dmc_nir.csv` (SHA-256 pinned), `data/farm/` (placeholder until collected).

## CREST writing reminders (for the report)
- 15 criteria, all at "excellent". First person, formal + human. Zero em-dashes; "honest"-family ≤2; no rubric narration in the body (it lives in the Student Profile form). In-text citations; 15–25 real refs, most primary. Every figure referenced before it appears. Report body ~5,500 words.

## Build status
Done: full analysis + real-data results, figures, tests, firmware with on-device parity, report
(+.docx), profile form (+.docx), logbook, verification, build guide, farm-collection guide,
`/ai-check` (5/27, Likely Human). Next: fold in hostile-assessor scrutiny findings; then the
student collects real Alphonso/Kesar data and swaps it in for the farm placeholder.

## Change log
- 2026-07-05: Replaced the leaf-wetness project with **AamParakh** (NIR dry-matter meter), grounded in the real public Anderson-Walsh mango NIR benchmark, with a trained model beaten against off-the-shelf sensors. Old builds archived to `extra_stuff/`.
