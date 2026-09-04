# CREST Gold Award — Student Profile Form

> **Working draft.** CREST requires a Student Profile Form alongside the report, one per student. It
> is the assessor's map: for each of the fifteen criteria it points to where in the report the
> evidence sits. This mirrors the official form, which is downloaded and transcribed from
> crestawards.org. The "Where" column cites report sections; **page numbers can only be filled in
> after the final PDF export and must be re-checked after any re-export.**
>
> Two rows below say a criterion is not yet met. That is deliberate. The project is at its
> simulation stage and the orchard season has not arrived, and a form claiming otherwise would be
> contradicted by the report it points at.

---

| | |
|---|---|
| Student's first name | Devadit |
| CREST Award level | **Gold** |
| Project title | Counting Fruit a Camera Cannot See: Estimating Mango Load from Few Viewpoints |
| Mentor name | None. Independent project. See the note at the end. |

---

## Part A — criteria checklist

### 1 — Planning the project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **1.1** Clear aim, broken into objectives | §1.1, §1.2; revisited §5.7 | One testable aim sentence, then five numbered objectives each ending in a *done when* test. Section 5.7 returns to all five and states plainly that the fifth is not met, because the ground truth for it is obtained by harvesting a tree and the season has not come. |
| **1.2** Wider purpose | §1 opening | A grower in Ratnagiri who hired eleven pickers for a job needing six, because the only crop estimate available to him was a walk down the rows. Production and smallholding statistics follow, and §2 explains why the existing correction does not solve it. |
| **1.3** Range of approaches | §3.1 | Four approaches compared in a trade-off table: manual counting, detection with a fitted multiplier, three-dimensional reconstruction with plain counting, and reconstruction with statistical abundance estimation. Each is eliminated for a stated reason and the second is retained as the measured baseline. |
| **1.4** Plan described and justified | §3, Appendix B | The method is replicable from §3, and Appendix B gives the seed, the population parameters, and the two commands that regenerate every number and figure. **Outstanding: the repository must be made public before submission, since the report cites it.** |
| **1.5** Time planning | §1.3 | *Not yet met.* The timeline table is real and dated from the commit history, but the project is young and there is no planned-against-actual record with genuine slippage yet. This criterion resolves as the work runs to the 2027 season, and the table is built to receive it. |

### 2 — Throughout the project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **2.1** Materials and people | Appendix B | *Partly met.* The material side is complete: pinned code, fixed seed, the exact reproduce commands, the parameter ranges, and the published field measurements the simulator is checked against. **Outstanding: the people side is thin. The cooperating grower, whose orchard hosts the 2027 campaign and whose account of hiring pickers set the problem, should be named as a resource, together with any course or documentation actually relied on.** |
| **2.2** Background, sources acknowledged | §2, References | §2 is built as an argument rather than a list: detection is solved, the hidden fraction is large and measured, the field repairs it with a constant it knows is not constant, and a body of statistics for populations that hide exists in another field. Thirteen references, every one cited in the text and every citation listed. **Outstanding: seven entries need their bibliographic details checked against the originals, which the report states.** |

### 3 — Finalising the project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **3.1** Logical conclusions and implications | §6.1, §6.3 | The conclusion answers the aim directly and with numbers, then bounds itself: the result is simulated, on canopies the report itself shows to be milder than a real hedgerow. §6.3 declines to compare my simulated figure with the published field figure and explains why the two are not comparable. |
| **3.2** How actions and decisions affected the outcome | §6.2 | Two explicit causal links. Replacing a smooth canopy-depth proxy with the reconstruction's measurement of unobserved volume roughly halved the error at two viewpoints. Splitting the detector's hit rate from the number of chances it had made both identifiable, and the estimator that does not split them reaches 28.3% error where the one that does reaches 2.3%. |
| **3.3** Learning and reflection | §8 | Specific and tied to events: the simulator was missing tree trunks for two days and nothing internal caught it, because everything internally agreed. What caught it was somebody else's harvested orchard. The change I would make is to go to the field measurements before building rather than after. |

