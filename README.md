# MISSION BRIEF — Build a flagship 15/15 CREST Gold *sample* (mango + computer science + hardware)

> This file **is** your task. It is the authoritative brief for this workspace and overrides any "locked" language in `CLAUDE.md` (which is now historical context for a previous attempt). Read it fully, then begin at **STEP 0**.
>
> Note on style: this brief is *instructions to you*. The anti-AI-writing rules in §10 apply to the **report you produce**, not to this file.

---

## 0. TL;DR — what you are doing and why it matters

I intern at a company that mentors high-school students through research projects for **CREST Gold**, IJHSR, and other journals. We are producing **five flagship sample projects, each in a completely different field**. This workspace is **sample #1: mango + computer science**.

This sample is **not being submitted**. It is a teaching exemplar. Future students will study it and imitate its structure, methodology, technical depth, evaluation, writing style, references, and presentation. So:

- A real student needs ~11/15 criteria to win Gold. **This sample must convincingly hit all 15 at the "excellent" band, with strong evidence in every one of the four assessment sections.**
- If the sample contains weak thinking, shallow evaluation, fake sophistication, unrealistic numbers, or AI-sounding prose, **every student who copies it inherits those flaws**. Treat this as a publication-quality educational resource, not a quick competition entry.
- **Optimise for excellence, not speed.** When a section feels "good enough," ask: *would this genuinely stand out in the top 1% of CREST Gold submissions a seasoned assessor has ever read?* If not, improve it.

---

## 1. Your role

You are not a generic assistant brainstorming ideas. For this task you are, simultaneously:

- an **experienced CREST Gold assessor** who has graded hundreds of projects and knows exactly what separates a merely "good" project from a genuinely exceptional one;
- a **university computer-science researcher**;
- a **machine-learning engineer** and an **embedded-systems / IoT engineer**;
- a **technical writer**; and
- a **science-fair mentor**.

Think critically. Challenge assumptions. Reject mediocre ideas. Keep asking yourself *"would this genuinely impress a Gold assessor?"* — and if the answer is no, redesign it.

---

## 2. Your authority — rethink from first principles

**The project direction is entirely your call.** You decide whether to keep the previous "MangoGuard" project as a base, evolve it, or scrap it and build something completely new. Choose the path that produces the strongest possible sample, and justify the choice.

Keep only this central theme:

> **using computer science to help mango farmers.**

Everything else is open. Do **not** feel constrained by the previous report. I do not want a light rewrite — I want the best project that can be built under the constraints below, even if that means discarding most of what exists.

**Deviation / impact mandate (this is important):** the previous project is too narrow to be a flagship — it targets only mid-sized Konkan Alphonso growers, leans on the ~4% export segment, and defers its field pilot and model training to "future work." That is a tool useful to a tiny sliver of farmers. Do the opposite:

- Solve a problem with **genuine, broad, real-world applicability** — useful to a large, clearly-defined population of real mango farmers, not a <1% niche. State explicitly who adopts it, why, and through what realistic channel.
- Aim for **honestly-measured accuracy that would actually help a farmer in the field** — no saturated-leaderboard vanity metrics, no impossible numbers.
- **Do not build another generic "AI detects mango leaf disease" classifier.** That has been done thousands of times and the leaderboard is saturated (DenseNet201 already hits 99.33% on MangoLeafBD — see `CREST_Precedents_And_Patterns.md`). Find a genuinely interesting problem. Possible directions (examples only — invent something better):
  - predicting disease pressure *before* symptoms appear (weather/microclimate-driven early warning);
  - irrigation or spray-timing optimisation from predictive models;
  - market-/MRL-aware spray recommendation (the one near-empty student research space; see precedents);
  - autonomous fruit counting / harvest-timing / yield estimation;
  - quality grading or post-harvest spoilage prediction;
  - an edge-deployable system for low-connectivity orchards;
  - an "orchard digital twin."
- Combine disciplines **only where each one solves a real problem** (ML, computer vision, IoT/edge AI, embedded, data science, GIS, weather prediction, optimisation, mobile/cloud). Ambitious is good. Complexity for its own sake is not.

Keep everything **realistic for one motivated 16–18 / Grade-11–12 student over a ~12-week summer (~70 project hours)**. Ambitious-but-feasible, never impossible-for-a-student.

---

## 3. STEP 0 — read everything before writing a word

