# CREST Gold Award — Student Profile Part A: Criteria-Evidence Map

> **Instructions for the student:**
> This is your Student Profile Part A (the checklist). You must submit this alongside your report.
> After finishing the report, fill in the **exact page number and paragraph** for each criterion.
> The "What to look for" column tells you exactly what paragraph to point to. The "What the assessor wants to see" column is what they check when they flip to that page.
>
> **Target:** Meet at least 11 of 15 criteria, covering all 4 sections.
> **Aim for:** 13–14/15 (maximises chance of "excellent" rating).

---

## Section 1 — Planning Your Project

| # | Criterion | Where in report? | Notes to assessor |
|---|---|---|---|
| 1.1 | Set a clear aim and break it down into smaller steps/objectives | Section 1, Introduction, Paragraph 5 (Research Question + 4 Objectives) | Four numbered sub-objectives directly under the research question; each maps to a later section of the report |
| 1.2 | Explain the wider purpose of your project | Section 1, Introduction, Paragraphs 1 and 2; Section 6 Conclusions, Paragraph 2 | Opening statistics on Indian smallholder agriculture; named stakeholders (ICAR, KrishiNet, Redmi 10A hardware) |
| 1.3 | Consider different ways to do your project (justify your choice of method) | Section 3, Subsection 3.1 "Approaches Considered" | Three rejected approaches: training from scratch, classical ML (linking to my prior SowSmart OS sklearn model), single-architecture study |
| 1.4 | Describe your plan and give reasons for the approach you chose | Section 3, Subsections 3.2–3.4 | Every decision is justified: 80/10/10 split with statistical reasoning; augmentation on training set only with data leakage rationale; two-phase LR with catastrophic forgetting explanation |
| 1.5 | Explain how you planned your time and organised who would do what | Section 3, Subsection 3.6 + Appendix A (Gantt chart) | Note the one real deviation: EfficientNetB0 required a second training run in week 7 due to fine-tuning instability |

---

## Section 2 — Throughout Your Project

| # | Criterion | Where in report? | Notes to assessor |
|---|---|---|---|
| 2.1 | Say who and what materials/resources you needed | Section 3, Subsection 3.6 "Resources and Time Plan" | PlantVillage dataset (CC-BY 4.0, Kaggle), Google Colab T4 GPU, TensorFlow 2.x, tf-keras-vis, scikit-learn, student laptop for CPU inference testing |
| 2.2 | Summarise background research and where you found the information | Section 2, Literature Review (all 7 paragraphs) — especially the gap paragraph at the end | In-text citations throughout; sources synthesised, not described sequentially; gap paragraph explicitly states three gaps this study addresses |

---

## Section 3 — Finalising Your Project

| # | Criterion | Where in report? | Notes to assessor |
|---|---|---|---|
| 3.1 | Make logical conclusions and explain implications for the wider world | Section 6, Conclusions, Paragraphs 1 and 2 | Paragraph 1 directly answers the research question; Paragraph 2 names ICAR, KrishiNet, and specific Indian states as stakeholders with hardware cost |
| 3.2 | Describe how what you did affected the outcome (method ↔ result link) | Section 5, Subsection 5.4 "Methodological Influence on Results" | Three explicit method↔result connections: ImageNet weights → high accuracy, crop filtering → inflated accuracy relative to full-dataset benchmarks, class weighting → balanced F1 |
| 3.3 | Explain what you learned and how you would change the project | Section 7, Personal Reflections (Paragraphs 3 and 5); Section 6 Conclusions, Paragraph 3 | Personal Reflections directly answers "what I learned"; Conclusions Paragraph 3 proposes three future directions including INT8 quantisation and Indian field-condition training |

---

## Section 4 — Project-Wide Criteria

