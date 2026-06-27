# AamRakshak — design doc (locked 2026-06-27)

> **AamRakshak** (आम रक्षक, "mango protector"): a sub-₹2,000 open-source leaf-wetness + microclimate sensor node that gives smallholder mango growers — **any variety, any humid growing region** — the anthracnose early-warning that today only a ₹40,000+ commercial agro-met station can provide.
>
> **Scope note (variety- and region-agnostic by design).** The target pathogen, anthracnose (*Colletotrichum gloeosporioides*), is the dominant pre/post-harvest disease across essentially all Indian mango varieties and humid regions — Alphonso (Konkan), Kesar (Gujarat), Dasheri/Langra (UP), Banganapalli/Totapuri (south), Himsagar (Bengal). The risk model keys on **microclimate, not cultivar** (leaf wetness + humid-thermal ratio describe the *fungus's* needs), and the hardware measures microclimate, so both generalize by construction. Cultivar is handled as a documented per-variety susceptibility multiplier, not a hard assumption. Konkan Alphonso is the **primary validation testbed** (worst-case humidity); generalization is demonstrated on a second, contrasting regional climate (§7).
>
> This is the locked design for the flagship CREST Gold *sample* build (see `README.md`). It supersedes the archived "MangoGuard" interoperability project (`useless stuff/`). Internal working doc — the anti-AI-writing rules in `AI Writing.md` apply to the *report*, not to this file.

---

## 1. The one-line thesis

The previous project's own evaluation proved that **a single signal — leaf wetness — is the difference between a disease predictor that works (ROC-AUC ≈ 0.78) and one that is no better than a coin toss (≈ 0.48)**. It then assumed the grower already owns the expensive commercial station that measures it. Almost no smallholder does. AamRakshak builds that signal for ₹2,000 of hobbyist parts, so the prediction skill is available to the **millions of Indian mango growers — across varieties and regions —** who spray on a fixed calendar today.

## 2. Research question and success conditions

**Focal research question (specific, measurable, falsifiable):**

> Can a sub-₹2,000 open-source leaf-wetness and microclimate sensor node predict mango-anthracnose infection-risk periods accurately enough (ROC-AUC ≥ 0.75) to safely cut calendar fungicide sprays for smallholder Indian mango growers — recovering disease-prediction skill that currently requires a commercial agro-meteorological station costing 20× more, and generalising across growing regions rather than over-fitting one?

**I will have achieved my aim if:**

- **S1 — the leaf-wetness signal is decisive.** A risk model fed the node's measured leaf-wetness + local microclimate achieves materially higher discrimination (ROC-AUC) than the same model fed only free district weather feeds that lack leaf wetness. Target: node ≥ 0.75; free-feed gap ≥ 0.10 AUC.
- **S2 — the cheap node nearly matches the expensive station.** The ₹2,000 node lands within ~0.05 AUC of a simulated clean commercial reference station, i.e. ≥ 90% of the achievable skill at ~5% of the cost.
- **S3 — the DIY leaf-wetness sensor is trustworthy.** The interdigitated resistive sensor classifies surface wet/dry against a reference at ≥ 90% accuracy on the bench, after calibration.
- **S4 — fewer sprays, no missed windows.** In a season simulation, an early-warning spray rule cuts total fungicide applications by ≥ 30% versus the fixed ICAR-CISH calendar **while still covering ≥ 90% of true high-infection windows**. (This is the broad-applicability payoff: it helps the 96% domestic majority, not a <4% export niche.)
- **S5 — it generalises across regions and varieties.** The node-tier model holds its discrimination on *each* growing region (within-region ROC-AUC ≥ 0.75 on both the humid coastal and the drier inland region, the two regions agreeing within ≤ 0.05 AUC), and cultivar differences are absorbed by a documented per-variety susceptibility multiplier rather than retraining — evidence the device is not Konkan-Alphonso-locked. (Note: the *pooled* multi-region AUC runs higher than either within-region AUC because two base rates are easier to separate; the honest generalisation test is within-region.)

S1–S5 are all testable from this project's own code and bench data inside the window. There are no deferred-to-future-season headline claims; the only honest limitation kept as future work is a multi-season real-orchard deployment (§7).

## 3. Why it matters (wider purpose, broad population)

- Mango is India's largest fruit crop (~20 Mt/yr; National Horticulture Board) and India is the world's largest producer, grown across more than a dozen major varieties and a dozen states. Anthracnose (*Colletotrichum gloeosporioides*) is the dominant pre/post-harvest disease wherever humidity is high during fruit development — i.e. across nearly all of those regions — and a leading cause of fruit loss.
- Growers overwhelmingly spray on a **fixed calendar**, not on conditions. Calendar spraying over-applies on dry, low-risk weeks and can still miss a humid infection window. The cost lands on three groups at once: the grower (input bill + wasted labour), the farm worker (avoidable chemical exposure), and the consumer (dietary residue).
- The fix that agronomy already knows — weather-driven infection-risk forecasting — needs leaf-wetness data the smallholder cannot afford to measure. **That affordability gap, not the science, is the unsolved problem.** AamRakshak closes it. Because the device and model are variety- and region-agnostic, the adopter is any of the **millions of Indian mango smallholders**, directly or via a Farmer Producer Organisation field officer who can build and place a handful of nodes across member farms.

## 4. Approaches considered (feeds criterion 1.3)

**Project-level approach — how to deliver disease early warning:**

| Approach | Positives | Negatives |
|---|---|---|
| A. Fixed calendar (status quo) | Zero tech; what growers do now | Ignores weather; over-sprays and still misses windows. Not a contribution. |
| B. Free-feed software only (IMD district forecast → risk model) | No hardware; deploys instantly | Lacks leaf wetness + local microclimate; district forecasts are spatially coarse. The old project showed this sits near chance. |
| C. Commercial station + software | Best data quality | ₹40k+; out of reach for smallholders; only helps the ~1% who own one. |
| **D. DIY low-cost node + edge risk model (chosen)** | Supplies the decisive leaf-wetness signal for ~₹2k; works offline; buildable by a student; broad reach | Sensor calibration + corrosion + power are real engineering problems to solve (which is the design-and-make evidence). |

**Hardware-level approach — how to sense leaf wetness cheaply:**

| Sensor route | Positives | Negatives |
|---|---|---|
| Commercial leaf-wetness sensor (e.g. dielectric) | Accurate, calibrated | ₹8,000–15,000; defeats the cost goal |
| Capacitive DIY grid | No DC corrosion; robust | Needs an oscillator/timing circuit; harder for a first build |
| **Resistive interdigitated grid (chosen)** | ₹100; trivial ADC read; intuitive physics (surface water lowers resistance) | DC corrosion/drift over weeks → mitigated with low-duty AC-ish excitation + recalibration, and an honest limitation + capacitive upgrade path |

The chosen pair (D + resistive grid) is the cheapest route that still delivers the signal, and its weaknesses are exactly the documented problems (criterion 4.4) and creative mitigations (4.3).

## 5. Hardware specification

**Function:** sample air T/RH, canopy/soil temperature, and **leaf-surface wetness** at the canopy; integrate leaf-wetness duration; compute the Akem humid-thermal-ratio infection probability **on-device**; show RISK: HIGH / WATCH / LOW on the OLED (works with no phone/data); log to flash and optionally POST JSON over WiFi to the dashboard. Deep-sleep between samples for solar/battery field life.

**Bill of materials (indicative India prices, 2026; full BOM in the build guide):**

| Component | Spec | Why | ~₹ |
|---|---|---|---|
| ESP32 DevKit V1 | WiFi/BLE MCU, ADC, deep-sleep | Brains + edge compute + comms, all in one | 400 |
| SHT31 (or AHT20) | I²C digital T/RH, ±2% RH | HTR needs accurate RH; digital beats DHT11 noise | 250 |
| Resistive leaf-wetness grid | interdigitated FR4 / repurposed board | **the decisive signal** | 100 |
| DS18B20 (waterproof) | 1-Wire temp probe | canopy/soil temp; diurnal range | 130 |
| SSD1306 OLED | 0.96" I²C | offline local risk readout (no connectivity needed) | 160 |
| TP4056 + 18650 + holder | Li-ion charge + cell | field power | 220 |
| 6V 1W solar panel | small PV | recharge in-field | 180 |
| IP65 enclosure + DIY radiation shield | stacked plates | weatherproofing + shade for honest air-temp | 300 |
| Perfboard, wires, resistors, headers | — | assembly | 160 |
| **Total (field-ready)** | | | **≈ 1,900** |

A "core bench build" (no solar/enclosure, USB-powered) is ≈ ₹1,300. Headline comparison: **≈ ₹2,000 vs ₹40,000+** commercial station. Assembly target **≤ 8 h** (soldering 1.5 h, breadboard + per-sensor test 2 h, flash + leaf-wetness calibration 1.5 h, enclosure + radiation shield 1.5 h, field power + end-to-end test 1.5 h).

**Firmware (ESP32 Arduino C++):** read SHT31 (I²C) + DS18B20 (1-Wire) + leaf-wetness (ADC, with brief alternating-polarity excitation to limit electrolysis), maintain a rolling leaf-wetness-duration counter and a morning-RH / diurnal-range tracker, evaluate the Akem logistic in fixed-point-safe float, drive the OLED, append to flash log, optional WiFi POST, then deep-sleep. Error handling: sensor-read retries, NaN guards, HTR denominator clamp, safe defaults on missing reads.

## 6. Software architecture

Clean rebuild as package `aamrakshak` (old `mangoguard` archived). Everything downstream of a reading is source-agnostic: a node POST, a logged CSV, or a simulated season all become the same `Reading` record.

```
src/aamrakshak/
  riskengine/  anthracnose.py (Akem HTR logistic) · leafwetness.py (LW estimation + sensor model) · ppi.py (index + spray decision)
  sim/         weather.py (grounded Konkan generator, seeded) · outbreaks.py (INDEPENDENT label generator) · sensors.py (tier noise models)
  eval/        metrics.py · tier_study.py · leafwet_validation.py · spray_reduction.py
  io/          ingest.py (node JSON/CSV → Reading)
scripts/  run_evaluation.py (→ artifacts/eval_metrics.json) · make_figures.py (→ artifacts/figs/)
firmware/ aamrakshak_node/aamrakshak_node.ino
app/      streamlit_app.py
tests/    riskengine, sim, eval, io
docs/     DESIGN.md · report/ · hardware/HARDWARE_BUILD_GUIDE.md
```

**The science (criterion 4.1 anchors), all derived in the report:**
- Akem (2006) HTR logistic regression: HTR = morning RH / (T_max − T_min) (denominator clamped to 0.1 on saturated days); P(infection) = σ(β₀ + β_htr·HTR + β_lw·LW + β_sun·S + β_wind·W). Coefficients from the paper; signs encode the biology.
- Leaf-wetness sensor physics: surface water film bridges interdigitated electrodes → conductance rises → ADC voltage divider response; calibration maps ADC → wet/dry; corrosion drift and the AC-excitation mitigation.
- ROC-AUC (rank skill) + Brier score (calibration) + confusion matrix; why both AUC and Brier are reported.

## 7. Evaluation plan (all regenerable: code → JSON → figures)

Honesty rules (brief §6): every number is a real output of `run_evaluation.py`; weather + outbreak labels are **simulated from documented Konkan climate normals and the published Akem relationship**, clearly labelled simulated; the leaf-wetness sensor validation uses a **bench dataset** (emulated where a physical wet/dry reference is stated honestly); fixed seed; train/val/test where a model is fit; confusion-matrix cells sum to n.

1. **Sensor-tier discrimination study (S1, S2).** Same simulated seasons, four data tiers — (A) calendar, (B) free district feed *without* leaf wetness + spatial smoothing, (C) AamRakshak node (local T/RH + measured leaf wetness, node-grade noise), (D) clean commercial station. Report ROC-AUC + Brier per tier, averaged over N noise seeds. Outbreak labels come from an **independent** generator (different coefficients + Bernoulli noise) so the test cannot be circular.
   - **Regional generalisation (S5).** Run the tiers on ≥2 contrasting regional climates — a humid coastal profile (Konkan/Alphonso, the primary testbed) and a drier inland profile (e.g. Gujarat/Kesar) — and check the node tier holds ROC-AUC ≥ 0.75 on both. Apply a per-variety susceptibility multiplier and confirm it shifts the spray threshold sensibly without retraining.
2. **Leaf-wetness sensor validation (S3).** Bench wet/dry trials → ADC → calibrated classifier; confusion matrix + accuracy/precision/recall; honest corrosion-drift note.
3. **Spray-reduction analysis (S4).** Encode the ICAR-CISH fixed calendar vs an early-warning rule (spray when risk sustained above threshold + min-interval lockout). Report sprays/season for each, % sprays cut, and % of true high-infection windows still covered.
4. **Calibration + ablation.** Reliability curve for the node tier; leave-one-feature-out to show leaf wetness is the load-bearing feature (quantifies the §1 thesis).

## 8. CREST 15-criteria coverage (target: all 15 at "excellent")

| # | Where it lands |
|---|---|
| 1.1 aim+objectives | §2 RQ + S1–S4 measurable conditions |
| 1.2 wider purpose | §3 broad smallholder population + farmer/consumer harm + NHB stat |
| 1.3 approaches | §4 two comparison tables (project + sensor) |
| 1.4 plan+rationale | build sequence + contract-first rationale |
| 1.5 time plan | Gantt planned vs actual + ≥1 documented deviation |
| 2.1 materials/people | the BOM itself + datasets + tools, each with alternative considered |
| 2.2 background | synthesised lit review, 15–25 real refs, ≥70% primary |
| 3.1 conclusions | S1–S4 answered with numbers + what they do NOT prove |
| 3.2 method→result | tier/feature choices traced to AUC outcomes + counterfactuals |
| 3.3 reflection | 5-part honest reflection |
| 4.1 science | Akem derivation, sensor physics, ROC-AUC/Brier — the maths is the evidence |
| 4.2 ethics+safety | hardware electrical/battery/weather safety + data/responsible-AI + risk table |
| 4.3 creativity | named: the ₹2k sensor that recovers a ₹40k station's signal; offline edge risk |
| 4.4 problems | leaf-wetness corrosion, ADC noise, calibration, monsoon power, sim-honesty — ≥3 full arcs |
| 4.5 communication | abbreviations on first use, 6–10 captioned figures, ≥3 tables, glossary, audience line |

## 9. Build sequence (TDD; commit+push after each)

1. Data generator (weather + independent outbreaks) + tests.
2. Risk engine (port Akem/anthracnose + leaf-wetness + PPI/spray decision) + tests.
3. Sensor-tier noise models + eval pipeline → `eval_metrics.json` + tests.
4. Firmware (ESP32) + on-device model parity check against Python.
5. Streamlit dashboard (node ingest → risk/history/decision).
6. Figures from JSON.
7. Hardware build guide.
8. CREST report (human voice per `AI Writing.md`).
9. Student Profile form + dated logbook.
10. Self-critique ≥2 passes + verification gate.

*End of design doc.*
