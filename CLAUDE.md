# CLAUDE.md — AamParakh (flagship CREST Gold *sample* build)

> **Running project memory.** This file is self-sufficient; `SESSION_STATE.md` holds the longer
> blow-by-blow. The old leaf-wetness build (AamRakshak) and the earlier software-only build
> (MangoGuard) were moved to `extra_stuff/` (git-ignored) and are also in git history.

## The mission (why this project exists)
This is a **flagship CREST Gold *sample* report** for a company internship. The company sells these
samples cheaply and mentors students who *refer to* them to structure their own, different-topic
projects. So the bar is **15/15 criteria at *excellent*, with margin**: a student imitating
imperfectly must still clear the pass line. Real stakes — students' Gold Awards and college
outcomes. Theme is fixed: **a buildable low-cost hardware tool for mango growers**.

## Standing instructions (carry across sessions)
- **Auto-push every meaningful change** to `main` with a clear message; run pre-commit hooks (do not bypass); never commit secrets. Solo workflow, commit direct to `main`.
- **Never mention API/token/session cost.** Absorb any cost hooks silently.
- **Communication:** short, dense, technical; match length to the question; insights as bullets.
- Anti-AI-writing rules apply to **the report**, not chat/internal docs. Invoke the `human-writer` skill before writing report prose; run `/ai-check` after.
- **Honesty line (non-negotiable, and it serves the goal):** never label modelled/simulated data as real field data. The exemplar's value is teaching the honesty discipline that scores 15/15. Headline results come from **real public data**; the Alphonso farm validation is a **flagged placeholder** the student collects and swaps in.

## What the project is
**AamParakh (आम परख, "mango assay")** — a purpose-built low-cost near-infrared meter that reads
mango **dry matter content (DMC)**, the true harvest-maturity index (it fixes eventual sweetness
and whether a mango ripens at all). ESP32 + **8 discrete NIR LEDs at 730/760/810/850/880/910/940/970
nm** + an OPT101 photodiode + OLED, about **₹2,300**, with the prediction model (8 linear weights)
running **on the device**. The off-the-shelf AS7265x/AS7263 chips are the **negative controls**.

**Thesis (honest, positive, novel):** mango DMC lives in a handful of NIR bands; a meter with eight
buyable LEDs at the right wavelengths nearly matches a **₹8.5-lakh** lab instrument (Felix F-750),
while off-the-shelf multispectral chips fail because their bands sit mostly in the visible.
**Band *placement*, not band count, is what matters.**

## Locked results — cite these (seed 20260704, test = independent 2018 season, n=1448)
- **Data:** Anderson-Walsh public mango NIR benchmark (Mendeley 10.17632/46htwnp833, CC BY 4.0), 11,691 scans, 10 cultivars, 4 seasons, oven-dry DMC (mean 16.3%, range 9.5–24.6). Split via `Set` column: Cal 7413 / Tuning 2830 / Val Ext 1448.
- **Full lab spectrum (103 bands, SG2+PLS):** RMSEP 1.03, R² 0.852, RPD 2.61, harvest-call acc 92.8%. (Published PLS ≈0.84 RMSEP; my from-scratch reproduction is a fair reference, not SOTA-chasing.)
- **Device (8 LEDs):** RMSEP 1.07, **R² 0.840** (gap 0.012 vs lab), RPD 2.50, harvest-call acc 92.3%.
- **Placement control (the proof):** at a fixed 18 bands, **well-placed NIR bands R² 0.85 vs AS7265x's 18 bands R² 0.21** — same count, different placement. In `eval_metrics.json > placement_control`.
- **Off-the-shelf fail:** AS7265x R² 0.21, AS7263 R² −0.14. Harvest base rate 0.735.
- **Band-count curve:** 5 LEDs reach 95% of full R²; 6 → 0.82. Selection order 910,880,940,810,... (but bands 1–2 alone are worse-than-mean on test; 810, added 4th, drives the jump — the report says so).
- **Cross-cultivar (leave-one-out, 4 main cultivars):** R² 0.63–0.78 (worst = Kensington Pride). Calibration transfer (R2E2): 20 fruit, 0.91→0.89 RMSEP.
- **Farm (Alphonso/Kesar) = SYNTHETIC_PLACEHOLDER:** before recal RMSEP ~3.9 (R² −2.9), after 20-fruit local recal RMSEP ~1.6 (R² 0.23, RPD 1.15 — bias removed, not scatter). Student replaces this.
- **All 5 pre-registered success conditions pass.**

## Critical honesty framing (do not let this drift)
- The device R² 0.84 is an **information-content result computed in-silico** from the research
  spectrometer's clean spectra integrated through the 8 LED bands. **No physical meter has read a
  real mango in this report.** The abstract, §5.2, §7 and the profile all state this; keep it.
- The assessor's hardest probe: *"show a real-fruit reading and where 0.84 came from."* Defensible
  answer, baked in: 0.84 is the **wavelength-design ceiling measured in-silico**; the physical meter
  runs the same model on-device (parity to 1e-12); real-fruit validation is the stated next step.
