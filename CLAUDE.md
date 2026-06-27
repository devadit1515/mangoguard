# CLAUDE.md — AamRakshak (flagship CREST Gold *sample* build)

> **Authoritative brief:** `README.md` (the mission). **Locked design:** `docs/DESIGN.md`.
> This file is the running project memory. The old "MangoGuard" build (code, report, data)
> was removed from the working tree during cleanup; it is recoverable from git history
> (commit before `e046ef6`) if ever needed.

## Standing instructions (carry across sessions)
- **Auto-push every meaningful change** to `main` with a clear message; run pre-commit hooks; never commit secrets. Solo workflow, commit direct to `main`.
- **Never mention API/token/session cost.** Absorb any cost hooks silently.
- **Communication:** short, dense, technical; match length to the question; insights as bullets.
- The anti-AI-writing rules in `AI Writing.md` apply to **the report**, not to chat or internal docs.

## What the project is now
**AamRakshak (आम रक्षक, "mango protector")** — a sub-₹2,000 open-source ESP32 leaf-wetness + microclimate sensor node that predicts mango **anthracnose** infection windows well enough to cut needless calendar fungicide sprays. Variety- and region-agnostic (anthracnose is near-universal across Indian mango; the model keys on microclimate, not cultivar). Konkan Alphonso = primary testbed; Gujarat/Kesar = the contrast region for generalisation.

**The thesis:** the old project's own evaluation proved leaf wetness is the signal that lifts disease-prediction AUC from chance to useful — then assumed a ₹40k+ commercial station to supply it. AamRakshak builds that signal for ₹2k, for the millions of smallholders who spray on a fixed calendar.

**Hardware (mandatory, ≤8h build):** ESP32 + SHT31 (T/RH) + DIY interdigitated resistive **leaf-wetness sensor** (the star) + DS18B20 + OLED (offline risk readout) + 18650/solar + radiation shield. Computes the Akem model on-device.

## Locked decisions
- Scope: **lean, hardware-focal** (one tight question, depth > breadth). Dropped the MRL recommender, chatbot, yield/price, 5-connector zoo.
- Kept from old work: Akem (2006) humid-thermal-ratio anthracnose model; ROC-AUC/Brier evaluation discipline; honest simulation methodology (independent outbreak generator → non-circular backtest).
- Package renamed `mangoguard` → `aamrakshak`. Clean tree.

## Pre-registered success conditions (all currently PASS)
- **S1** leaf wetness decisive: node ROC-AUC ≥ 0.75 and node−free gap ≥ 0.10.
- **S2** cheap node ≈ ₹40k station: commercial−node ≤ 0.05 AUC.
- **S3** DIY sensor trustworthy: ≥ 90% wet/dry accuracy (bench).
- **S4** fewer sprays, no missed windows: ≥ 30% spray cut + ≥ 90% high-risk coverage.
- **S5** generalises: within-region AUC ≥ 0.75 on both regions, agreeing within 0.05.

## Headline results (real outputs of `scripts/run_evaluation.py`, seed 20260627, n=2400 block-days)
- Tier ROC-AUC: calendar 0.753 · free district feed 0.753 · **node 0.857** · commercial 0.864.
- Ablation: removing leaf wetness drops AUC 0.073; every other feature ≤ 0.004 (thesis, quantified).
- Calibration (Platt): node Brier 0.254 → 0.146 on held-out season.
- Leaf-wetness sensor: 92.8% bench accuracy; drift 99%→68% by wk 8 without recal, recovered to ~95% with recal.
- Spray reduction: 33.7% fewer sprays overall, high-risk coverage 0.994 (Konkan 25.7%/1.0; Gujarat 41.7%/0.99). Honest nuance: bigger savings in drier regions; humid regions already near-optimal on calendar.

## Repo map (current)
- `docs/DESIGN.md` — locked design. `docs/report/` — CREST report (to write) + blank profile templates.
- `src/aamrakshak/` — `riskengine/` (anthracnose, leafwetness, ppi), `sim/` (weather, outbreaks, sensors), `eval/` (metrics, tier_study, calibration, spray_reduction, leafwet_validation, ablation), `io/` (ingest).
- `scripts/run_evaluation.py` → `artifacts/eval_metrics.json`. (figures script + firmware + app: to build)
- `tests/` — 33 passing; metrics cross-checked vs scikit-learn; pipeline asserts S1–S5.
- Reference docs (keep): `README.md`, `AI Writing.md`, `../CREST_Gold_Award_Guide.md`, `CREST_Official_Guidelines_Research.md`, `CREST_Precedents_And_Patterns.md`.

## CREST writing reminders (from the guide; for the report)
- 15 criteria, all at "excellent". 1.3 (≥3 approaches, most-missed) and 1.5 (Gantt planned-vs-actual) are easy to drop — don't. 4.1 = the maths (Akem derivation, sensor physics, ROC-AUC). 4.3 = name the creative choices. 4.4 = ≥3 problem arcs. Analysis section ≥ literature review length. Body ~4,500–6,000 words. Harvard refs, 15–25, ≥70% primary, all real.

## Build status / next
Done: design doc, risk engine, sim, full eval pipeline (S1–S5 pass), tests, repo cleanup.
Next: ESP32 firmware → figures from JSON → Streamlit app → hardware build guide → CREST report → Student Profile + logbook → self-critique ≥2 passes → verification gate.

## Change log
- 2026-06-27: Pivoted from MangoGuard (software-only, export-niche, no hardware) to **AamRakshak** (hardware-focal leaf-wetness early-warning, broad smallholder applicability, variety/region-agnostic). Archived old build. Built risk engine + sim + eval; all 5 success conditions pass on honest simulated/bench data.