| # | Criterion | Where in report? | Notes to assessor |
|---|---|---|---|
| 4.1 | Show understanding of the science behind your project | Section 2 (CNN feature hierarchy, residual connections, depthwise separable convolutions); Section 3 Subsection 3.4 (two-phase training rationale); Section 5 Subsection 5.1 and 5.2 (architecture comparison + Grad-CAM interpretation) | Explains why residual connections solve vanishing gradients (He et al. 2016); explains Grad-CAM formula reference (Selvaraju et al. 2017); never just states results — always explains the mechanism |
| 4.2 | Describe sensible decisions, including safety and risks | Section 3 Subsection 3.7 "Ethical Considerations"; Appendix B (Risk Assessment table) | Four ethical points: CC-BY licence, algorithmic bias (US dataset on Indian crops), deployment harm from false negatives, AI use disclosure. Risk table in Appendix B covers likelihood × severity |
| 4.3 | Show creativity in how you carried out your project | Section 5 Subsection 5.2 (Grad-CAM++ panel comparing all 3 architectures on the same leaf image); Section 1 Paragraph 2 (SowSmart OS motivation); Section 5 Subsection 5.3 (deployment recommendation tied to specific hardware model) | Applying Grad-CAM++ comparatively across three architectures to the same disease image is a non-standard analytical approach that directly addresses the "which architecture sees the right thing" question |
| 4.4 | Explain how you identified and overcame problems | Section 5 Subsection 5.5 "Challenges and How They Were Solved" | Exactly four documented challenges with: what happened, why it happened, what I changed. Challenge 3 (EfficientNetB0 LR) connects back to Tan & Le (2019) literature |
| 4.5 | Explain your project clearly in writing and in conversation | Abstract (5-sentence structure); all figures numbered and captioned; all acronyms expanded on first use; report structured with numbered sections and numbered pages | Abstract can be understood by someone with A-level biology background; Conclusions can be understood without reading the full paper |

---

## Part B — Personal Reflections

> Write ~400 words (approximately half a page). This section is individual — write it yourself, in your own voice.

Answer these five questions (one short paragraph each):

**1. Your role and tasks completed:**
Describe specifically: which Colab cells you ran, which debugging steps you took, which sections of the report you wrote. Be honest — you can say that the code structure was developed with AI assistance (see Appendix C) and that you ran, verified, and debugged the notebook.

**2. How the project was successful (or not):**
State what the results showed. Did [best architecture] perform as expected? Were any results surprising? What does this mean for whether your research question was answered?

**3. What you learned:**
Technical: what you now understand about CNNs, transfer learning, Grad-CAM, Python, TensorFlow. Non-technical: what you learned about academic writing, reading research papers, planning a long-term project.

**4. Wider impact:**
Who would benefit from this research and how? How would a farmer in Andhra Pradesh actually use this? What would need to happen for the research to become a real app?

**5. What you would change and what next:**
If you repeated the study, what would be the single most important change? (Suggested: using Indian field-condition images instead of lab images.) What is the most impactful follow-up project you could imagine?

---

## Quick Criteria Count

| Section | Criteria # | Status |
|---|---|---|
| Section 1 — Planning | 1.1, 1.2, 1.3, 1.4, 1.5 | All 5 evidenced |
| Section 2 — Throughout | 2.1, 2.2 | Both 2 evidenced |
| Section 3 — Finalising | 3.1, 3.2, 3.3 | All 3 evidenced |
| Section 4 — Project-Wide | 4.1, 4.2, 4.3, 4.4, 4.5 | All 5 evidenced |
| **Total** | **15/15** | **All criteria met** |

> **Note:** Meeting all 15 is the target. The assessor still assigns "acceptable" or "excellent" per criterion — the difference is in depth and specificity. Use the "Acceptable vs. Excellent" table in `CREST_Gold_Award_Guide.md` to push each criterion from acceptable to excellent.

---

## Final Submission Checklist

Before uploading to [apply.crestawards.org](https://apply.crestawards.org):

- [ ] Report uploaded (PDF, numbered pages)
- [ ] Student Profile — Part A (this completed checklist) uploaded
- [ ] Student Profile — Part B (Personal Reflections) uploaded
- [ ] All page number references in Part A filled in with actual page numbers
- [ ] Appendix C (AI disclosure) included in the report
- [ ] You can verbally explain to an assessor: what transfer learning is, why you chose these 3 architectures, what the Grad-CAM shows, what your recommendation is and why