### 4 — Project-wide

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **4.1** Understanding of the science | §3.2, §3.3, Appendix C | The body explains in plain terms why re-sighting frequencies carry information about what was never seen, and why that reasoning has a blind spot that geometry closes. Appendix C gives the transmittance law, the clumping treatment, the zero-truncated likelihood and the Horvitz-Thompson total, each with a sentence on why it is the right tool. |
| **4.2** Ethics and safety decisions | §7 | Decisions rather than disclaimers: which direction to err in and why, whose harvest is destroyed to obtain ground truth and on what terms, and a fairness finding measured from my own results, since accuracy is worst on dense unpruned canopies and those belong to growers with least capital. Dual use is named: a buyer holding this estimate and a grower without it is worse for the grower than today. |
| **4.3** Creative thinking | §6.4 | Two decisions named as choices. Treating fruit counting as a wildlife abundance problem, a transfer I have not found made before. And using a three-dimensional reconstruction for what it measures rather than what it appears to measure, since its useful output here is a map of where the cameras could not look. |
| **4.4** Identified and overcame problems | §4.1–4.3, fix log | Three told in full: occlusion drawn independently per viewpoint, which flattered every result; ray marching stepping over the cells it was meant to test; and a simulator easier than any real orchard, caught only by comparison with published harvest counts. The full log of eight sits in the repository, including two entries still open. |
| **4.5** Communication | Whole report, Appendix A | Written to be followed without a background in statistics. Each hard idea gets one plain comparison at first use, jargon is expanded, the glossary carries definitions, and all the mathematics is quarantined in an appendix the body never depends on. Seven figures, each captioned and referenced before it appears. |

**Summary for the assessor.** Thirteen criteria are evidenced at this stage. Criterion 1.5 needs
elapsed time and criterion 2.1 needs its people axis completed; both are named above rather than
padded.

---

## Part B — personal reflections

*(Draft. Put these into your own words before transcribing, and make sure every sentence is one you
would say out loud to an assessor.)*

**Why I chose this project.** A grower we buy from told my father he had hired eleven pickers for a
job that needed six. He had estimated his crop by walking the rows and looking, because that is the
only method available to him. I wanted to know whether the number he needed could be got from a
phone instead of from a harvest.

**How it was and was not successful.** The estimator works on simulated trees, and works best exactly
where the problem is hardest, on dense canopies scanned from few positions. Three viewpoints with it
beat twelve without. What it has not done is count a real mango. Everything in this report is
measured on trees I generated, and the trees I generated are easier than a real orchard by an amount
I can quantify but have not closed.

**What I learned.** That a simulation is a claim about the world and has to be tested against the
world. My trees had no trunks for two days and every internal check passed, because they were all
checking the simulator against itself. The thing that caught it was a number from somebody else's
harvested orchard. I also learned to treat a result that contradicts me as information: twice my own
measurements undercut what I had set out to show, and both times the right move was to change the
claim rather than the code.

**What impact it might have.** A grower who can measure his crop rather than guess it hires the right
number of pickers, books the right transport, and negotiates from a number instead of from hope. The
method needs no equipment beyond a phone and no harvested trees to calibrate against, which is the
practical difference from the correction factor the field uses now.

**What I would improve.** I would have read the published field measurements before building the
simulator rather than after. The figure that exposed my missing tree trunks was available the whole
time. I built outward from physics I trusted instead of inward from measurements someone had already
made, and it cost me two days and very nearly cost me the credibility of every number.

---

## My mentor

This project has no mentor or supervisor. Where I needed to check the physics of light through a
canopy or the statistics of capture-recapture, I went to the primary literature, which the reference
list records. The role of the sceptic, which a supervisor would normally play, was filled badly at
first: my early results agreed with me because my simulator and my checks shared the same
assumptions. What eventually played that role was published field data from an orchard someone else
had harvested. Finding a person who is allowed to doubt me earlier is the change I would make.

A cooperating grower in Ratnagiri has agreed to host the orchard campaign in 2027, which will
require picking and counting whole trees.

---

## AI declaration

☑ **AI declaration.** All AI-assisted content has been referenced and declared. The full disclosure
is in the report, under "A note on AI use", and it states plainly that the assistance was substantial
rather than incidental.

> **Read this before transcribing.** The AI-use statement in the report describes the position as of
> September 2026. It must be rewritten to describe the position at submission, and it must not
> overstate your own share. CREST's requirement is that the work is sufficiently your own and that
> you can explain to the assessor how the tool was used. There are parts of this report you cannot
> yet defend in conversation, and those need to be studied until you can, or removed.

| | |
|---|---|
| Student name | Devadit Jain |
| Declaration | ☐ I confirm this is my own work. *(Do not tick until the statement above is true and current.)* |
| Signature / date | *(Sign and date on the official CREST form.)* |
