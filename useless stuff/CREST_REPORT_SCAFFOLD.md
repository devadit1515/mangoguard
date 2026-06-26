# A market-conditioned pesticide recommender for Konkan Alphonso mango (DRAFT SCAFFOLD)

> **CREST Gold submission scaffold.** This file mirrors the locked structure in CLAUDE.md §9.6. Each section opens with the CREST criteria it primarily satisfies and the writing patterns from §9.5 it should mimic. Replace every PLACEHOLDER with the student's own words; commit prose updates in dedicated docs(report) commits.

**Working title (for the form):** *Smarter Mango Spraying with Machine Learning and Open Data* (Environmental Science, Project setting: Other, Partner scheme: None).

**Intended audience:** "Someone with a good amount of scientific literacy but no background or specialist knowledge of the topic" (verbatim CREST 4.5 phrasing).

---

## 0. Abstract (~250 words) -- satisfies 4.5

> PLACEHOLDER. Write last. Five sentences: (1) the problem (Indian mango residue-driven rejections), (2) what we built (an MRL- and RASFF-aware recommender that ingests data from existing monitoring systems), (3) the method spine (PPI risk engine, market-conditioned filter pipeline, counterfactual evaluation against historical RASFF data), (4) the headline result (relative_improvement_pct from `artifacts/eval_metrics.json`), (5) the wider implication.

---

## 1. Aim, success conditions, and objectives (~800 words) -- satisfies 1.1, 1.2, 4.5

### 1.1 Aim

> PLACEHOLDER -- one broad-sentence aim. Use the CLAUDE.md §5 focal-research-claim wording as starting material.

### 1.2 Success conditions ("I will have achieved my aim if:")

> Mimic the CREST 1.1 exemplar block: a bulleted list of measurable conditions.
> * I have shown that disease-risk prediction accuracy scales monotonically with the number of integrated monitoring systems.
> * I have shown via RASFF counterfactual that MangoGuard's recommender prevents >= 30% more rejections than the ICAR-CISH calendar baseline.
> * The cooperating farmer accepts >= 50% of recommendations during Visit 2.
> * >= 2 FPO officers and >= 1 APEDA-registered exporter validate the recommender's utility.

### 1.3 Numbered objectives (six)

> One per Module (CLAUDE.md §6) + the evaluation harness. Cite specific files / code where each is implemented.

---

## 2. Wider purpose and affected populations (~800 words) -- satisfies 1.2, 3.1

