# CREST Precedents and Patterns: AI for Mango Cultivation in India

A field scan of student-publication venues, mango-specific AI research, and CREST Gold criteria, conducted to calibrate a 12-week Grade 11 project. All claims are linked to the source surfaced in the search.

## Critical Context — Read This First

**JEI tightened its scope in March 2026 and will no longer accept "purely computer science, data mining, or projects based solely on publicly available datasets"** ([JEI guidance summary](https://emerginginvestigators.org/submissions/faq), via Aralia's [guide](https://www.aralia.com/helpful-information/guide-to-journal-of-emerging-investigators/)). For a mango + AI project this is decisive: a PlantVillage-only or MangoLeafBD-only CNN paper is now out-of-scope for JEI. The project must include either original data the student collected, a hypothesis-driven experimental component (e.g., field trial, farmer user study, soil-sample comparison), or a life-sciences framing. **JSR, STEM Fellowship, and arXiv remain viable for pure ML work.**

CREST Gold separately requires ~70 hours, 11 of 15 criteria, and a portfolio that "documents the full research, design, or communication process from aim to conclusion, supported by materials such as raw data, sketches, images, videos, appendices, feedback forms, or logbooks" ([CREST Gold criteria](https://www.crestawards.org/help-centre/gold-criteria-guidance/), [Gold student guide](https://secondarylibrary.crestawards.org/student-guide-gold/62444084/2)). AI use is allowed if referenced and evidenced ([CREST AI guidelines](https://www.crestawards.org/help-centre/crest-guidelines-on-use-of-ai-for-students/)).

## Mined Precedents — Student-Tier Papers

### 1. Samay Jain, "Crop Disease Detection with Machine Learning," JSR 14(1), 2025
[Paper](https://www.jsr.org/hs/index.php/path/article/view/8470) | DOI 10.47611/jsrhs.v14i1.8470. Mission San Jose High School (US).
- **Topic**: CNN crop disease classifier with a medication-recommendation layer.
- **Method**: MobileNetV2 transfer learning on a public image dataset; 87% test accuracy; rule-based "medication" lookup after classification.
- **Novel contribution**: not the model — the bolt-on advisory step ("here's a disease + here's the treatment").
- **Strengths**: clear problem framing tied to the USDA $220B annual crop-loss figure; honest accuracy number; functional decision layer beyond classification.
- **Weaknesses**: no original dataset, no field validation, no baseline comparison beyond reporting a single number, the "recommendation" is a static lookup not a model.
- **Lesson**: JSR HS accepts modest accuracy (sub-90%) **if** the work has a clear application wrapper around the model. But this paper would now likely fail JEI's new "publicly available datasets only" filter.

### 2. Kar, S. & Willert, J., "CropMates: IoT and AI Integrated System to Detect Crop Diseases and Nutrient Deficiency," JSR 10(4), 2021
[Paper](https://www.jsr.org/hs/index.php/path/article/view/2079)
- **Topic**: GPS drone surveys farm; AlexNet disease classifier + ANN nutrient-deficiency model from IoT soil sensors.
- **Method**: AlexNet on PlantVillage (38 classes, 87,000 images); ANN on 20,000 soil-sensor data points.
- **Novel contribution**: integration story — combining drone vision, sensor ML, and a pipeline. The framing is "system," not "model."
- **Strengths**: ambitious systems framing; uses two distinct ML models; ties hardware (drone, sensors) into the pipeline; positions itself as a "large farm" deployment, not a lab demo.
- **Weaknesses**: no real drone flight reported, no farm partner named, accuracy of integrated system not measured end-to-end.
- **Lesson**: **dashboards/multi-modules can be published if you frame as a system AND pick one ML claim to defend rigorously**.

### 3. JSR HS, "Fully Automatic Controlled Environment Agriculture using ML-based Plant Size Estimator"
[Paper](https://www.jsr.org/hs/index.php/path/article/view/3926)
- **Lesson**: estimation/regression problems (size, yield, days-to-harvest) are accepted at JSR — not just classification. Useful for a mango yield-prediction angle.

### 4. JSR HS, "Crop Yield Prediction across Climate Zones" (multi-model)
[Paper](https://www.jsr.org/index.php/path/article/view/2644)
- **Topic**: compares RF, XGBoost, RNN, ANN, LSTM, KNN for yield prediction by climate zone.
- **Novel contribution**: the **comparative analysis itself**, not a new model.
- **Lesson**: a benchmark/comparison paper is publishable at JSR — meaning a "we benchmarked 5 CNNs on a mango dataset under realistic perturbations" angle is viable.

### 5. JSR HS, "Drought Prediction with Streamlit Interactive App"
[Paper](https://www.jsr.org/hs/index.php/path/article/view/8737)
- **Lesson**: deploying as a Streamlit dashboard is acceptable and even encouraged in JSR — they explicitly published this. **Direct precedent for the dashboard format the student wants.**

### 6. JSR HS, "Smart Greenhouse for STEM Education"
[Paper](https://www.jsr.org/hs/index.php/path/article/view/7505)
- **Lesson**: education/impact framing is publishable. If part of the mango dashboard is positioned as a farmer literacy / extension tool, this is precedent.

## Mined Precedents — Adjacent Mango SOTA (the ceiling)

### 7. Ahmmed et al., "Fine-Tuned CNN-Based Approach for Multi-Class Mango Leaf Disease Detection," arXiv:2510.05326 (Oct 2025)
[arXiv](https://arxiv.org/abs/2510.05326)
- 5 backbones (DenseNet201, InceptionV3, ResNet152V2, SeResNet152, Xception) on MangoLeafBD (8 classes). DenseNet201 hits 99.33%.
- **Implication**: leaderboard on MangoLeafBD is saturated. Pushing accuracy is not a publishable contribution anymore — the gap is elsewhere.

### 8. "GourNet: A CNN-Based Model for Mango Leaf Disease Detection"
[arXiv](https://arxiv.org/abs/2604.27764) | [code](https://github.com/ekramalam/GourNet-Repo)
- 683K-parameter model, 97% on MangoLeafBD.
- **Implication**: **efficiency / on-device / low-parameter** is a live publishable angle, especially with a Grad-CAM and farmer-phone deployment story.

### 9. Indian J. Horticulture, "Explainable AI for mango leaf disease detection: bridging the gap between model accuracy and farmer usability"
[Paper](https://journal.iahs.org.in/index.php/ijh/article/view/2988)
- Modified VGG-16 + Grad-CAM on MangoLeafBD; 92.8% accuracy; **explicit web UI + farmer-trust study**.
- **Implication**: **explainability + usability is the live publication frontier in mango ML right now.** This is the most directly relevant precedent for a dashboard project.

### 10. "ViX-MangoEFormer: Vision Transformer–EfficientFormer Ensemble with XAI for Mango Leaf Disease," Computers 14(5), 2025
[MDPI](https://www.mdpi.com/2073-431X/14/5/171)
- Transformer ensemble + explainability on imbalanced sets.
- **Implication**: the *imbalance-robustness* angle (rare diseases like Cutting Weevil) is publishable.

### 11. "South Indian Mango Leaf Disease Detection," CMC 77(3), 2023
[Paper](https://www.techscience.com/cmc/v77n3/55036)
- South-India-specific dataset collection — explicit acknowledgment that MangoLeafBD is Bangladesh-only and South Indian conditions differ.
- **Implication**: a *region-specific Indian dataset* (Konkan, Ratnagiri, Krishnagiri, Chittoor) is an open, publishable contribution.

### 12. PeerJ 2025, "Pre-harvest mango yield prediction using ANN based on leaf nutrient variability"
[PeerJ](https://peerj.com/articles/20013/)
- ANN on leaf-N, P, K data → pre-harvest yield.
- **Implication**: yield prediction from cheaply measurable inputs (soil/leaf nutrients, weather) is a live area and **does not require a CNN or images**, lowering the data-collection bar.

### 13. Nguyen-Huy et al., "Climate Predictors for Mango Yield, Tamil Nadu 2008–2019"
[SSRN](https://doi.org/10.2139/ssrn.4893902) | [ScienceDirect quantifying-error paper](https://www.sciencedirect.com/science/article/pii/S0168169925005563)
- 31 Tamil Nadu districts, copula + ML; identifies Palmer Drought Severity Index, T_min, evapotranspiration as top predictors.
- **Implication**: openly available IMD/PDSI/AGMARKNET data + standard ML = a tractable solo research arc with publishable, India-specific findings.

### 14. "Attention-based Deep Learning for Mango Price Prediction" (preprint)
[Sciety](https://sciety.org/articles/activity/10.20944/preprints202601.0660.v1) and [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0283584)
- 2001–2025 dataset; hybrid ETS+SVM reaches R² = 0.873.
- **Implication**: AGMARKNET mango-price forecasting is publishable; the student could reproduce + extend with mandi-level granularity.

### 15. "Interpretable Produce Price Forecasting for Small/Marginal Farmers in India," arXiv:1812.05173
[arXiv](https://arxiv.org/pdf/1812.05173)
- Collaborative filtering on Indian mandi prices, designed around farmer constraints.
- **Implication**: clear academic precedent for "ML targeted at smallholder usability."

### 16. RASFF pesticide-rejection literature
[PMC9324178 on RASFF pesticide notifications](https://pmc.ncbi.nlm.nih.gov/articles/PMC9324178/) | [MDPI 2025 RASFF border-rejection analysis 2008–2023](https://www.mdpi.com/2071-1050/17/7/2923) | [Ratnagiri pesticide case study](https://www.academia.edu/43980330)
- India is the #1 source country for RASFF pesticide notifications (18.1%); Imidacloprid, Cypermethrin, Quinalphos, Hexaconazole repeatedly cited in Ratnagiri Alphonso.
- **Implication**: a **"safe-pesticide recommender that explicitly checks EU MRLs and predicts export-rejection risk"** is a genuinely novel student angle — no existing student paper does this.

## Patterns of Excellence — the 15 Lessons That Actually Matter

1. **Original data is now the gatekeeper for JEI.** The March 2026 JEI policy means a PlantVillage/MangoLeafBD-only paper will not pass. You need *some* original data — even 200–400 photos of mango leaves shot in a local orchard, or 30 farmer-survey responses, or one experimental comparison.
2. **JSR HS still accepts public-dataset ML if there is an application wrapper or comparison.** The bar is lower than JEI but you still need a defensible "what's new."
3. **Mango leaf disease accuracy is saturated.** DenseNet201 at 99.33% on MangoLeafBD means a higher-accuracy claim is not publishable. **Move the metric: parameters, latency, robustness, imbalance, region.**
4. **Explainability + farmer usability is the open frontier.** A student doing the same with even 5–10 farmer interviews has a paper.
5. **Region-specific Indian datasets are a real gap.** MangoLeafBD is Bangladesh. Collecting 300–500 images at one Indian orchard (Konkan/Ratnagiri Alphonso, Krishnagiri Totapuri, Malihabad Dasheri) is a publishable contribution by itself.
6. **The successful JSR "system" papers frame one ML component as the focal research claim.** The dashboard format works only if you choose one module to defend rigorously and call the rest "supporting modules."
7. **Stakeholder validation is a cheap differentiator.** 5–10 structured farmer interviews + a SUS-style usability survey is enough to credibly cite.
8. **Yield prediction does not require images.** Tabular nutrient/climate data also works. This is the most solo-feasible mango research path.
9. **Pesticide / MRL / export-rejection ML is essentially untouched at student level.** Genuine white space.
10. **CREST Gold rewards process artifacts, not model accuracy.** A weekly logbook, a pre-registered hypothesis, and farmer-feedback forms automatically clear 4–5 of the 15 criteria.
11. **Baseline + error analysis is the cheapest way to look like a researcher.** Always include: simple baseline (e.g., color-histogram + SVM), one transfer-learning model, and a per-class confusion matrix.
12. **Deployable artifact = bonus credibility.** A live demo URL in the manuscript helps reviewers.
13. **Imbalanced/minority classes are publishable angles on their own.** A student paper that specifically tackles the worst-performing class (data augmentation, focal loss) and reports honest per-class metrics is a clean contribution.
14. **Saturation in CV means tabular ML is the higher-marginal-value angle.** Crop recommendation from soil-NPK, price/yield from tabular data are less crowded than leaf-image classification.
15. **The JEI rejection mode you most need to avoid is "literature review or invention description."** Frame the project around a falsifiable claim: e.g., "Grad-CAM explanations increase Alphonso growers' trust in disease predictions, measured by SUS score."

## Realistic Targets for a 12-Week Mango Project

**Venue ranking, given 12 weeks solo and the JEI March-2026 rule change**:

1. **JSR High School track** — *most realistic*. Direct precedent for the dashboard format, multi-model comparison, and modest-accuracy ML. Acceptance bar: clear problem, working model, baseline comparison, some discussion of limitations. Original data is not strictly required.
2. **STEM Fellowship Journal** — viable for Canadian-affiliated students or via data science writing competitions. Better for data-science-style writeups with public datasets.
3. **arXiv (cs.CV or cs.LG)** — no peer review barrier; a Grade 11 student can post if the work is technically sound. Excellent for visibility, mediocre for "credential." Useful as a parallel deposit alongside a JSR submission.
4. **JEI** — *now harder*. Would need a genuine experimental/biological hypothesis (e.g., a field disease-prevalence survey, a controlled comparison of pesticide regimes informed by ML predictions, or a user study with measurable trust outcomes). Pure CNN-on-images will not pass post-March-2026.
5. **IEEE high-school track / ProjectBoard / Regeneron-ISEF** — competition tracks, not journals; useful as parallel submissions.

**Minimum bar to clear at JSR HS**:
- A defined research question.
- One ML model trained end-to-end with code in a repo.
- One baseline comparison or one ablation.
- A confusion matrix or per-class error breakdown.
- A clear "limitations" section.
- ~3,000–6,000 words, IEEE/JSR template.

**What would make the paper competitive (not just publishable)**:
- One **original component** the literature does not have (regional dataset, farmer user study, MRL-aware advisory, low-parameter on-device model, multi-modal leaf+fruit).
- Honest reporting of failure cases.
- A live deployment artifact (Streamlit/Gradio) linked in the manuscript.
- Stakeholder validation: even 5 farmer interviews with structured feedback is more than most student papers show.

## Concrete Project Shape Ideas

Each idea is researchable in 12 weeks solo, has a clear publishable claim, and addresses a real gap.

### Idea A — "Konkan-Alphonso Leaf Disease: a Region-Shift Study"
**Claim**: models trained on Bangladesh's MangoLeafBD ([dataset](https://data.mendeley.com/datasets/hxsnvwty3r/1)) degrade on Indian Alphonso conditions; targeted fine-tuning with a small original Indian set recovers performance.
**Work**: collect 300–500 leaf photos at one accessible orchard (one varietal, one region) labeled with 4–6 disease classes. Train DenseNet201/MobileNetV3 on MangoLeafBD; evaluate zero-shot on your data; fine-tune; report Δ-accuracy and per-class confusion.
**Publishability**: directly addresses the South-Indian-gap finding from CMC 2023. Original data clears the JEI bar.
**Feasibility**: requires one orchard visit + ~2 weeks of labeling. Solo-feasible.

### Idea B — "Pre-Harvest Mango Yield from Public Indian Agroclimatic Data"
**Claim**: XGBoost on IMD weather + AGMARKNET + district-level mango acreage predicts district yield ±X% in Maharashtra/Tamil Nadu; SHAP identifies top predictors.
**Work**: replicate the Tamil Nadu copula-ML paper at a smaller, simpler scale; add SHAP for interpretability; benchmark vs. a naive seasonal-mean baseline.
**Publishability**: tabular ML on Indian public data with a SHAP/interpretability angle. Hits the multi-model-comparison template perfectly.
**Feasibility**: no fieldwork; entirely public-data. Solo-feasible in 6–8 weeks.

### Idea C — "MRL-Aware Pesticide Recommender for Indian Mango Exports"
**Claim**: a system that takes a disease prediction + destination country and outputs ranked pesticides constrained by that country's MRL list, predicting export-rejection probability from historical RASFF data.
**Work**: scrape RASFF mango notifications 2010–2025; build pesticide × destination × MRL table; train a small classifier on RASFF rejection patterns; integrate with a disease-classifier front-end.
**Publishability**: **no student paper exists on this**; even the academic literature is descriptive not prescriptive. **Highest-novelty angle.**
**Feasibility**: medium — RASFF scraping and MRL table assembly take ~3 weeks; the ML claim is modest but the application is genuinely new.

### Idea D — "Explainable On-Device Mango Disease Detection for Low-Resource Indian Smartphones"
**Claim**: a <1M-parameter mango disease classifier with Grad-CAM that runs in <500ms on a budget Android phone; user study with N=5–10 mango growers measures trust delta with vs. without explanations.
**Work**: distill DenseNet201 into a MobileNetV3-Small; deploy via TF-Lite; build a Streamlit/Gradio prototype; SUS-style usability study.
**Publishability**: combines GourNet efficiency angle with the IJH XAI usability angle. The user study is what makes it JEI-defensible as a hypothesis-driven study.
**Feasibility**: high if a small interview cohort is reachable; medium otherwise.

### Idea E — "The Mango Dashboard, Framed as a System Paper" (the project the student wants)
**Claim**: an integrated decision-support tool for Indian mango growers consisting of (i) variety recommendation, (ii) disease detection, (iii) yield estimate, (iv) MRL-aware pesticide lookup, (v) chatbot — with **one module designated as the focal research claim** and the rest described as supporting infrastructure.
**Work**: build the full dashboard; pick *one* module (recommended: Idea A or D as the focal module) and run the rigorous evaluation on it; for the other modules, report architecture and qualitative farmer feedback.
**Publishability**: follows the CropMates JSR template exactly. Lower novelty per-module, but the integration story + farmer feedback + one rigorous component is publishable at JSR HS.
**Feasibility**: high but only if scope is managed; the temptation is to do all 5 modules at half-depth, which is exactly the JEI rejection pattern ("invention description").

**Strongest single recommendation**: **combine Idea A (small original Indian dataset) + Idea D (efficient on-device + farmer trust study) into the focal module of Idea E (dashboard)**. This single combined arc clears JSR HS comfortably, has a real shot at JEI under the new rules because of the user-study hypothesis, and accumulates the artifact set (logbook, raw data, farmer feedback forms, code repo, deployed demo) that maps directly onto 11+ of the 15 CREST Gold criteria.

---

## Headline Findings

1. JEI's March-2026 rule change is the single most important thing to know — it disqualifies pure-CV-on-public-data projects.
2. JSR HS is the realistic target and has direct precedents for both the dashboard format and the ML methods.
3. The mango-leaf-disease accuracy leaderboard is saturated; the open angles are region-specific data, explainability + farmer trust, efficient on-device, and MRL-aware pesticide advice — the last being a near-empty student-research space.
4. The strongest single project shape is one original Indian dataset + one efficient model + one small farmer user study, packaged as the focal module of a multi-feature dashboard.

## Sources Consulted

JEI policy: https://emerginginvestigators.org/submissions/faq | CREST Gold criteria: https://www.crestawards.org/help-centre/gold-criteria-guidance/ | CREST AI policy: https://www.crestawards.org/help-centre/crest-guidelines-on-use-of-ai-for-students/ | Samay Jain JSR: https://www.jsr.org/hs/index.php/path/article/view/8470 | CropMates JSR: https://www.jsr.org/hs/index.php/path/article/view/2079 | JSR climate-zone yield: https://www.jsr.org/index.php/path/article/view/2644 | JSR drought Streamlit: https://www.jsr.org/hs/index.php/path/article/view/8737 | JSR plant size CEA: https://www.jsr.org/hs/index.php/path/article/view/3926 | MangoLeafBD dataset: https://data.mendeley.com/datasets/hxsnvwty3r/1 | GourNet: https://arxiv.org/abs/2604.27764 | Fine-tuned CNN mango: https://arxiv.org/abs/2510.05326 | South Indian mango CMC: https://www.techscience.com/cmc/v77n3/55036 | IJH Explainable mango: https://journal.iahs.org.in/index.php/ijh/article/view/2988 | ViX-MangoEFormer: https://www.mdpi.com/2073-431X/14/5/171 | Mango yield ANN PeerJ: https://peerj.com/articles/20013/ | Tamil Nadu mango climate SSRN: https://doi.org/10.2139/ssrn.4893902 | Mango price PLOS: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0283584 | Interpretable produce price arXiv: https://arxiv.org/pdf/1812.05173 | RASFF pesticide PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9324178/ | RASFF border rejections 2008–2023: https://www.mdpi.com/2071-1050/17/7/2923 | Ratnagiri Alphonso pesticide case: https://www.academia.edu/43980330