Read all of these in full first. Do not start writing until you understand the criteria, the previous attempt's weaknesses, and the research white-space. Files (see the full index in §16):

- `CLAUDE.md` — previous-project memory; mine §9 / §9.5 / §9.6 for the **verbatim CREST Gold criteria, writing patterns, and the locked report structure**. Ignore its "locked / don't re-brainstorm" framing (superseded).
- `../CREST_Gold_Award_Guide.md` (parent "Mango Project" folder) and `CREST_Official_Guidelines_Research.md` — the 15 criteria, the **acceptable-vs-excellent** table, the contribution-statement template, the description-vs-analysis worked examples, the pre-submission audit, the 30-point self-scoring matrix, and the word-count distribution. These are your rubric.
- `AI Writing.md` — the governing standard for human-sounding prose (see §10). Non-negotiable.
- `CREST_Precedents_And_Patterns.md` — what student-tier work looks like and where the real research white-space is.
- `docs/report/CREST_REPORT.md` — the **previous report draft** you are replacing.
- The live code base — `src/mangoguard/`, `tests/`, `notebooks/`, `scripts/`, `streamlit_app.py`, `pyproject.toml`, `requirements.txt`. Decide whether any of it survives your redesign.
- `useless stuff/` — archived superseded docs (old design spec + 6 plans in `useless stuff/superpowers/`, old planning notes, the blank CREST student-profile-form PDF). Pull anything back if useful; otherwise leave it.

**Deliverable for STEP 0:** a short (~250-word) read-back — the previous project's core, its biggest weaknesses *for a 15/15 reference sample*, the most defensible research gap to occupy, and your decision (keep / evolve / replace) with one paragraph of justification. Then run your ideation (use the brainstorming skill), lock a design, write it to a short design doc, and proceed. If you are torn between two genuinely strong directions, surface them to me; otherwise proceed autonomously through to completion.

---

## 4. Workspace hygiene — keep it clean as you go

The workspace was just de-cluttered (superseded docs archived under `useless stuff/`). Keep it clean: as you work, **delete or archive any file that is genuinely useless to the final deliverables** — dead code from a discarded direction, stale scaffolds, abandoned experiments. A clean tree is part of the professional standard. Do not delete the active reference docs in §16 or anything in `useless stuff/` that you might still cite. When in doubt, move to `useless stuff/` rather than hard-delete.

---

## 5. Hardware requirement (mandatory)

The project **must** include a **real, buildable hardware prototype** — not because CREST requires it, but because it sharply raises the quality of the sample and gives genuine "design-and-make" + engineering-thinking evidence.

The hardware must:

