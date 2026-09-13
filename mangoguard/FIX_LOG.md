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

---

## 7 — The simulator was easier than a real orchard, checked against published field counts

**Found:** 03/09/2026, on first comparing the simulator with the literature rather than with
itself.

**Symptom:** the simulator reported 85% of fruit visible from two viewpoints. Wang, Walsh and
Koirala, counting mango on a real orchard against manual harvest counts, detected **40.2%** of
the harvest count from dual-view imaging and **62.3%** from video tracking. Objective 1 requires
the simulated visible fraction to sit inside the range real mango canopies show, and it did not.

**Root cause, first part:** the trees had no wood. A mature mango carries a trunk near 280 mm
across and several primary limbs, and those block a line of sight completely. The model had
foliage and fruit and nothing else.

**Why leaf density was not the answer:** raising leaf area density to force the visible fraction
down would have required a leaf area index above 20. A bearing mango carries 3 to 6. The
discrepancy therefore had to be a missing occluder rather than an underestimated one, which is
what identified the wood.

**Fix:** a trunk and seven scaffold limbs, as opaque capsules, now block sight lines. Canopy
density was reset to leaf area indices of 2.9 to 7.2, which is the physical range, and the fruit
distribution was moved off the outer shell to Beta(3,2), a mean radius of 0.6 rather than 0.75.

**Verified, and only in part.** One viewpoint now gives 0.49 to 0.67 visible, which brackets the
published dual-view figure of 0.40 acceptably. Two viewpoints give 0.77 to 0.88 against the
published video-tracking figure of 0.62, so the simulator remains easier than the field.

**Why I stopped tuning here.** The remaining gap has a geometric explanation rather than a
parameter one. The published figures come from a vehicle imaging a contiguous hedgerow from two
fixed sides at 5 km/h, where neighbouring canopies occlude, the camera height is fixed and the
images carry motion blur. The simulator represents a free-standing tree scanned from positions
chosen by a person on foot, which is a genuinely easier problem. Forcing agreement by moving
parameters until the number matched would be adjusting the simulator to rescue a result, which
is the failure already recorded in entry 4. The gap is stated instead, and it bounds the claims:
simulated visible fractions are optimistic relative to hedgerow imaging, so the accuracy figures
should be read as the favourable end.

**Consequence for the comparison.** The published per-tree error, 18.0 fruit against a mean of
156.5, is 11.5%, obtained on real trees under a harder protocol. It is not comparable with a
simulated figure and must never be set beside one. The like-for-like comparison remains the
fitted multiplier scored on identical simulated trees, and the real comparison waits for picked
and counted trees in 2027.

---

## 6b — the interval fix over-corrected, and that is also a miscalibration

**Found:** 03/09/2026, on the calibrated study.

**Symptom:** the parametric bootstrap replaced 50% coverage with 98% at two viewpoints and
100% at three and above, against a nominal 90%. Mean width is 17% to 19% of the true count.

**Reading:** the intervals now cover more than they claim. That is the safe direction for a
grower deciding how much labour to hire, but it is still a miscalibration, and an interval
that is honest about being conservative is worth more than one that quietly is. With sixty
trees and sixty covered, the true coverage is above about 0.95, so the excess is real rather
than a small-sample artefact.

**Status:** open, and deliberately not tuned. Narrowing the interval until the coverage hits
0.90 on these trees would be fitting the interval to the test set. The correct route is to
calibrate the width on a separate set of simulated trees and then report coverage on trees
never used for that, which is the next piece of work. Until then the report says the
intervals are conservative and gives both the coverage and the width.

---

## 8 — Detection was all-or-nothing on a ray to the fruit's centre

**Found:** 04/09/2026, while trying to replace the assumed detector reliability of 0.95 with
something anchored to a measurement.

**Symptom:** not a wrong number so much as an arbitrary one. A fruit was detectable if an
unobstructed line reached its centre, at a fixed rate of 0.95, and undetectable otherwise. Two
things are wrong with that. A mango whose centre sits behind a twig but whose body is in plain
view is detectable, and my model said it was not. A mango showing a sliver through a gap in the
leaves is usually missed, and my model said it was found 95 times in a hundred.

**What the literature gave.** Published mango detectors report an F1 near 0.97 on a curated test
set and near 0.89 on daytime orchard images [3]. The gap between those two figures is largely fruit
that are partly behind something, which is the effect the model was missing entirely.

**Fix:** visibility is now measured over nine points spread across the face each fruit presents to
the camera, giving a showing fraction rather than a yes or no. Detection probability rises with
that fraction and saturates at the detector's ceiling.

**Calibration, and what it is not.** Sweeping the two parameters found that a ceiling of 0.89 with
recall halving at 0.85 showing reproduces both published field figures at once: 0.35 of fruit
detected from one viewpoint against their 0.402 from dual view, and 0.62 from two viewpoints
against their 0.623 from video tracking. Matching both from one setting is better agreement than I
expected.

