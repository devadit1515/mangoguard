# AamGanak — project definition

> Written before any code, and not edited to match results afterwards. Changes to this file are
> made by appending a dated amendment at the bottom, never by rewriting what is above.
>
> Started 03/09/2026. Independent project, no mentor. Target: CREST Gold, then ISEF.

## Working title

Counting what the camera cannot see: occlusion-aware yield estimation for mango trees from
monocular video.

## The problem

A mango grower's single most valuable number before harvest is how many fruit are on the tree.
It sets the labour they hire, the transport they book, the price they can hold out for, and the
insurance or credit they can raise against the crop. Almost no smallholder has that number. They
have an eyeball guess made by walking the orchard.

Machine counting of fruit from images is a solved problem in one narrow sense and unsolved in the
sense that matters. Detectors reach near-ceiling accuracy at finding the fruit that are *visible*
in a photograph. But a mango tree hides most of its own crop: fruit sit behind leaves, behind
branches, and behind other fruit. The count a camera returns is not the crop. The field's standard
correction is to multiply the visible count by a factor calibrated on a handful of trees, which
assumes the hidden fraction is a constant of the orchard. It is not. It changes with canopy
density, with tree age, with pruning, and with where the fruit sit in the canopy.

**The number a camera cannot see is the number the grower is paid for.**

## Aim

To test whether the total number of mangoes on a tree, including fruit that no camera position can
see, can be recovered from a single phone video walked around that tree, and whether doing so is
measurably closer to the true count than the fixed-multiplier correction the field currently uses.

## Objectives

Each carries a test I can check, so that "done" is not a matter of opinion.

1. **A canopy simulator with known truth.** Generate mango trees whose exact fruit count is known
   by construction, with occlusion modelled from the physics of light through foliage rather than
   assumed. *Done when* the visibility model reproduces the analytic transmittance it is built
   from, and the visible fraction it predicts falls within the range reported for real mango
   canopies in the literature.

2. **An abundance estimator from detection histories.** Recover the total count from which
   viewpoints did and did not see each fruit, rather than from how many fruit were seen.
   *Done when* it returns both an estimate and an interval on simulated trees.

3. **Geometric extrapolation into the unobservable.** Use the reconstructed canopy geometry to
   account for the volume no viewpoint could ever see into, which detection histories alone cannot
   reach. *Done when* it beats the estimator from objective 2 on canopies dense enough to hide
   fruit from every camera position.

4. **A fair comparison against current practice.** Score the naive visible count, the fixed
   multiplier, classical capture-recapture, and my estimator on identical trees from identical
   detections. *Done when* all four report from the same simulated trees and the same detection
   events, so only the estimator differs.

5. **Validation on real trees.** Scan real Alphonso trees, predict, then pick the tree and count
   every fruit. *Done when* per-tree error against picked ground truth is measured and reported,
   whatever it turns out to be.

## Pre-registered success conditions

Written now so they cannot be moved later. Objectives 1 to 4 are testable this autumn; condition
S5 waits for the fruiting season in early 2027.

- **S1.** The visibility model passes its analytic checks, and simulated visible fractions fall
  inside the range published for mango canopies.
- **S2.** Across canopy densities, my estimator's mean absolute percentage error on total count is
  at least 30% lower than the fixed-multiplier baseline fitted on the same trees.
- **S3.** Nominal 90% prediction intervals contain the true count on at least 85% of trees.
- **S4.** The advantage is attributable: removing the geometric term degrades accuracy on dense
  canopies, which shows the gain comes from the mechanism I claim and not from tuning.
- **S5.** On real trees, per-tree absolute percentage error against picked ground truth is
  reported, with the fixed multiplier scored on the same trees for comparison.

A result where S2 fails is still a result. If detection histories alone are enough and the geometry
adds nothing, that is worth knowing and I will report it.

## Approaches considered

| Approach | For | Against | Verdict |
|---|---|---|---|
| Manual counting by a person walking the orchard | No technology; what growers do now | Hours per tree; counts only visible fruit anyway, with worse consistency than a detector | Ruled out: it is the problem, not the solution |
| 2D detection on photographs, corrected by a fixed multiplier | Current published practice; cheap; fast | The multiplier assumes a constant hidden fraction, which varies by canopy; needs recalibration per orchard | The baseline I measure against |
| 3D reconstruction, then count the fruit visible in the reconstruction | Removes double-counting across frames; gives fruit size for free | Still counts only what was seen; the hidden fruit remain hidden | A component, not the answer |
| **3D reconstruction, then statistical abundance estimation (chosen)** | Each viewpoint is a survey occasion, so fruit seen from few angles reveal the detection probability; canopy geometry says how much volume was never observable | More machinery; rests on a detection model that must itself be checked | Chosen |

