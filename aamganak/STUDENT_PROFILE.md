# CREST Gold Award — Student Profile Form

> **What this is.** CREST requires a Student Profile Form submitted alongside the report. This file mirrors the official form. The "Where" column cites report sections and page numbers of the final PDF. If the report is re-exported after any layout change, re-check the page numbers before transcribing.

---

| | |
|---|---|
| Student / team member's first name | Devadit |
| CREST Award level | **Gold** |
| Project title | Counting Fruit a Camera Cannot See: Estimating Mango Load from Few Viewpoints |
| Mentor name | None — independent project (see the note at the end) |

---

## Criteria checklist

*Notes to the assessor are optional and deliberately brief — the evidence is in the report section named.*

### 1 — Planning your project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **1.1** Set a clear aim, broken into smaller objectives | §1.1–1.2, p. 2 (+ scorecard in §5.8, p. 9) | One testable aim sentence, split into five numbered objectives, each with an explicit "done when" test. Section 5.8 revisits all five against the results and says plainly which is not met: objective 5, validation against picked and counted trees, cannot be met until the fruit exists. Four are met and reported. |
| **1.2** Explained a wider purpose | §1 opening, p. 1; §6.1, p. 8 | The grower in Ratnagiri who hired eleven pickers for a job that needed six. The scale follows: India grows around 22 million tonnes of mango a year and about 86% of holdings are under two hectares, so the fruit count per tree is the number everything else is planned around and almost nobody has it. Section 2 explains why the existing repair, a correction factor fitted per orchard, does not solve it. |
| **1.3** Identified a range of approaches | §3.1, p. 4 | Four genuinely different approaches compared in a trade-off table: a person walking the rows and counting; detecting fruit in images and multiplying by a fitted constant; reconstructing the tree in three dimensions and counting what is visible in the reconstruction; and reconstructing, then estimating abundance statistically. Each carries the reason it was eliminated or chosen. The fitted multiplier was not discarded but kept as the measured baseline, because it is what published work actually does. |
| **1.4** Described the plan and why I chose it | §3, pp. 4–5; Appendix B, p. 12 | Section 3 sets out the design and the reason for it: the chosen route is the only one that uses information the images already contain, since a fruit seen from three viewpoints out of twelve tells you something a fruit seen from all twelve does not, and counting throws that away. Appendix B gives the seed, the population parameters, and the two commands that regenerate every number and every figure, so the method can be checked rather than believed. The repository must be made public before submission, since the report cites it. |
| **1.5** Planned and organised my time | §1.3, p. 3 | A dated timeline of ten stages, reconstructed from the commit history (Jun–Sep 2026), with three future stages marked as planned. The main deviation was a premise correction: the corrected simulator contradicted the original framing, and the aim narrowed rather than the simulator being adjusted. Stages 4 to 7 compressed into two days as a direct result of the two earlier attempts. |

### 2 — Throughout your project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **2.1** Made good use of materials and people | §1.3, p. 3; Appendix B, p. 12 | The materials side is complete: the code, the fixed seed, the exact commands that reproduce every number, the parameter ranges and their physical justification, and the published field measurements the simulator is checked against. The people side: the cooperating grower in Ratnagiri whose account of hiring pickers set the problem and whose orchard will host the 2027 campaign is a named resource. Python 3.11, NumPy, SciPy, matplotlib and pytest are pinned in the project configuration. The research community (published field measurements, the CREST criteria and exemplar materials) stood in for a mentor. |
| **2.2** Researched the background, acknowledged sources | §2, p. 3; References, pp. 10–11 | The background is built as an argument rather than a list. Detection is solved, with a published mango detector reaching an F1 of 0.968. The gap between what is seen and what is there is large and has been measured against actual harvest counts, at 40.2% of fruit recovered from dual-view imaging. The field repairs that gap with a constant it knows is not constant, ranging from 1.05 to 2.43 across orchards, and says so itself. A body of statistics for populations that hide already exists in ecology. The gap sits where those four meet. Fourteen references, every one cited in the text and every citation appearing in the list. |