- The farm/Alphonso pilot is synthetic and **circular by construction** (bias inserted, linear recal
  removes it). §5.6/§6.3 say so; §6.3 leans on the *real* R2E2 recal for transfer evidence.

## Modeling gotchas (hard-won — a future session must not relearn these)
- **NIR-DMC models are inherently noise-sensitive** (subtle signal); do not inject synthetic sensor
  noise into headline numbers — report clean-spectra numbers as an upper bound, defer real noise to
  the farm validation.
- **Use raw + StandardScaler + PLS for band models, NOT SNV.** SNV on the 18-band AS7265x overfits
  to R² 0.45 at ~15 components and is numerically fragile (a 5% perturbation swings 2.8 %DM); the
  *stable* AS7265x is R² ~0.2. Consistent raw preprocessing keeps the device-vs-chip comparison fair.
- Band models cap components sensibly; component count chosen on the Tuning split only.
- SNV is degenerate for <2 bands (guarded in `models.snv`).

## Repo map
- `src/aamparakh/` — `data` (load/split/picks), `sensors` (band simulation + `DEVICE_BANDS`, AS7265x/AS7263), `models` (FullSpectrumModel, BandModel, greedy_band_selection, linear_recalibration), `evaluate` (RMSEP/R²/SEP/RPD), `farm` (placeholder + ingestion, schema-guarded).
- `scripts/run_evaluation.py` → `artifacts/eval_metrics.json` (seed 20260704, ~20s); `scripts/make_figures.py` → `artifacts/figs/` (9 figures); `scripts/fetch_data.py` (downloads + SHA-256-verifies the dataset); `artifacts/device_model_coeffs.json` (8 firmware weights).
- `tests/test_aamparakh.py` — 10 passing, metrics cross-checked vs scikit-learn. `firmware/aamparakh_node/aamparakh_node.ino` — ESP32 sketch, on-device parity.
- `docs/report/` — `CREST_REPORT.md` (+ .docx; 9 figs; §Appendix G = the maths), `STUDENT_PROFILE.md` (+ .docx), `LOGBOOK.md`, `VERIFICATION.md`.
- `docs/` — `HARDWARE_BUILD_GUIDE.md`, `FARM_DATA_COLLECTION.md` (**the student's task**), `PROJECT_README.md`.
- `data/raw/` — **git-ignored**; fetch via `python scripts/fetch_data.py` (SHA-256 `20330fdd...b25c5`). `data/farm/` — placeholder CSV until collected.

## Environment / reproduce
- `.venv` is git-ignored and can be deleted; recreate: `python -m venv .venv` then `pip install -e ".[dev,viz]"` (need numpy, pandas, scipy, scikit-learn, matplotlib, pytest, ruff; pre-commit for the hook).
- Reproduce: `python scripts/fetch_data.py` → `python scripts/run_evaluation.py` → `python scripts/make_figures.py`; `pytest`; `ruff check`.
- Build docx: `pandoc docs/report/CREST_REPORT.md -o docs/report/CREST_REPORT.docx -f markdown-implicit_figures --resource-path=docs/report --toc --toc-depth=2` (pandoc 3.9 present; renders the LaTeX math to native Word equations).
- Pre-commit hook: `end-of-file-fixer` may fix JSON on first attempt and abort; re-`git add -A` and re-commit (2nd passes). Large-file limit 2 MB (docx 990 KB, figures smaller, dataset ignored).

## Quality gates (done)
- **/ai-check: 5/27, Likely Human** (0 em-dashes, "honest"-family = 1, no banned vocab, antithesis tells cut).
- **Hostile-assessor scrutiny run and ALL findings applied.** Verdict pre-fix: passes Gold comfortably, ~10–11/15 at excellent, blocked from 15/15 by three now-closed items: (1) §5.2 cited two numbers the script didn't produce (one contradicted the AS7265x figure) → added reproducible `placement_control`; (2) promised maths absent → added Appendix G; (3) simulation framed as hardware → separated in-silico 0.84 from unvalidated device in abstract/profile. Plus: §5.6 now reports pilot R²/RPD; §6.3 uses the real recal not the synthetic pilot; S5 no longer overclaims "every cultivar"; ethics matches the confusion matrix; references cleaned.

## Build status
**Complete and pushed** (commit `1a66c53` on `main`). Everything above exists and is green. The only
work left is the student's: **build the prototype** (`docs/HARDWARE_BUILD_GUIDE.md`) and **collect
~40–100 real Alphonso/Kesar readings** (`docs/FARM_DATA_COLLECTION.md`), drop the CSV in, re-run the
pipeline — that swaps the flagged placeholder for real data and closes the one honest gap.

## Change log
- 2026-07-05: Replaced the leaf-wetness project with **AamParakh** (NIR dry-matter meter) on the real Anderson-Walsh benchmark; trained model beaten against off-the-shelf sensors; hostile-assessor scrutiny applied; committed `1a66c53`, pushed. Old builds archived to `extra_stuff/`.