The chosen route treats fruit counting as an abundance-estimation problem of the kind ecologists
solve when counting animals that hide. That transfer is the central idea of the project.

## Why the statistics work

A fruit seen from three of twelve viewpoints tells me something a fruit seen from all twelve does
not: that fruit like it are easy to miss. The distribution of how often fruit were seen carries the
information needed to estimate how many were never seen at all. That is capture-recapture, and it
has one blind spot: fruit with zero probability of detection from any viewpoint leave no trace in
the data at all, so no amount of statistics recovers them.

The 3D reconstruction is what closes that blind spot. It measures the canopy volume and how deep
each viewpoint could see into it, which gives a physical estimate of the volume that was never
observable and therefore how many fruit are likely to sit inside it.

## Scope

In scope: the estimator, the simulator that validates it, the comparison against current practice,
and validation on real trees when the season allows. In scope later: the phone application that
makes it usable by a grower.

Out of scope: fruit detection itself. Published detectors already solve finding visible mangoes in
an image, and rebuilding one adds nothing to the question I am asking.

## Amendments

*(Append dated entries here. Never edit the text above.)*

### 03/09/2026 — the aim narrowed, because the measurement said it should

The simulator, once its occlusion model was corrected (`FIX_LOG.md`, entries 1 to 3),
showed that a full walk around a tree recovers most of what a single view hides. At
twelve viewpoints only about 3% of fruit are never seen from anywhere. The project had
been framed around recovering fruit that no camera position can see, and at that
protocol there are few of them to recover.

The occlusion is severe where the viewpoints are few: at one viewpoint 38% of fruit are
never seen, at two 13%. That is also the protocol anyone scanning a real orchard would
actually use, because nobody walks twelve camera positions around each of two hundred
trees.

So the aim narrows to the question the measurement supports and the field cares about:

> How few viewpoints does an estimator need to match the accuracy that naive counting
> reaches with many, and what does that buy in scanning time per orchard?

The objectives and success conditions above are unchanged in substance; S2 is now read
against the fixed multiplier at matched viewpoint counts, and the viewpoint count becomes
the primary experimental axis rather than a fixed setting. The original framing was not
wrong so much as aimed at a regime that a twelve-viewpoint protocol does not reach.

### 03/09/2026 — objective 3 is answered by the reconstruction, not by a proxy

Objective 3 asked for geometric extrapolation into the volume no viewpoint could see. The
first attempt used the mean length of canopy between a fruit and the cameras, computed
from the canopy envelope, as a stand-in for how hidden that fruit was. That proxy assumes
foliage is spread evenly, which is the assumption the clumped simulator exists to break,
and it barely improved on plain capture-recapture.

The replacement uses what a carved reconstruction actually recovers: for any point in the
canopy, how many cameras had an unobstructed line of sight to it. Points seen by none of
them are the unknown region, and its volume is measured rather than assumed. The estimator
now separates two things that were previously tangled. The reconstruction says how many
chances the detector had on each fruit; the detection histories say what it did with those
chances. Both become identifiable, and the fruit that were never observable at all are
estimated by carrying the fruit density measured in each shell of the canopy into the
unobserved part of that same shell.

Objective 3's "done when" test is unchanged and is now met by a different mechanism than
the one I had in mind when I wrote it.

### 03/09/2026 — a published reference point, and what it may and may not be compared with

Wang, Walsh and Koirala counted mango on real trees against manual harvest counts, which is
the same ground truth objective 5 specifies. Their dual-view imaging recovered 40.2% of the
harvest count and their video tracking 62.3%, with per-orchard correction factors ranging
from 1.05 to 2.43, and they state that the final estimate is sensitive to that factor. That
is the gap this project addresses, in the field's own words.

Those figures come from a vehicle imaging a contiguous hedgerow at speed, which is a harder
protocol than a person walking around a free-standing tree. Their per-tree error of 11.5%
is therefore not comparable with any simulated figure here and must not be set beside one.
The like-for-like comparison is the fitted multiplier scored on identical simulated trees.
The comparable comparison waits for picked and counted trees in 2027.
