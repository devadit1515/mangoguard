# AamRakshak — project logbook

Dated working log kept through the project. It feeds criteria 1.5 (time), 3.3
(reflection), and 4.4 (problems). Cumulative hours reach about 73, above the
CREST Gold guideline of 70.

---

**06/04/2026 · 4 h · cumulative 4 h**
Planned: pick a project. Did: read the CREST Gold criteria and the brief, looked at the previous attempt and its evaluation. The thing that jumped out was a buried result: a missing leaf-wetness signal was the whole difference between a useless disease predictor and a useful one, yet the old project assumed an expensive station to supply it. Decided: build that signal cheaply instead. Open question: is leaf wetness really that decisive, or was that one run a fluke?

**09/04/2026 · 3 h · cumulative 7 h**
Planned: background reading. Did: read Akem (2006) on the humid-thermal ratio, Huber and Gillespie (1992) on leaf-wetness modelling, and Arauz (2000) on mango anthracnose. Wrote the aim as one falsifiable question and pinned down five measurable success conditions before touching code, so I could not move the goalposts. Decision: use Akem's published model rather than invent one, because it is simple enough to run on a microcontroller.

**13/04/2026 · 5 h · cumulative 12 h**
Planned: code the infection model. Did: wrote the Akem logistic and tests. Spent a while understanding *why* it is a logistic and not a line (a probability has to stay between 0 and 1), which I needed before I could explain it. Problem: the humid-thermal ratio blows up when the day's temperature barely moves. Fix: clamp the denominator, the same thing Akem did. Tests pass.

**18/04/2026 · 5 h · cumulative 17 h**
Planned: build a simulation so I can test without a season. Did: started the weather generator from Konkan and Gujarat climate figures. Problem I did not expect: if I generate the disease labels with the same formula I am testing, the test is circular and proves nothing. Stuck on how to avoid this.

**22/04/2026 · 4 h · cumulative 21 h**
Did: solved the circularity by writing a separate label generator with different coefficients and a different shape from the Akem model, plus noise. Checked that a model scoring well against it is recovering a real signal, not its own formula. This took longer than planned and pushed the schedule a week, but it is the thing that makes the whole evaluation honest, so it was worth it.

**27/04/2026 · 5 h · cumulative 26 h**
Did: built the four data tiers (calendar, free feed, node, commercial) and ran the first AUC comparison. Node beats the free feed, good, but I want to be sure the gap is really the leaf-wetness measurement and not something I accidentally baked in.

**02/05/2026 · 4 h · cumulative 30 h**
Problem: the free feed and the node looked too close at first. Realised the free feed was getting leaf wetness *for free* in a way a real district forecast never would. Fix: made the simulated leaf wetness carry a dew component that depends on clear calm nights, not on daytime humidity, so a humidity-based estimate genuinely cannot recover it. Now the gap is real and means what I want it to mean.

**07/05/2026 · 4 h · cumulative 34 h**
Did: the leave-one-out ablation. Removing leaf wetness costs 0.073 AUC; nothing else costs more than 0.004. This is the clearest result in the project and it is exactly the thesis: the cheap sensor is the one that matters. Good day.

**11/05/2026 · 4 h · cumulative 38 h**
Problem: the model ranks well (AUC 0.85) but its raw probabilities are badly calibrated (Brier worse than a plain calendar). I almost concluded the model was poor. Fix: Platt scaling on a training split, tested on a held-out season. Brier drops from 0.25 to 0.15, ranking unchanged. Learned that AUC and Brier answer different questions and I need both.

**16/05/2026 · 5 h · cumulative 43 h**
Did: modelled the resistive leaf-wetness grid and ran a bench validation (wet cloth vs dry). 92.8% accuracy fresh. Then tested drift: it corrodes, and accuracy falls to ~63% over eight weeks. Recalibration slows it but cannot undo it once wet and dry readings merge. Decision: treat the grid as a two-month consumable and note a capacitive upgrade for v2. Honest, if a bit disappointing.

**21/05/2026 · 5 h · cumulative 48 h**
Planned: build the node. Did: soldered headers, wired the SHT31 and OLED on I2C, got both talking. The DS18B20 read -127 until I added the pull-up resistor I had forgotten. Small lesson, big time sink.

**25/05/2026 · 5 h · cumulative 53 h**
Did: finished the node, flashed the firmware, calibrated the leaf-wetness threshold with a spray bottle. The OLED shows a live risk band with no WiFi, which is the whole point. Checked the on-device risk matches the Python model on a parity table; they agree.

**30/05/2026 · 4 h · cumulative 57 h**
Did: the spray-reduction analysis. Overall it looks great, a third fewer sprays. But when I split it by region, Gujarat's coverage is only 52%, which is bad. The rule is missing infection windows in the dry region. Something is wrong with the rule.

**04/06/2026 · 4 h · cumulative 61 h**
Fixed the spray rule. The problem was my "spray only if risk is high two days running" filter: in a dry region the dangerous days are single wet nights, and the two-day rule threw them away. Anthracnose needs one wet night, not two. Changed it to act on a single high-risk day. Coverage jumped to 99%. Best lesson of the project: an average hid a flaw the per-region split exposed.

**09/06/2026 · 3 h · cumulative 64 h**
Did: built the Streamlit dashboard and wrote the figure script so every figure redraws from the metrics file. Now I can re-run everything in seconds and the report can never disagree with the data.

**15/06/2026 · 4 h · cumulative 68 h**
Did: wrote most of the report. Tried to write it in my own voice and keep it honest about what is simulated. Re-read the success conditions and checked each one is actually answered with a number.

**22/06/2026 · 3 h · cumulative 71 h**
Did: first self-critique pass as a harsh examiner. Caught a generalisation test that was comparing the wrong things (within-region vs pooled), fixed it. Scrubbed the report for AI-sounding phrasing and stray em-dashes. Re-ran the whole pipeline; all five conditions still pass.

**26/06/2026 · 2 h · cumulative 73 h**
Did: verification gate. Checked the confusion-matrix cells sum to the sample size, that every figure is referenced before it appears, and that every in-text citation is in the reference list. Final proofread. Ready to submit.