### 3 — Finalising your project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **3.1** Logical conclusions + implications for the wider world | §6.1, p. 8; §6.3, p. 9; §6.5, p. 9 | Section 6.1 answers the aim directly and with numbers, then bounds itself: the result is measured on simulated trees that the report itself shows to be easier than a real hedgerow. The implication for a grower is specific: the method needs no harvested trees to calibrate against, and a correction factor has to be bought with a harvest, so this removes a cost rather than only an error. Section 6.3 declines to set my simulated figure beside the published field figure of 11.5% per-tree error and explains why the two are not comparable. Refusing a flattering comparison is itself a conclusion. |
| **3.2** How my actions/decisions affected the outcome | §6.2, p. 9; §4, pp. 6–7; §5.6, p. 8 | Two decisions did most of the work. Replacing a smooth canopy-depth proxy with the reconstruction's measurement of unobserved volume roughly halved the error at two viewpoints. Separating the detector's hit rate from the number of chances it had made both quantities identifiable; the estimator that does not separate them reaches 68.2% error at two viewpoints where the one that does reaches 9.5%. Section 4 traces the opposite direction too: my first simulator flattered every result, and correcting it changed what the project was about. A third decision: testing the conclusion against a deliberately worse detector found the setting where my own method loses to the multiplier it is meant to beat. That boundary would not be in the report if I had only tested where I expected to win. |
| **3.3** What I learnt and would improve | §8, p. 10 | Section 8 is specific rather than general. My simulated trees had no trunks for two days and every internal check passed, because the checks and the simulator shared the same assumptions. What caught it was a number from somebody else's harvested orchard. The change I would make is to go to the published field measurements before building rather than after. Next steps are given with what each one needs, and the one that matters is constrained by a fruiting season rather than by effort. |

### 4 — Project-wide

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **4.1** Understanding of the science | §3.2–3.3, pp. 4–5; Appendix C, pp. 13–14 | The body explains in plain terms why the pattern of re-sightings carries information about fruit that were never seen, and why that reasoning has a blind spot: a fruit with no chance of being seen from anywhere leaves no trace at all, so it is absent rather than under-represented, and no statistics recover it. Appendix C sets out the transmittance law and why discretising the canopy leaves it unchanged, the clumping treatment and why scattered-leaf theory gets gap statistics wrong without it, the zero-truncated likelihood and why the truncation is necessary, and the reciprocal-probability total. Each is explained as why it is the right tool rather than named and cited. |
| **4.2** Ethics and safety decisions | §7, pp. 9–10 | Decisions specific to this project, not boilerplate. Which direction to err in, since an over-estimate means pickers standing about and an under-estimate means fruit left past ripeness, and the intervals are currently conservative for that reason. Whose harvest is destroyed to obtain ground truth, and on what terms: the 2027 campaign requires picking a cooperating grower's trees, agreed in writing, with the fruit and the data belonging to him. A fairness finding measured from my own results: accuracy is worst on dense unpruned canopies, and those belong disproportionately to growers with least capital to spend on management, so a tool that worked best on well-managed orchards would widen a gap it claims to close. Accuracy is therefore reported by canopy density rather than as a single average that would hide it. Dual use is named: a buyer holding this estimate while the grower does not is worse for the grower than the situation today. |
| **4.3** Creative thinking | §6.4, p. 9 | Two decisions are named as choices rather than steps. Treating fruit counting as a wildlife abundance problem: the methods ecologists use for animals that hide map onto a camera walked around a tree without forcing, because both produce repeated survey occasions of one population. I have not found the transfer made before. Using a three-dimensional reconstruction for what it measures rather than what it appears to measure: a reconstruction looks like a tool for finding where things are; its more useful output here is a map of where the cameras could not look, which is a statement about absence. |
| **4.4** Identified and overcame problems | §4.1, p. 6; §4.2, p. 7; §4.3, p. 7; full log in FIX_LOG.md | Three problems are told in full with cause, fix and verification: occlusion drawn independently for each viewpoint, which treated foliage as if it rearranged itself between camera positions and made every estimator look adequate; ray marching that stepped over the very cells it was meant to test; and a simulator easier than any real orchard, caught only by comparing against published harvest counts, where the diagnosis was that leaf density could not be the answer because closing the gap would have needed a leaf area index above 20 against a real 3 to 6. A fourth is recorded but is not a defect in the code: the corrected simulator contradicted the premise the project began with, and I narrowed the aim rather than adjusting the simulator to rescue it. A fifth is a diagnosis I got wrong and tested: I attributed unstable prediction intervals to too few calibration trees; tripling the set barely moved the fitted correction, which showed the cause was the shape rather than the precision. The full log of thirteen entries, including five still open, is in the repository. |
| **4.5** Explained the project clearly | Whole report; Appendix A, p. 11 | The body is written to be followed without a background in statistics, with one everyday comparison for each hard idea and no more. Jargon is expanded at first use and the glossary in Appendix A carries the definitions. All the mathematics is quarantined in Appendix C, and the argument never depends on it. Eight figures, each captioned and referred to before it appears. |

