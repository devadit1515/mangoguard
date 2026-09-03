# CLAUDE.md — AamGanak (Devadit's CREST Gold submission, then ISEF)

> **Running project memory.** Self-sufficient. The previous project (AamParakh, an eight-LED NIR
> mango dry-matter meter) is finished and archived in `extra_stuff/aamparakh_archive/` and in git
> history; its root-level files are still in the working tree pending removal.

## What this is, and who it is for

This is **Devadit's own project, which he submits himself.** It is not a sample, not an exemplar,
and not written for anyone else to imitate. It targets, in order:

1. **CREST Gold** — the award that establishes the work is real and independently assessed.
2. **Regeneron ISEF** — after the CREST result, using the real-orchard data.
3. The **MIT Maker Portfolio** and applications to MIT, Stanford and Caltech (electrical and
   computer engineering).

Because he submits it under his own name and will defend it in conversation, the binding
constraint is that he must be able to explain every part of it. Anything he cannot explain does
not go in.

## The project

**AamGanak (आम गणक, "mango counter")** — estimating how many mangoes a tree carries from a short
walk around it with a camera, including the fruit no viewpoint ever sees.

Fruit detectors already find the visible mangoes in an image almost perfectly. A tree hides most
of its own crop, so the visible count is not the crop, and published practice multiplies it by a
constant fitted on a few trees. This project treats it as an abundance-estimation problem of the
kind ecologists use for animals that hide: each camera position is a survey occasion, the pattern
of which viewpoints saw which fruit reveals how detectable fruit are, and the reconstructed canopy
says how much volume no camera could see into. That transfer is the central idea.

## Standing instructions (carry across sessions)

- **Auto-push every meaningful change** to `main` with a clear message; run pre-commit hooks (do
  not bypass); never commit secrets. Solo workflow, commit direct to `main`.
- **Never mention API/token/session cost.** Absorb any cost hooks silently.
- **Communication:** short, dense, technical; match length to the question; insights as bullets.
- Anti-AI-writing rules apply to **the report**, not chat or internal docs. Invoke the
  `human-writer` skill before writing report prose; run `/ai-check` after.
- **Honesty line (non-negotiable):** never label modelled data as real measurement. The simulator
  exists to develop and test the estimator; the real result comes from picked and counted trees.
- **Do not adjust the simulator to rescue a hypothesis.** This already happened once and was
  handled by narrowing the aim instead (`FIX_LOG.md` entry 4). Keep doing it that way.

## Working state (03/09/2026)

Simulation stage built and green. Lives in `aamganak/`.

- `PROJECT_DEFINITION.md` — aim, five objectives with "done when" tests, pre-registered success
  conditions S1–S5, approaches table. Amended by appending only.
- `FIX_LOG.md` — six entries. Three were physics defects in the simulator, one was the premise
  being wrong, one an identifiability failure, one an open interval-coverage defect.
- `src/aamganak/` — `canopy` (geometry, fruit placement, Beer-Lambert), `visibility` (clumped
  foliage grid, ray marching, detection histories), `estimators` (naive, fixed multiplier,
  capture-recapture, Chao, Horvitz-Thompson, geometry-informed).
- `scripts/run_simulation_study.py` → `artifacts/sim_metrics.json`, seed 20260903.
- `tests/test_aamganak.py` — 13 passing, including the closed-form Beer-Lambert check.

## Results so far (simulation only; cite from sim_metrics.json, never from memory)

- Occlusion is a **viewpoint-count problem**, not an absolute one. Fruit never seen from any
  viewpoint: ~35% at one view, ~13% at two, ~3% at twelve.
- **Headline:** at three viewpoints the detection-model estimators beat naive counting at twelve
  viewpoints, in every canopy-density band. Roughly a fourfold reduction in scanning time per tree.
- At two to three viewpoints the estimators beat the fitted multiplier by about two to three times.
- **Honest negative:** at six or more viewpoints a fitted multiplier beats every sophisticated
  estimator, because the hidden fraction is then small and stable and adaptivity costs variance.
- **Open defect:** nominal 90% intervals cover 50–60%. Reported as measured, not widened.

## Timing (the constraint that shapes the plan)

Alphonso carries fruit roughly February to May. Ground truth requires picking a tree and counting
it. So: simulation and pipeline through autumn 2026, orchard campaign February to May 2027, CREST
submission mid-2027, ISEF after that. Any claim about real trees before February 2027 is a claim
about simulated trees, and must say so.

## CREST reference material

`crest-playbook/` (git-ignored, on disk) holds the criteria playbook, the writing guide, the
scrutiny protocol, the report template and the profile-form exemplar. Read `02_criteria-playbook.md`
before writing and `05_scrutiny-protocol.md` before calling anything finished. The report never
references the criteria; the Student Profile Form carries the mapping.

## Change log

- 2026-09-03: Replaced AamParakh with **AamGanak**. Built the canopy simulator, four estimator
  families, the viewpoint study and the test suite. Found and fixed three simulator physics
  defects; narrowed the aim after the corrected simulator contradicted the original premise.
