# CREST Gold Award — Student Profile form

> CREST asks for a Student Profile form alongside the report, one per student. It is the assessor's map: for each of the 15 criteria it points to where in the report the evidence sits, with a short note. This mirrors the official form (download and transcribe from crestawards.org). The "Where" column cites the report's numbered sections; on the exported PDF these map to printed page numbers, which should be filled in last, after the final export.

---

| | |
|---|---|
| Student's first name | Devadit |
| CREST Award level | **Gold** |
| Project title | Reading mango dry matter with eight wavelengths: a low-cost near-infrared meter for harvest timing |
| Mentor name | None — independent project (see the note at the end) |

---

## Part A — criteria checklist

### 1 — Planning the project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **1.1** Clear aim, broken into objectives | §1.1 (aim), §1.2 (conditions S1–S5), §1.3 (six objectives) | One testable aim, five measured success conditions written before the analysis, and six build-and-check objectives; revisited in §5.7. |
| **1.2** Wider purpose | §1.4 | Named stakeholders (smallholder, trader, buyer), a production and loss statistic, and why the problem is unsolved: instrument cost, and cheap sensors looking in the wrong place. |
| **1.3** Range of approaches | §3 | Two trade-off tables. Four ways to give a maturity reading and three ways to build the sensor, each with a reasoned elimination. |
| **1.4** Plan and rationale | §3, §4, §4.8, Appendix A | Every major decision carries its reason; the method is replicable from §4 and the reproduce commands in Appendix F. |
| **1.5** Time plan | Appendix A | Planned-against-actual timeline with a buffer and one documented deviation (the week spent diagnosing the weak first result). |

### 2 — Throughout the project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **2.1** Materials and people | §4.7, Appendix C | Each resource paired with the alternative I weighed against it; full bill of materials; a cooperating grower described how harvest timing is judged now; a reflection on working without a supervisor and what it cost. |
| **2.2** Background, sources acknowledged | §2, References §9 | A synthesis that runs from the physics to the public benchmark to the open cheap-sensor gap; 18 references, most peer-reviewed, cited in the text. |

### 3 — Finalising the project

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **3.1** Logical conclusions and implications | §7 | Each success condition answered with numbers; implications for a smallholder; an explicit statement of what the findings do not prove. |
| **3.2** How actions and decisions affected the outcome | §6 | The choice to pick wavelengths from data rather than buy a chip is traced to the 0.63 R² it bought; the weak first result is traced to band placement. |
| **3.3** Learning and reflection | §8 | Five parts: what I learned, what went well, what went wrong, what I would change, and where it goes next with the resource each step needs. |

### 4 — Project-wide

| Criterion | Where I show this | Note to the assessor |
|---|---|---|
| **4.1** Understanding of the science | §2, §4.2, §4.3, Appendix F | The near-infrared chemistry, partial least squares, the derivative preprocessing and the metrics explained in my own words; the maths and settings in the appendix. |
| **4.2** Ethics and safety | §4.9, Appendix B | Electrical and eye safety; the asymmetry of a wrong maturity call; a measured fairness check across cultivars; no personal data. |
| **4.3** Creative thinking | §6.4 | Four named creative decisions, including simulating the sensor from real spectra before building it, and reading the failure as a design rule. |
| **4.4** Identified and overcame problems | §5.2, §6.2, §8 | The near-useless first result and its diagnosis (placement, not band count); the scatter-correction step that made a model unstable; each with cause and fix. |
| **4.5** Communication | Whole report, glossary Appendix D | Written for a scientifically literate non-specialist; abbreviations expanded, nine captioned figures, tables, a glossary, and the depth quarantined in the appendix. |

Every criterion has explicit evidence; no row is blank.

---

## Part B — personal reflections

*(First draft for the official form; put it into your own words before transcribing.)*

**Why I chose this project.** My family buys Alphonso every summer, and some years the fruit never ripens properly however long we wait. I learned that this comes down to dry matter at harvest, a number growers cannot measure because the meter costs about ₹8.5 lakh. I wanted to know whether I could build one for the price of a school project.

**How it was and was not successful.** It worked better than I expected on the core question. A model using my meter's eight wavelengths, computed from the research spectra, read dry matter almost as well as a laboratory instrument, an R² of 0.84 against 0.85, and I found which wavelengths are needed and why the popular cheap chips fail. The built meter runs that model on the device, but I have not yet validated it against oven-dried fruit, and it is not yet proven on Indian cultivars because the public data are Australian. Those two steps are the gap I have set up a field validation to close.

**What I learned.** Why a handful of wavelengths can stand in for a whole spectrum, because the dry-matter signal is concentrated where sugar, starch and water absorb rather than spread across the light. That a cheap sensor is a different design problem, not a worse instrument. And that a discouraging result deserves to be taken apart rather than believed, since the project's main finding was hiding inside a number I almost wrote off.

**What impact it might have.** A sub-₹2,500 meter that reads maturity turns a grower's guess into a number, which lets a smallholder pick at the right time and prove the quality of a lot at sale. The eight-wavelength design is open for anyone to reproduce, and the finding that off-the-shelf chips are placed wrongly should save other builders the week it cost me.

**What I would improve.** I would arrange the orchard access before the analysis, so the field season was not the part left hanging. I would build the meter with a proper white tile and dark-current correction from the first prototype, since those, not the wavelengths, are what will limit a real device. And I would test the transfer to a new cultivar earlier, because it is the result that most shapes how the meter should be used.

---

## My mentor

This project was completed independently, with no mentor or supervisor. Where I needed to check the spectroscopy or the agronomy I went to the primary literature, recorded in the reference list. A local mango grower has agreed to host the field validation described in Appendix E. AI assistance is disclosed in the report's Appendix E: an assistant was used for coding help, for reasoning about the evaluation design, and for editing drafts.

---

## AI declaration

☑ **AI declaration.** All AI-assisted content has been referenced and declared. The full disclosure (which tool, what it did, and how I checked it) is in the report's Appendix E, "AI use statement".

| | |
|---|---|
| Student name | Devadit Jain |
| Declaration | ☑ I confirm this is my own work. |
| Signature / date | *(Sign and date on the official CREST form.)* |