It is a calibration of the whole pipeline and not a measurement of a detector, and the difference
matters. The published figure counts detections against a harvest, so it also includes fruit that
no camera was ever pointed at, high in the tree or on the far side of the row. My cameras see the
whole tree, so this setting may be standing in for losses the model does not represent. Reported as
a calibrated pipeline rather than as a measured detector, and the study now runs the headline
comparison under a better and a worse detector as well, so the conclusion can be checked against
the setting rather than resting on it.

---

## 6c — Interval width calibrated on trees the coverage is not reported on

**Found:** 04/09/2026, closing entry 6b.

**Fix:** the raw parametric interval is rescaled by one multiplier. For each calibration tree the
distance from estimate to truth is expressed in units of the raw half-width, and the multiplier is
the target quantile of those distances, which is the reasoning conformal prediction uses.

**The part that makes it honest:** the multiplier is fitted on the twenty trees used to fit the
multiplier baseline, and coverage is reported on the sixty the estimator is scored on. Those sixty
never inform the width. Fitting the width on the same trees the coverage is reported on would have
produced a better-looking number that meant nothing, which is why entry 6b left it open rather than
tuning it.

**Verified:** both the uncalibrated and calibrated coverage are reported, so the size of the
correction is visible rather than hidden.

---

## 9 — Where the method actually fails, found by testing it against a worse detector

**Found:** 04/09/2026, from the detector sensitivity analysis added under entry 8.

**Symptom:** on two viewpoints with a poor detector, ceiling 0.80 and recall halving at 0.95 showing,
the reconstruction estimator reaches 21.9% error against the fitted multiplier's 12.5%. It is not
merely worse; it is worse by a wide margin, and it is the only setting tested where it loses.

**Cause:** with two viewpoints and a detector that finds only 41% of fruit, the detection histories are
both short and mostly empty. The estimator fits a detection model to them and then extrapolates
confidently from it. A wrong model applied with confidence is worse than a blunt constant applied
cautiously, which is what the multiplier is.

**Not fixed, reported.** Three viewpoints recover the advantage even with that detector, and six restore
it fully, so the boundary is specific and checkable: do not use this on two viewpoints unless the
detector is known to be good. Publishing the boundary is more useful than tuning until it disappears,
and it would not have been found without deliberately testing against a detector worse than the one the
calibration chose.

---

## 6d — the interval calibration works in the middle of its range and is noisy at the edges

**Found:** 04/09/2026, from the calibrated run.

**Symptom:** the multiplier fitted on twenty calibration trees brings coverage to 90% at three
viewpoints, 95% at six and 93% at twelve. At four viewpoints it overshoots and coverage falls to 80%,
below what the interval claims. At two viewpoints it pushes an already acceptable 88% up to 98%.

**Cause:** twenty trees are too few to fit a stable multiplier, and the fitted values swing from 1.26 to
0.38 across viewpoint counts, which is more variation than the underlying uncertainty should show.

**Status:** open, and reported as measured. Both the uncalibrated and the calibrated series appear in
the report so the size and the instability of the correction are both visible. The fix is more
calibration trees, which costs only compute.

---

## 6e — the diagnosis in 6d was wrong, and testing it is how I know

**Found:** 04/09/2026, by acting on entry 6d.

**What 6d claimed.** That the interval calibration was unstable because twenty trees are too few to
fit the multiplier, and that the fix was more calibration trees, costing only compute.

**What I did.** Gave the interval calibration its own set of fifty trees, drawn separately from the
twenty that fit the multiplier baseline, and re-ran.

**What happened.** Almost nothing. The fitted multipliers moved from 1.259 to 1.309 at two
viewpoints, 0.769 to 0.764 at three, 0.511 to 0.509 at four, 0.539 to 0.493 at six and 0.375 to
0.313 at twelve. Coverage at three, six and twelve viewpoints sits acceptably at 0.90, 0.93 and 0.92.
Coverage at four viewpoints is still 0.80, below what the interval claims, and at two viewpoints the
correction still pushes an already reasonable 0.883 up to 1.000.

**The real diagnosis.** The multipliers barely moved when the sample tripled, which is what a
well-determined quantity does. So they were never the noisy part, and entry 6d was wrong about the
cause. The problem is the shape of the correction rather than its precision: one scalar per viewpoint
count cannot repair an interval whose miscalibration differs from tree to tree within that viewpoint
count. At two viewpoints the raw interval is close to right on average and the scalar makes it worse.

**Status:** open, with a better-founded next step. The correction needs to depend on the tree, most
likely on how much of the canopy went unobserved, rather than on viewpoint count alone. Recorded
here rather than quietly dropped, because a wrong diagnosis that was tested and refuted is worth more
in the record than one that was never checked.