> PLACEHOLDER. Quantify (table required by 4.5 pattern #7): smallholder Alphonso population in Devgad / Ratnagiri / Sindhudurg, share of domestic vs export channels (96% / 4%), affected exporter cohort (APEDA), policy lever (FSSAI MRL enforcement), consumer angle.

### 2.1 Stakeholder map

| Stakeholder | Direct or indirect | What MangoGuard offers them |
|---|---|---|
| Mid-sized Konkan grower | Direct | per-block per-segment spray decisions |
| FPO field officer | Direct | force multiplier across 100-500 small farmers per officer |
| Smallholder grower | Indirect | served via FPO |
| Konkan exporter | Indirect | fewer RASFF rejections at gate |
| Consumer | Indirect | lower residue exposure |

---

## 3. Range of approaches considered (~1,200 words) -- satisfies 1.3, 3.2

### 3.1 Approach-level alternatives (CREST 1.3 exemplar pattern: Method | Positive | Negative)

> Three approaches to architecture; positives/negatives bullets per approach (per the 1.3 exemplar method-comparison structure).
> 1. **Pure computer-vision** (photo-only).
> 2. **Rule-based MRL-only** (no risk engine).
> 3. **Hybrid risk-engine + MRL recommender** (chosen).

### 3.2 Hardware tradeoff

> Two-option comparison: install new IoT vs interoperability layer (CLAUDE.md change log 2026-05-30). Chosen: interoperability.

---

## 4. Plan and rationale (~600 words) -- satisfies 1.4

### 4.1 Six-step plan

> PLACEHOLDER -- numbered list of six objectives. End with one rationale paragraph beginning **"Our rationale for this approach is..."** (CREST 1.4 exemplar pattern).

---

## 5. Background research and literature review (~2,000 words) -- satisfies 2.2, 4.1

### 5.1 Anthracnose epidemiology -- HTR + logistic regression

> Cite Akem (2006) for the canonical anthracnose HTR formula. Derive the logistic regression mathematically (this is one of the 4.1 KS5-depth anchors).
> ```
> logit(p) = beta_0 + beta_htr * HTR + beta_lw * LW_hours + beta_sun * sunshine + beta_wind * wind
> ```

### 5.2 Powdery mildew T-band x RH window

> Cite NHB Bulletin 31 + ICAR-CISH. Derive the optimal-band Gaussian product (T_min, T_max, RH bands defined in `src/mangoguard/risk/powdery_mildew.py`).

### 5.3 Mango hopper -- CROPSAP x local-T triangular multiplier

### 5.4 NDVI / NDRE / NDMI biophysics

> Chlorophyll-a / chlorophyll-b absorption bands. NDRE biophysics rationale.

### 5.5 ROC-AUC, Brier score, Beta-prior conjugacy

> The mathematical bases used in `risk.calibration` and `recommend.rasff`.

### 5.6 MRL pharmacology + RASFF + CIB&RC

### 5.7 Inline citations + reference list

> Use Author, Year format throughout. >= 25 references; >= 70% primary sources.

---

## 6. Methodology -- module by module (~3,500 words) -- satisfies 1.4, 2.1, 4.1, 4.3

### 6.1 System architecture diagram

> Figure required: 5-module block diagram + data flow.

### 6.2 Module 1 -- Disease detector (MobileNetV3 + Grad-CAM)

### 6.3 Module 2 -- Orchard health (NDVI/NDRE/NDMI queries + anomaly + seasonal)

### 6.4 Module 3 -- Spray Audit & Recommender (FOCAL)

> This is the 4.3 creativity anchor section. Spell out the decision flow exactly:
> 1. compute_ppi -> primary pathogen.
> 2. CIB&RC pesticides_for_pathogen.
> 3. PHI filter.
> 4. MRL filter (market-conditioned).
> 5. RASFF filter (export segments, cutoff 0.20).
> 6. Ranker (log-efficacy / log-half-life / log-cost).
> 7. Top + alternatives.

### 6.5 Module 4 -- Yield + Mandi Price (XGBoost + SHAP)

### 6.6 Module 5 -- AskHapus chatbot

### 6.7 Evaluation harness (CROPSAP retrospective + RASFF counterfactual)

---

## 7. Ethics, safety, and AI use (~800 words) -- satisfies 4.2

### 7.1 Risk assessment

> Risk-assessment table (1-5 likelihood x 1-5 impact) in Appendix B. Items: orchard heat stress, pesticide exposure, snake / insect risk, vehicle travel.

### 7.2 Farmer consent

> Consent form (English + Marathi). Reference Indian Digital Personal Data Protection Act 2023.

### 7.3 Pesticide recommendation safety disclaimer

> Recommendations are advisory, not prescriptive; final responsibility rests with the farmer; PHI compliance is non-negotiable.

### 7.4 AI use disclosure

> Per CREST AI policy (https://www.crestawards.org/help-centre/crest-guidelines-on-use-of-ai-for-students/). See Appendix E for the full statement.

---

## 8. Results and findings (~2,000 words) -- satisfies 3.1, 3.2, 4.1

### 8.1 Disease-pressure discrimination (Notebook 05, retrospective)

> Pull figures from `artifacts/eval_metrics.json` + `artifacts/figs/`:
> * ROC-AUC: MangoGuard PPI vs seasonal-mean vs ICAR-CISH calendar.
> * Brier score.
> * Per-pathogen confusion (50 cutoff).

### 8.2 RASFF counterfactual prevention rate

> Headline number for the report. Pull from `evaluate_rasff_counterfactual` results: `prevention_rate_mangoguard`, `prevention_rate_icar_baseline`, `relative_improvement_pct`. Spec target: >= 30%.

### 8.3 Connector-coverage tier study (interoperability claim)

> Plot AUC vs number of integrated systems (free-only / + 1 commercial / multi-system).

### 8.4 Cooperating-farmer pilot (Visit 2)

> Acceptance rate + qualitative quotes from `data/fieldwork/visit_2.yaml`.

### 8.5 Yield + price MAE vs seasonal-mean baseline

---

## 9. Problems encountered and how they were overcome (~1,200 words) -- satisfies 4.4

> Each entry in the CREST 4.4 three-stage structure: (problem) -> (workaround tried) -> (root-cause fix).
> 1. Monsoon Sentinel-2 cloud blackout.
> 2. MangoLeafBD region mismatch vs Indian Alphonso.
> 3. No public API for Fyllo / Fasal.
> 4. PLACEHOLDER MRL / CIB&RC / RASFF data risk.
> 5. Plantix Vision API gated -- dropped from connector list.

---

## 10. Conclusions and wider-world implications (~1,500 words) -- satisfies 3.1

> Tie each module's result back to the aim. Quantify the affected populations (cross-reference table from §2). Name the downstream artifact (open-source Streamlit app + GitHub repo + reusable CIB&RC / MRL data schema).
> Policy implications (APEDA, FSSAI, exporter, consumer).

---

## 11. Reflection and future work (~1,200 words) -- satisfies 3.3

> Five-part reflection per CLAUDE.md §9.5 pattern #9:
> 1. Skills gained.
> 2. What went well (team / individual).
> 3. Honest failures with root cause.
> 4. "If I were to repeat this..."
> 5. Concrete next-iteration improvements with the resources/time they'd require.

### 11.1 Future work directions

* Multi-cultivar (Kesar, Dasheri).
* Drone integration (BharatRohan-style hyperspectral) if DGCA permission obtainable.
* Exporter-buyer marketplace integration.

---

## 12. References

> Harvard / (Author, Year) format. >= 25 entries. Generate from `CREST_Reference_List.md`.

---

## Appendix A -- Gantt chart (planned vs actual) -- satisfies 1.5

## Appendix B -- Risk assessment + farmer consent form -- satisfies 4.2

## Appendix C -- Code samples + open-source data manifest -- satisfies 4.3

## Appendix D -- Plain-English glossary -- satisfies 4.5

> Required terms: MRL, PHI, NDRE, NDVI, RASFF, HTR, ROC-AUC, CIB&RC, FSSAI, FPO, APEDA, PPI, GDD, IPM.

## Appendix E -- AI use statement -- satisfies 4.2, 4.5

> Per CREST AI policy: each tool, task, date, prompt sample, post-editing performed.