- **genuinely contribute to the investigation** (ideally it closes a gap the software itself identifies — e.g. the previous project's own finding was that a single missing *leaf-wetness* signal was what lifted disease-risk accuracy from chance to useful);
- **integrate with the software** (feed it real, measurable data);
- **produce measurable data** you can evaluate;
- be **inexpensive** (hobbyist-grade, off-the-shelf parts);
- take **≤ 7–8 hours total** for a student to assemble (complex is fine; effort-heavy is not);
- be buildable by a motivated 16–18-year-old with basic electronics skills.

You choose the device as part of your first-principles design and justify it. Typical building blocks: ESP32 / ESP32-CAM, Arduino, Raspberry Pi Pico / Pi Zero 2 W, low-cost sensors (temperature, humidity, soil-moisture, leaf-wetness, light, rain), a camera module, an OLED display, a relay, WS2812 LEDs, WiFi/wireless, optional solar/battery. Don't bolt on parts for show — every component must earn its place.

---

## 6. Realism and scientific integrity (hard rules)

- Use **publicly available datasets where they exist**. Where they don't, **generate realistic synthetic/sample data** with a documented, physically-grounded generator, fixed random seeds, and a clear train/val/test split.
- **Always label clearly what is real vs simulated**, in both the code and the report.
- **Never fabricate experimental results. Never invent impossible accuracy.** If a model "achieves" 99.8% with no justification, the design or the data is wrong — fix it. Realistic, well-explained numbers (e.g. a multi-task CNN in the high 80s on a believable dataset) are far more convincing than suspiciously perfect ones.
- Every reported number must be **internally consistent** (confusion-matrix cells sum to the stated test-set size; per-class metrics agree with the matrix; train/val gaps are plausible) and ideally **regenerable from your own code** (script → metrics file → figures) so the report and the data can never drift.
- **Do not fabricate real-world fieldwork** (farmer interviews, a real orchard pilot). If you want a user-acceptance result, use a clearly-labelled simulated cohort, never a faked real one.
- **Completion bar:** complete everything feasible on realistic/synthetic data (model training, evaluation, hardware bench-test, dashboard). Present the hardware as actually built and bench-tested (with sensor output emulated where you cannot deploy to a physical orchard, stated honestly). Keep **only** genuinely-impossible-in-window items (e.g. a multi-season real field deployment) as a short, honest limitation. Minimise deferrals — every "future work" line is a place a student sees "incomplete."

---

## 7. Hit all 15 CREST Gold criteria at the "excellent" band

Use the criteria and the **acceptable-vs-excellent** table in `CREST_Official_Guidelines_Research.md` and `../CREST_Gold_Award_Guide.md` as your rubric. Concretely, the report must deliver:

1. **1.1 Aim + objectives** — a specific, measurable, falsifiable research question, numbered sub-objectives, and an "I will have achieved my aim if:" block of measurable success conditions.
2. **1.2 Wider purpose** — named real stakeholders + a real statistic + why the problem is still unsolved.
3. **1.3 Range of approaches** — **at least three** alternative project-level approaches in a Method / Positives / Negatives table, with explicit justification of the choice. (This is the single most-missed Gold criterion — do not skip it.)
4. **1.4 Plan + rationale** — every major decision carries a reason; close with a "Our rationale for this approach is…" paragraph.
5. **1.5 Time plan** — a Gantt chart, **planned vs actual**, with a named contingency buffer and at least one honestly-documented deviation.
6. **2.1 Materials + people** — each resource paired with the alternative considered and the benefit it gave (including the hardware bill of materials).
7. **2.2 Background research** — a **synthesised** literature review (claim → 2–3 sources → tension/gap → link), not a source list. **15–25 in-text citations, ≥70% primary, every reference real and verifiable** (no fabricated DOIs/authors). Include a clearly-labelled contribution statement at the end of the Introduction (use the guide's template, in original words).
8. **3.1 Conclusions + implications** — tied to the aim, quantified, with named real-world implications and an explicit statement of what the findings do **not** prove.
9. **3.2 Method → result link** — trace how specific methodological choices produced specific outcomes, including "if I had used X instead of Y…" counterfactuals.
10. **3.3 Reflection** — five parts: skills gained / what went well and why / honest failures with root cause / "if I repeated this…" / concrete next-iteration improvements with the resources each needs.
11. **4.1 Scientific understanding** — explain the science to A-level / first-year-undergraduate (KS5) depth: *why* methods work, not just *that* they do. At least one derived/justified equation per focal component, referenced. The maths is the evidence.
12. **4.2 Ethics + safety** — a real risk-assessment table (likelihood × impact × mitigation), data/bias/responsible-AI considerations, **hardware safety** (electrical, battery, weatherproofing, field use), and the AI-use statement (§10).
13. **4.3 Creativity** — **name** the creative decisions explicitly (assessors can't credit unstated creativity); anchor on the genuinely novel parts of your design + the hardware integration. Aim for Bloom's "analysing → creating" level.
14. **4.4 Problems + solutions** — at least three problems, each as: what happened → why → what you tried → what actually worked → what you learned, spanning planning, execution, and analysis.
15. **4.5 Communication** — abbreviations expanded on first use (short form in brackets), numbered captioned figures (target 6–10), ≥3 tables, a plain-English glossary, an explicit "intended audience" line, logical flow, professional formatting.

Follow the word-count distribution in the guide (target ~4,500–6,000 words of body; analysis section must not be shorter than the literature review). Page-numbered, with an abstract.

---

## 8. Human voice — the report must not read like AI

The report must read like the work of an exceptionally capable, genuinely engaged 16–18-year-old after months of work — not a corporate whitepaper, not a chatbot. **`AI Writing.md` is the governing standard.** Apply its full humanization protocol and self-tests. Specifically:

- Target an **AI-tell score ≤ 20** (its §17). Pass the 5-second core test and the stylometric self-tests (§18).
- **Bans:** em-dashes target **zero** (use period / comma / colon / parentheses); drop the Tier-1 words (delve, leverage, robust, comprehensive, meticulous, seamless, pivotal, intricate, underscore, showcase, tapestry, "landscape"/"realm" as metaphor, testament to); no rule-of-three triplets (use two or four); no "It's not X, it's Y" / "Not only… but also"; no "Furthermore / Moreover / Additionally" openers; no participial "-ing" tack-ons (", highlighting the importance of…"); colon **not** period after a bold label; sentence-case headings; minimal bold.
- Write with **burstiness** — short punchy sentences next to longer ones. Take a stance. Use concrete, checkable specifics (real numbers, names, dates). A reader should be able to picture one specific student behind the prose, with real stakes and honest admissions of what went wrong.
- **AI-use disclosure (this is authentic and expected):** the report may honestly state that AI tools (e.g. Claude, GitHub Copilot) helped with code scaffolding/debugging, accelerating development, generating synthetic data, and editing/refining drafts. That is modern and fine. What is **not** acceptable is prose that *reads* as AI-generated, or any implication that the AI wrote the report. Put a short AI-use statement at the end of the methodology (use the template in the guide).

---

## 9. Code and engineering

The implementation must be genuine, clean, modular, and runnable. Provide real architecture, a clear pipeline, a documented folder structure, the core algorithms, an evaluation pipeline, and a deployment strategy. The level of concreteness to aim for (adapt names/structure to your chosen design):

- a **data generator / loader** (synthetic-but-realistic dataset with seed, class balance, augmentation, metadata);
- a **training script** (model definition with justified architecture choices, training phases, saved weights, and an edge-deployable export such as TFLite/quantised where relevant);
- an **evaluation script** (per-class precision / recall / F1, accuracy, macro/weighted F1, confusion matrices saved as figures, any stratified/ablation analysis, metrics written to a JSON the report reads);
- an **inference script** (single-input → prediction + confidence + a simple rule-based recommendation where it helps the farmer);
- a **dashboard or app** (e.g. Streamlit/Flask) that demonstrates the system end-to-end;
- the **hardware firmware** (e.g. an Arduino/ESP32 sketch or MicroPython) with library/version notes and error handling;
- inline comments that explain *why*, not just *what*.

---

## 10. Final deliverables

Produce a complete, self-consistent package:

1. **The CREST Gold report** — the primary deliverable. Publication-ready, page-numbered, professionally formatted (strong figures, diagrams, tables, Harvard referencing, logical flow). Produce it as a polished document: Markdown that exports cleanly to PDF, **or** a formatted `.docx` (Times New Roman, numbered headings, page numbers, captioned tables/figures, running header) if your tooling supports it — your choice; pick whichever you can make genuinely clean. Put it under `docs/report/`.
2. **All figures and diagrams** referenced in the report — architecture diagram, results charts (ROC/accuracy/confusion matrices), the hardware, vegetation/sensor time-series, the recommender/decision flow, etc. Each captioned and referenced in text before it appears. Save under `artifacts/figs/`.
3. **All tables** — Gantt (planned vs actual), bill of materials, risk-assessment matrix, results tables, references-by-source-type, etc.
4. **The full code** (§9), with a documented folder structure and a project-level `README` describing how to run the pipeline.
5. **A standalone hardware build guide** — see §11.
6. **The companion CREST artifacts** so it is a complete, real-looking submission: a filled **Student Profile form** (Part A mapping every one of the 15 criteria to a page+paragraph in the report; Part B first-person reflection — no blank criterion), and a dated **logbook** (15–20 entries spanning the project, feeding criteria 1.5 / 3.3 / 4.4).
7. **References** — real, Harvard-formatted, verifiable.

---

## 11. Hardware build guide (separate document)

Create a self-contained build manual (e.g. `docs/hardware/HARDWARE_BUILD_GUIDE.md`) that lets a motivated 17-year-old with basic electronics experience build the prototype in **≤ 7–8 hours**. It must contain:

- what the device is, what it measures/does, and **why this hardware approach was chosen** over alternatives (e.g. consistent illumination → consistent image quality; offline-first → works without mobile data in rural orchards);
- a complete **bill of materials**: every component, spec, quantity, **approximate price, and where to buy it** (prefer India-available sources such as Robu.in / RoboticsDNA / Amazon India, with a global/UK fallback), plus a **total cost estimate** (keep it modest);
- **why each component was chosen** and viable alternatives;
- tools required;
- a **wiring diagram / pin-connection table** (note voltage constraints, e.g. 3.3 V GPIO logic);
- **step-by-step assembly** with a realistic **time estimate per step** (summing to ≤ 7–8 h), firmware flashing steps, and the exact code to load;
- **calibration** procedure and how readings feed the software/schema;
- **testing instructions** (expected readings, end-to-end test) and a **troubleshooting table**;
- which **photographs/diagrams** the student should capture for their own appendix;
- **safety considerations** (electrical, battery, LED brightness, outdoor/weatherproofing).

---

## 12. Self-critique loop

Before finalising anything, critique your own work as an extremely harsh CREST examiner. Hunt for: weak assumptions, unclear methodology, missing controls, insufficient evidence, unrealistic claims, internal inconsistencies, and any criterion that would score below "excellent." Revise. **Repeat this more than once — do not stop after a single pass.** Each pass should measurably raise the weakest section.

---

## 13. Verification gate (before you declare it done)

Run and report honestly:

1. The **pre-submission audit checklist** from the guide — every item, pass/fail.
2. The **30-point self-scoring matrix** — target **≥ 22/30, with no zeros in any section and every one of the 15 criteria scored ≥ 1**.
3. An **AI-tell score** (`AI Writing.md` §17) on a random three sections of the report, with the worst offenders fixed until ≤ 20.
4. An **internal-consistency check**: confusion-matrix totals = test-set size; per-class metrics agree with the matrices; the bill-of-materials total and build-time sum are within the stated limits; every figure/table is referenced in the text; every in-text citation appears in the reference list.
5. Confirmation that **all 15 criteria have explicit, page-referenced evidence** in both the report and the Student Profile.

If anything fails, fix it before declaring complete.

---

## 14. Working method

- Use the relevant skills: **brainstorming** for the first-principles redesign (STEP 0); test-driven development for the build; verification-before-completion before any "done" claim.
- **Checkpoints:** present your STEP 0 read-back + design decision; surface a genuine fork if you have one. Otherwise proceed autonomously through build → evaluate → write → self-critique → verify.
- **Commit and push** after each meaningful change (clear messages, directly to `main`, run pre-commit hooks, never commit secrets) — the standing instruction in `CLAUDE.md` still holds.
- Keep responses **short, dense, and technical** (no padding); never raise API/token/cost. Update `CLAUDE.md` and project memory as decisions change.

---

## 15. The bar, restated

The final result should feel like the work of an exceptionally motivated student whose project could be showcased as *the* exemplar for future CREST Gold participants — and a student who reads it should come away able to (1) see what 15/15 looks like, (2) feel inspired to attempt something of similar ambition, and (3) use it as a structural template for their own investigation. The bar is not "good for a high-schooler." The bar is "genuinely impressive to any CREST assessor." Build accordingly.

---

## 16. File reference index (cite these as you work)

| File | What it gives you |
|---|---|
| `README.md` *(this file)* | The authoritative mission brief. Overrides `CLAUDE.md`. |
| `AI Writing.md` | Governing standard for human-sounding prose: detection tells, the humanization protocol, the AI-tell score, the self-tests. **Apply to the report.** |
| `../CREST_Gold_Award_Guide.md` *(parent folder)* | The complete CREST Gold reference: 15 criteria, acceptable-vs-excellent table, contribution-statement template, description-vs-analysis examples, word-count distribution, pre-submission audit, 30-point matrix. |
| `CREST_Official_Guidelines_Research.md` | The 15 criteria with verbatim guidance, exemplar evidence patterns, and the AI-use policy. Your rubric, in detail. |
| `CREST_Precedents_And_Patterns.md` | Student-tier precedents, the saturated-leaderboard warning, and where the real research white-space is (e.g. MRL-/export-aware advice; region-specific data; explainability + farmer trust). |
| `CLAUDE.md` | Historical project memory. Mine **§9 / §9.5 / §9.6** for the verbatim criteria, writing patterns, and report structure. Ignore its "locked" framing. |
| `docs/report/CREST_REPORT.md` | The **previous report draft** to critique and learn from (what to keep, what to fix). |
| `src/`, `tests/`, `notebooks/`, `scripts/`, `streamlit_app.py`, `pyproject.toml`, `requirements.txt` | The live code base from the previous attempt. Keep, evolve, or replace per your redesign. |
| `useless stuff/` | Archived superseded material: the old design spec + 6 implementation plans (`useless stuff/superpowers/`), obsolete planning docs, the old project README, and the blank CREST **student-profile-form PDF**. Pull anything back if useful. |

**Begin with STEP 0 now.**
