# Understanding the statistics

Not part of the submission. This exists because there are two pieces of the method I could not
currently explain out loud under questioning, and an assessor is entitled to ask. Work through it
with a pen; every worked example below uses numbers small enough to check by hand.

---

## 1. The problem in one sentence

I can see some of the fruit on a tree. I want to know how many there are. The fruit I cannot see
leave no direct evidence, so the whole method rests on inferring them from the behaviour of the
fruit I *can* see.

---

## 2. The idea I borrowed, in the form ecologists use it

Suppose you want to count fish in a lake. You cannot see them, so you do this:

1. Catch 100 fish, mark them, put them back.
2. Wait, then catch 100 again.
3. Count how many of the second catch were marked. Say 20 are.

Twenty of your second sample of 100 were marked, so marked fish are about 20% of the lake. You
marked 100 of them. So the lake holds about 100 ÷ 0.20 = **500 fish**.

You never saw 400 of them. You inferred them from a *rate*.

**My version.** Each camera position is one "catch". A fruit detected from viewpoint 3 and again
from viewpoint 7 is a fish caught twice. The pattern of which fruit were seen how often tells me how
easy fruit are to see, and from that I can work out how many I missed entirely.

---

## 3. Why the likelihood has that awkward denominator

This is the first thing I could not explain, and it is simpler than it looks.

**The set-up.** A fruit had `c` viewpoints with a clear line to it. The detector finds a fruit it can
see with probability `q`. So the number of times that fruit was detected is

$$y \sim \text{Binomial}(c, q)$$

If `c = 4` and `q = 0.5`, the chances are: 0 detections 6.25%, 1 detection 25%, 2 detections 37.5%,
3 detections 25%, 4 detections 6.25%. Those five add to 100%.

**The problem.** I never observe the fruit with `y = 0`. They are not in my data at all. If I fit `q`
using the ordinary binomial formula on the fruit I *do* have, I am pretending my sample is
representative when it has had its entire zero column deleted.

Concretely: the fruit I see average more detections than fruit in general, because the ones with
fewest detections are exactly the ones that fell out. So ordinary fitting **overestimates `q`**, which
makes me think detection is easier than it is, which makes me **underestimate the total**.

**The fix.** Condition on what is actually true of every fruit in my data: it was detected at least
once. Probability of that is

$$P(y \ge 1) = 1 - P(y = 0) = 1 - (1-q)^c$$

With `c = 4, q = 0.5` that is 1 − 0.0625 = 0.9375. So I divide each fruit's probability by 0.9375,
which rescales the surviving outcomes so they add to 100% again. That division is the denominator:

$$P(y \mid y \ge 1) = \frac{\binom{c}{y} q^{y}(1-q)^{c-y}}{1-(1-q)^{c}}$$

**Say it in one line.** *"Fruit that were never detected are missing from my data by definition, so I
condition the likelihood on having been detected at least once. Without that, the fit sees only the
easy-to-see fruit and concludes detection is easier than it is."*

**Check you have it:** why does the denominator matter more when `q` is small? Because then
`(1-q)^c` is large, so a bigger share of fruit are missing, so the correction is bigger. When `q` is
near 1 almost nothing is missing and the denominator is near 1, doing nothing.

---

## 4. Turning a probability into a count

Once I have `q`, each detected fruit gets a weight of one divided by its chance of appearing at all:

$$\hat{N} = \sum_{i \text{ detected}} \frac{1}{1-(1-q)^{c_i}}$$

**Why that works.** A fruit that had a one-in-four chance of showing up stands for four fruit like
itself: itself plus the three with its properties that did not show up. This is the
Horvitz-Thompson estimator, and it is the same reasoning as a survey that oversamples a small group
and then weights it back down.

**Worked example.** Suppose 3 fruit each had `c = 2` clear views and `q = 0.5`. Chance of appearing
at all is 1 − 0.25 = 0.75. Each detected fruit is worth 1/0.75 = 1.33. If I detected 3, my estimate
is 4. That says: I found 3, and there is probably 1 more like them I missed.

---

## 5. The blind spot, which is the whole reason for the 3D reconstruction

Look at the formula again. If a fruit has `c = 0`, no clear line of sight from anywhere, then
`1 - (1-q)^0 = 0`, and its weight is 1 divided by 0.

That is not a bug to patch. It is the honest answer: **a fruit that could never have been seen
contributes nothing to a sum over things that were seen.** Capture-recapture cannot recover it, no
matter how clever the estimator, because it left no evidence anywhere in the data.

