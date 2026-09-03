# Fix log

Every defect found, with what it cost and how I know it is fixed. Numbered in the order
I found them. The report tells a few of these in full and points here for the rest.

---

## 1 — Occlusion drawn independently for each viewpoint

**Found:** 03/09/2026, on the first run of the simulation study.

**Symptom:** 86% of fruit came out visible, averaged over trees. Every estimator landed
within a few percent of the truth and the naive count was only 13.6% low, which made the
whole question look answered before it was asked.

**Root cause:** `visibility.detection_histories` drew a fresh Bernoulli trial for every
fruit and every viewpoint, using the Beer-Lambert transmittance along that line of sight
as the probability. That treats the foliage as if it were re-shuffled between viewpoints.
Real leaves do not move, so occlusion is deterministic given the geometry and strongly
correlated between neighbouring camera positions. Independent draws turn a fruit with a
30% chance per view into one with a 99% chance of being seen at least once across twelve
views, and a fruit buried in the canopy interior, which should be invisible from every
direction, became almost certain to be seen.

**Why it mattered:** it biased the study in favour of my own conclusion. An easy problem
makes every estimator look adequate, and it would have hidden the regime the project
exists to address.

**Fix:** the canopy is now built once per tree as a fixed grid of cells that are either
foliage or air, and every line of sight is ray-marched through that one realisation. Cell
occupancy is set to `1 - exp(-G * LAD * h)`, which reproduces the same Beer-Lambert
attenuation on average, so the physics is unchanged and only the correlation structure is
corrected.

**Verified:** visible fraction now falls with canopy density as it should, from near 1.0
on an open canopy to 0.60 at a leaf area density of 3.0, and the fraction of fruit with no
clear line of sight from any viewpoint rose from 0 to 0.39 on the densest trees.

---

## 2 — Foliage scattered rather than clumped

**Found:** 03/09/2026, immediately after fix 1.

**Symptom:** not a wrong number, a wrong model. Cell occupancy was drawn independently per
cell, making the foliage a fine uniform mist.

**Root cause:** leaves grow on shoots and shoots grow on branches, so foliage in a real
canopy is spatially correlated over roughly 20 cm. Canopy radiative-transfer models carry
a clumping index for exactly this reason: scattered-leaf theory gets gap statistics wrong
even when it gets mean density right.

**Fix:** the occupancy field is now a smoothed random field thresholded at the target
occupancy, which leaves the density identical and changes only its arrangement.

**Verified:** visible fractions rose, which is the correct direction, because clumped
foliage leaves larger persistent gaps than a uniform mist of the same density. Recording
the direction matters: this change made my own method's job easier, not harder.

---

## 3 — Ray marching stepped over thin foliage

**Found:** 03/09/2026, while checking why clumping had raised visibility so far.

**Symptom:** visible fraction sat at 0.94 to 1.00 across every density, with almost no
response to canopy density at all.

**Root cause:** `FoliageGrid.blocked` marched a fixed 160 samples along the whole segment
from fruit to camera. Most of that segment is open air outside the tree, so inside the
canopy the spacing between samples was larger than the 5 cm cells being tested, and thin
foliage could be stepped straight over.

**Fix:** the ray is clipped to the canopy envelope before marching, so every sample lands
where it can matter, and the step stays below half a cell.

**Verified:** visible fraction now responds to both density and viewpoint count, falling
to 0.36 at one viewpoint on a dense canopy.

---

## 4 — The premise was wrong, and the measurement said so

**Found:** 03/09/2026, from the corrected simulator.

**Symptom:** with twelve viewpoints, only about 5% of fruit were never visible. The
project had been framed around recovering fruit that no camera position can see, and on
that protocol there are few of them.

**Root cause:** my assumption, not a defect in the code. Walking a full circle around a
tree recovers most of what a single view hides, because a fruit hidden behind foliage from
one side is usually exposed from another.

**Fix:** the aim was re-stated rather than the simulator adjusted to rescue it. Occlusion
is severe at one and two viewpoints, where 27% to 64% of fruit are never seen, and that is
also the protocol anyone scanning a real orchard would use, because nobody walks twelve
camera positions around each of two hundred trees. The question became how few viewpoints
an estimator needs to match what naive counting achieves with many. See the amendment
dated 03/09/2026 in `PROJECT_DEFINITION.md`.

**Verified:** pending the re-run of the study on the viewpoint axis.

---

## 5 — Estimators returned numbers from a single viewpoint that could not mean anything

**Found:** 03/09/2026, from the viewpoint sweep.

**Symptom:** at one viewpoint the capture-recapture family reported errors of 331%, 318%
and, for Chao, 6577%.

**Root cause:** with a single viewpoint every observed fruit has been seen exactly once,
so the distribution of sighting counts is a single point. The detection probability is not
poorly estimated, it is not identified at all, and the optimiser was returning whatever
the likelihood surface happened to be flattest at.

**Fix:** the four detection-model estimators now raise `Unidentifiable` below two
viewpoints rather than returning a number, and the study records them as not estimable.

**Verified:** the one-viewpoint column now reports the naive count and the fitted
multiplier, which are the only two estimators the data supports there.

**Note:** this is worth stating plainly in the report rather than hiding behind a chart
that starts at two viewpoints. An estimator that refuses is more useful than one that
guesses.

---

## 6 — Prediction intervals cover far less than they claim

**Found:** 03/09/2026.

**Symptom:** nominal 90% intervals contained the true count on 50% of trees at two
viewpoints, and 60% at twelve.

**Root cause:** the bootstrap resamples the detected fruit, which captures the sampling
noise in which fruit this tree happened to grow, and nothing else. The dominant
uncertainty is in the fitted detection model itself, and resampling fruit barely moves it.

**Status:** open. Reported as measured rather than quietly widened. The candidate fixes
are propagating the detection-model parameter uncertainty into the interval, or
calibrating the interval width against held-out simulated trees. Both are honest; the
second is a calibration and must be labelled as one.