---

## Personal reflections

*(First draft for the official form; adjust the wording before transcribing.)*

**Why I chose this project.** I chose this project because of a conversation my father had with the grower we buy Alphonso from every summer. He had hired eleven pickers for a harvest he thought would need six and paid them all for a day of standing about. His only way of estimating his crop was to walk the rows and look at it. I wanted to know whether that number could come from a phone instead of from experience.

**How it was and wasn't successful.** It produced a simulator calibrated against published field measurements, seven estimators scored on identical trees, and a headline result: three viewpoints with the reconstruction estimator match twelve without, which for a grower with two hundred trees is the difference between a morning and a day. It did not count a single real mango. Everything in the report is measured on trees I generated, and I would rather say that plainly than let a reader assume otherwise. It also found its own limit: on two viewpoints with a poor detector the multiplier wins, and I reported that rather than hide it.

**What I learnt.** Twice my own measurements contradicted what I had set out to show. The first time, correcting the physics of my simulator revealed that walking a full circle around a tree already recovers most of what one view hides, which undercut the premise I had started from. The second time, comparing my trees against somebody else's harvested orchard showed that mine were far too easy, because they had no trunks or branches in them at all. Both times the right move was to change the claim rather than the code, and learning to do that is worth more to me than the accuracy figure. Working without a mentor cost me on both occasions: my simulator and my checks shared the same assumptions, so everything agreed with itself and nothing caught the error. What eventually played the sceptic was published field data from an orchard someone else had harvested, which is a poor substitute for a person who is allowed to doubt you early.

**What impact it might have on others.** The method needs no harvested trees to calibrate against, which is the practical difference: a correction factor has to be bought with a harvest, and this removes that cost. For a smallholder with a few hundred trees, the difference between three viewpoints and twelve is the difference between scanning an orchard in a morning and spending a whole day at it. Whether any of this holds on real trees is a harvest away.

**What I would improve.** I would have gone to the published field measurements before building the simulator rather than after. The 40.2% figure was available the whole time and would have caught the missing wood on the first day. I built inward from physics I trusted instead of outward from measurements someone had already made. Above all I would find one person allowed to doubt me early, because explaining a result to someone else catches what re-reading my own code never did.

---

## My mentor

This project was completed **independently, with no mentor or supervisor.** The second person who normally distrusts a convenient result did not exist here, so I audited my own work, which is how the missing-wood mistake (§4.3) was eventually caught. The cooperating grower in Ratnagiri provided the motivation and will host the orchard campaign, but was not involved in the design or analysis. AI assistance is disclosed in the report's AI-use note: Claude was used as a coding aid and drafting assistant, with the author retaining all scientific decisions.

> *Independent submission route. No registered provider is required for this entry.*

---

## AI declaration

☑ **AI declaration.** All AI-assisted content has been referenced and declared. The full disclosure (tool, what it did, and how I checked it) is in the report's **"A note on AI use"** section.

| | |
|---|---|
| Student name | Devadit Jain |
| Declaration | ☑ I confirm this is my own work. |
| Signature / date | *(Sign and date on the official CREST form.)* |