This is where geometry enters. The reconstruction measures the *volume* of canopy that no camera
could see into. It cannot tell me what is in there, but it can tell me how big it is. I then take the
fruit density I measured in the parts of each canopy shell I could see, and apply it to the part of
that same shell I could not.

**Say it in one line.** *"Statistics can infer the barely-seen from the often-seen, but it cannot
infer the never-seen. What I know about the never-seen is how much space it occupies, and that comes
from the reconstruction, not from the detections."*

**Why shell by shell, not one density for the tree?** Mangoes hang toward the outside of the canopy,
and the unobserved region is the middle. One density for the whole tree would put far too many fruit
in the interior. Assuming the seen and unseen parts of a *given depth* hold fruit alike is a much
weaker claim.

---

## 6. The parametric bootstrap, and why my first attempt failed

This is the second thing I could not explain.

**What an interval has to do.** Say "the true count is between 240 and 300, and I am right about
that 90% of the time". To check the 90%, you need to know how much your estimate would wobble if the
world had rolled its dice differently.

**My first attempt: resample the fruit.** Take the fruit I detected, draw from them with replacement
to make a new fake dataset, re-estimate, repeat 200 times, and look at the spread. This is the
standard bootstrap and here it fails badly. It covered 50% of the time while claiming 90%.

**Why it failed.** Resampling detected fruit varies *which fruit this tree happened to grow where*.
That is a real source of uncertainty but it is a small one. The uncertainty that dominates is in the
fitted detection rate `q` and in the density I extrapolate into the unseen volume. Resampling the
fruit barely moves either, so the intervals came out far too narrow.

Think of it as shuffling a deck to estimate how uncertain you are about a card you have not drawn.
The shuffle varies the wrong thing.

**The fix: re-simulate the whole chain.** Instead of reshuffling the data, generate new data from the
model I fitted:

1. Take my estimate: this tree has about `N̂` fruit.
2. Scatter `N̂` fruit through the canopy following the density profile I fitted.
3. Give each one the clear-view count of the canopy point it landed on.
4. Roll the dice: detect each with probability `q̂`, and **throw away the ones detected zero times**,
   exactly as reality throws them away.
5. Re-run the whole estimator on that synthetic tree.
6. Repeat 150 times and look at the spread.

Every step that made the real estimate uncertain is repeated, including the truncation. That is why
it captures the uncertainty the fruit-resampling missed.

**Say it in one line.** *"Resampling the detected fruit varies which fruit the tree grew, and almost
nothing else. The uncertainty that matters is in the detection model, so I re-simulate whole trees
from the fitted model instead and watch how far the estimate moves."*

**The remaining honesty.** Even this is not perfectly calibrated. It came out conservative, covering
more than it claimed, so I rescale the width by a factor fitted on trees held back for that purpose.
That correction works in the middle of the viewpoint range and is noisy at its edges, which the
report states.

---

## 7. Questions I should expect, and honest answers

**"Isn't your simulator just telling you what you told it?"**
Partly, and that is why it is checked against measurements I did not make. It reproduces three
separate published quantities from one setting: fruit found at one viewpoint, fruit found at two,
and the range of correction factors real orchards demand. Those were not fitted to; they were
compared against.

**"Why should I believe any of this without a real mango?"**
You should not, entirely, and the report says so. The estimator is validated against known truth in
simulation. The claim that it works on real trees is not yet made, and the harvest that would test it
is in 2027.

**"Your method loses to a simple multiplier somewhere. Why use it?"**
It loses in one identified place: two viewpoints with a poor detector, where the histories are too
short to fit a detection model and a confident wrong model is worse than a blunt constant. Three
viewpoints recover the advantage. The boundary is stated so a user can avoid it.

**"What is the weakest part?"**
That fruit positions can be recovered in three dimensions from a phone walk at all. Photogrammetry
does that under good conditions and less well in wind or poor light, and I have not tested it. If
that fails, everything downstream fails with it.

**"How much of this did the AI do?"**
Answered in the report's AI note, and the answer is a lot. What I can defend is why each piece is
there, what it does, and where it breaks.

---

## 8. Before the interview

Work these until they are automatic:

- [ ] Derive $P(y \ge 1) = 1-(1-q)^c$ from scratch, and say why the likelihood is divided by it
- [ ] Explain the fish-in-a-lake example with your own numbers, without notes
- [ ] Say why a fruit with `c = 0` breaks the Horvitz-Thompson sum, and what fills the gap
- [ ] Explain why resampling detected fruit gave 50% coverage instead of 90%
- [ ] State the failure boundary and the reason for it
- [ ] Name the assumption you consider weakest, unprompted
