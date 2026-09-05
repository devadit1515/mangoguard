# AamGanak

Estimating how many mangoes a tree carries from a short walk around it with a camera,
including the fruit no viewpoint ever sees.

Fruit detectors are close to perfect at finding the mangoes that are visible in an image.
A tree hides most of its own crop behind leaves, branches and other fruit, so the visible
count is not the crop, and the standard correction multiplies it by a constant fitted on a
few trees. This project treats the problem the way ecologists treat counting animals that
hide: every camera position is a survey occasion, the pattern of which viewpoints saw
which fruit says how detectable fruit are, and the reconstructed canopy says how much of
the tree no camera could see into at all.

## State

Simulation stage complete. Real-orchard validation waits for the Alphonso season in early
2027, because the ground truth for a tree is obtained by picking it and counting.

- `PROJECT_DEFINITION.md` — aim, objectives, pre-registered success conditions, written
  before the code and amended by appending, never by rewriting.
- `FIX_LOG.md` — every defect found, with cause, fix and verification. Three of them were
  in the physics of the simulator and one was in the project's premise.
- `artifacts/sim_metrics.json` — every number, from one seeded run.

## Reproduce

```
python scripts/run_simulation_study.py     # writes artifacts/sim_metrics.json (seed 20260903)
python -m pytest tests -q                  # 20 tests, including the analytic physics checks
```

Requires numpy, scipy and pytest.

## Layout

```
src/aamganak/canopy.py       canopy geometry, fruit placement, Beer-Lambert attenuation
src/aamganak/visibility.py   the foliage grid, ray marching, detection histories
src/aamganak/estimators.py   naive, fixed multiplier, capture-recapture, Chao,
                             Horvitz-Thompson, geometry-informed
scripts/                     the study that scores them all on identical trees
tests/                       analytic checks on the simulator, behaviour checks on estimators
```

## What the simulator is for

The estimator has to be judged against a truth, and on a real tree the truth costs a
harvest. So development runs on simulated trees whose count is known by construction, and
the real orchard is kept for the final test rather than spent on debugging.

That only works if the simulator is honest, which is why the foliage is a fixed object
rather than a per-viewpoint probability. Leaves do not rearrange themselves between camera
positions, so occlusion is deterministic given the geometry and correlated across nearby
views. Drawing it independently per view, which is what the first version did, turns a
fruit with a 30% chance per view into one that is near-certain to be seen across twelve,
and makes the whole problem look solved before it is asked. The canopy is now built once
per tree as a grid of cells that are foliage or air, clumped at roughly the scale of a
shoot, and every line of sight is traced through that one realisation. Cell occupancy is
set so the mean transmittance still matches Beer-Lambert, which the test suite checks
against the closed form.
