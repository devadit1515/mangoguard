# CREST Gold Student Profile form

**Student:** Devadit Jain · Grade 11 · 2026
**Project:** AamRakshak — a ₹2,000 leaf-wetness sensor node that predicts mango anthracnose and cuts needless fungicide sprays
**Report:** `CREST_REPORT.md` (page-numbered on PDF export). Section references below use the report's numbered sections; on the PDF these map to the printed page numbers.

---

## Part A — criteria checklist (where the assessor finds the evidence)

| # | Criterion | Where in the report | Note to assessor |
|---|---|---|---|
| 1.1 | Clear aim broken into objectives | §1.1 (aim), §1.2 (measurable success conditions S1–S5), §1.3 (six numbered objectives) | The aim is a single falsifiable question; success is pre-registered as five measured conditions. |
| 1.2 | Wider purpose | §1.4 | Named stakeholders (grower, farm worker, consumer, FPO officer), a production statistic, and why the problem is unsolved (an affordability gap, not a knowledge gap). |
| 1.3 | Range of approaches | §3 | Two decision tables (project-level and sensor-level), each with for/against and an explicit justified choice. |
| 1.4 | Plan and rationale | §3 (choices with reasons), §4 (method), §4.9 + Appendix A (plan) | Every major decision carries a reason; the approach is justified against the alternatives. |
| 1.5 | Time plan | Appendix A | Gantt-style planned-vs-actual with a named buffer and one honestly documented deviation (the spray-rule failure in week 8). |
| 2.1 | Materials and people | §4.8, Appendix C (bill of materials) | Each resource paired with the alternative considered and the benefit it gave. |
| 2.2 | Background research | §2, References §9 | Synthesised review (claim → sources → tension → gap), 20 real references, majority primary. |
| 3.1 | Logical conclusions + implications | §7 | Each success condition answered with numbers; named real-world implications; an explicit statement of what the findings do not prove. |
| 3.2 | Method → result link | §6 | Traces how specific choices produced specific outcomes, with "if I had used X instead" counterfactuals. |
| 3.3 | Reflection | §8 | Five parts: learned / went well / went wrong / would do differently / next steps with the resources each needs. |
| 4.1 | Scientific understanding | §4.2 (Akem logistic derived and justified), §4.3 (sensor physics), §4.7 (ROC-AUC, Brier), §2 | At least one derived/justified equation per focal component; the maths is the evidence. |
| 4.2 | Ethics and safety | §4.10, Appendix B (risk table) | Electrical/battery/field safety, responsible-advice asymmetry (false negative is the costly error), data note, AI-use statement. |
| 4.3 | Creativity | §6.4 | Four named creative decisions (₹100 sensor recovering a ₹40k signal; on-device model; non-circular test design; reframing detection→prediction). |
| 4.4 | Problems and solutions | §6.2, §6.3, §5.4, §8 | Three+ problems each as what happened → why → tried → worked → learned, spanning execution and analysis. |
| 4.5 | Communication | whole report; audience line (top), abbreviations on first use, 11 captioned figures, ≥3 tables, glossary (Appendix D) | Written for a scientifically literate non-specialist; logical structure; professional formatting. |

Every criterion has explicit evidence; no row is blank.

## Part B — personal reflection

**My role and what I did.** I did the whole project myself: I chose the question, designed the sensor node and wrote its firmware, built the risk model and the simulation, ran the evaluation, built the dashboard, and wrote this report. I used an AI assistant for code scaffolding, for help making the test non-circular, and for editing drafts, all disclosed in Appendix E; the decisions and the science are mine.

**How it went.** It worked better than I expected on the core question and worse on one design detail, which taught me the most. The headline result is strong and honest: a ₹2,000 node ranked infection days almost as well as a ₹40,000 station (AUC 0.857 versus 0.864) and far better than a free weather feed (0.753), and the leave-one-out test showed the cheap leaf-wetness sensor is exactly the part that carries the prediction. Acting on it cut sprays by a third while still covering 99% of the dangerous days. The part that went wrong, and that I am almost glad about, was my first spray rule: it quietly threw away the isolated wet days that matter most in dry regions, and I only caught it by breaking the numbers out by region. That is in the report because finding it is the science.

**What I learned.** Why a logistic regression is the right shape for a yes-or-no event and why leaf wetness, not humidity, is the variable that matters; that a cheap sensor is a different engineering problem (corrosion and calibration) rather than a worse one; and that an average can hide the result you most need to see.

**Impact on the wider world.** If the barrier to weather-based mango spraying was the price of one sensor, then a ₹2,000 node removes it. That means fewer wasted sprays, less chemical exposure for workers and consumers, and a route, through cooperative field officers, to the millions of smallholders who will never own a weather station.

**What I would improve, and develop next.** I would secure a real orchard and a fortnightly visit before building anything, so the field season was not the part I had to defer; I would build the leaf-wetness sensor as capacitive from the start to beat corrosion; and I would run a small farmer-trust study to find out whether growers actually act on the screen. The next version would also add a powdery-mildew module so one node covers the two main mango diseases.
