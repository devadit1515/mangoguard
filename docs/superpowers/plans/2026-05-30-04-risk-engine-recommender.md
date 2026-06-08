# MangoGuard Plan 4: Disease-Risk Engine + Market-Conditioned MRL Recommender (FOCAL)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. **Prerequisites:** Plan 1 (`v0.1.0`) + Plan 2 (`v0.2.0`). Plan 3 helpful but not required.

**This is the focal research module.** Every claim in the CREST report Discussion is grounded in code from this plan. Maximum rigor expected.

**Goal:** Implement disease-risk engine (anthracnose HTR + powdery mildew threshold + hopper × CROPSAP), per-block-per-day Pest Pressure Index (PPI), market-conditioned MRL recommender filtering by destination market + CIB&RC + PHI + RASFF rejection history, plus retrospective + RASFF counterfactual evaluation harness.

**Architecture:** Three layers. (1) `risk/` — pure-function disease-risk models. (2) `recommend/` — MRL lookup, CIB&RC parser, RASFF analyzer, ranker. (3) `evaluation/` — retrospective backtest + RASFF counterfactual.

**Tech Stack:** `pandas`, `scikit-learn`, `numpy`, `pdfplumber`, `pyyaml`, `freezegun`.

---

## File Structure

```
src/mangoguard/risk/
├── __init__.py
├── anthracnose.py
├── powdery_mildew.py
├── hopper.py
├── ppi.py
└── calibration.py

src/mangoguard/recommend/
├── __init__.py
├── mrl_loader.py
├── cibrc.py
├── rasff.py
├── markets.py
├── ranker.py
└── recommend.py

src/mangoguard/evaluation/
├── __init__.py
├── retrospective.py
├── rasff_counterfactual.py
└── baseline_schedule.py

data/
├── mrl_tables/
│   ├── eu.yaml
│   ├── japan.yaml
│   └── fssai.yaml
├── cibrc_mango_registered.csv
├── rasff_mango_rejections.csv
├── baseline_schedules/
│   ├── icar_cish_mango_2023.yaml
│   └── kvk_konkan_alphonso_2025.yaml
└── pesticide_metadata.yaml

tests/risk/   tests/recommend/   tests/evaluation/
```

---

## Task 1: Anthracnose HTR model

**Model:** Akem 2006 logistic regression. `logit(P) = β0 + β1·HTR + β2·LW_hours + β3·sunshine_hrs + β4·wind`. HTR = RH_morning / (T_max − T_min).

**Files:** `src/mangoguard/risk/anthracnose.py` + `tests/risk/test_anthracnose.py`.

```python
# Default coefficients from Akem (2006) "Mango anthracnose disease..."
DEFAULT_COEFFS = {"beta_0": -4.2, "beta_htr": 0.085, "beta_lw": 0.32,
                  "beta_sun": -0.18, "beta_wind": -0.12}

@dataclass(frozen=True, slots=True)
class AnthracnoseInputs:
    t_air_c_morning: float
    t_max_c: float
    t_min_c: float
    rh_morning_pct: float
    leaf_wetness_hr: float
    wind_speed_ms: float
    sunshine_hr: float

def anthracnose_risk(inp: AnthracnoseInputs, coeffs: dict[str, float] | None = None) -> float:
    """P(infection event) in [0, 1]. Pure function."""
    coeffs = coeffs or DEFAULT_COEFFS
    htr = inp.rh_morning_pct / max(0.1, inp.t_max_c - inp.t_min_c)
    z = (coeffs["beta_0"]
         + coeffs["beta_htr"] * htr
         + coeffs["beta_lw"] * inp.leaf_wetness_hr
         + coeffs["beta_sun"] * inp.sunshine_hr
         + coeffs["beta_wind"] * inp.wind_speed_ms)
    return 1.0 / (1.0 + math.exp(-z))
```

- [ ] **Step 1: Write failing tests** — `test_returns_value_in_0_1`, `test_high_htr_long_wetness_yields_risk_above_0_7`, `test_low_htr_short_wetness_yields_risk_below_0_2`, `test_div_by_zero_edge_handled` (Tmax == Tmin), `test_pure_function_no_state`.
- [ ] **Step 2: Implement `anthracnose_risk`**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(risk): anthracnose HTR logistic regression (Akem 2006)`

---

## Task 2: Powdery mildew model

**Model:** Threshold + ICAR forewarning logistic regression. Risk peaks: `T_min ∈ [11, 14]` AND `T_max ∈ [17, 31]` AND `RH ∈ [64, 72]`. Smooth Gaussian roll-off outside optimal bands.

**Files:** `src/mangoguard/risk/powdery_mildew.py` + `tests/risk/test_powdery_mildew.py`.

- [ ] **Step 1: Write failing tests** — `test_optimal_conditions_yield_high_risk`, `test_too_hot_yields_low_risk`, `test_too_cold_yields_low_risk`, `test_too_dry_yields_low_risk`, `test_returns_in_0_1`.
- [ ] **Step 2: Implement `powdery_mildew_risk(t_max_c, t_min_c, rh_pct) -> float`** using Gaussian kernel per variable; product of three kernel values.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(risk): powdery mildew T-band × RH window model`

---

## Task 3: Mango hopper model

**Model:** `hopper_risk = cropsap_taluka_pressure × local_t_multiplier`. T multiplier triangular max at 27°C, zero below 18°C or above 36°C.

**Files:** `src/mangoguard/risk/hopper.py` + `tests/risk/test_hopper.py`.

- [ ] **Step 1: Write failing tests** — `test_high_cropsap_high_local_t_yields_high_risk`, `test_zero_cropsap_yields_zero_risk`, `test_extreme_cold_dampens_risk`.
- [ ] **Step 2: Implement `hopper_risk(cropsap_taluka_pressure, t_air_c) -> float`**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(risk): mango hopper CROPSAP × local-T model`

---

## Task 4: Pest Pressure Index combiner

**Formula:** `PPI = w_anth · score_anth + w_pm · score_pm + w_hop · score_hop`. Default weights `w_anth=0.5, w_pm=0.3, w_hop=0.2`.

**NDRE-anomaly boost:** if Sentinel-2 NDRE for block dropped >1 SD below 30-day mean → `score_anth += 0.15` (capped at 1.0).

**Files:** `src/mangoguard/risk/ppi.py` + `tests/risk/test_ppi.py`.

```python
DEFAULT_WEIGHTS = {"anth": 0.5, "pm": 0.3, "hop": 0.2}

def compute_ppi(
    store: FeedStore,
    block_id: str,
    day: date,
    weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """Return {'ppi': 0-100, 'anth': 0-1, 'pm': 0-1, 'hop': 0-1, 'ndre_anomaly': bool}.

    Aggregates observations in [day-7, day+1) window: mean T/RH/wind, sum precip,
    sum leaf_wetness, latest NDRE + 30-day mean for anomaly check.
    Multiplies final PPI by 100 to yield 0-100 score.
    """
```

- [ ] **Step 1: Write failing tests** — `test_ppi_returns_dict_with_expected_keys`, `test_ppi_in_0_100_range`, `test_weights_sum_check_warns_if_not_unity`, `test_handles_empty_observations_returns_low_ppi`, `test_ndre_anomaly_boosts_anthracnose_component`.
- [ ] **Step 2: Implement `compute_ppi`** reading from the FeedStore.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(risk): Pest Pressure Index combiner with NDRE-anomaly boost`

---

## Task 5: Weight calibration

**Files:** `src/mangoguard/risk/calibration.py` + `tests/risk/test_calibration.py`.

```python
def calibrate_weights(
    historical_obs: pd.DataFrame,    # weather + NDRE + CROPSAP per (block, week)
    outbreak_labels: pd.DataFrame,   # 0/1 per (taluka, week, pathogen)
) -> dict[str, float]:
    """Grid search w_anth, w_pm, w_hop ∈ [0, 1] with sum=1, maximize ROC-AUC."""
```

- [ ] **Step 1: Write failing tests** with synthetic data — `test_perfect_separable_data_yields_high_weight_on_relevant_component`, `test_returns_weights_summing_to_1`, `test_falls_back_to_defaults_if_insufficient_data`.
- [ ] **Step 2: Implement** coarse grid (step 0.1) then fine grid (step 0.01) near best.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(risk): PPI weight calibration via ROC-AUC grid search`

---

## Task 6: MRL tables loader

**Files:** `src/mangoguard/recommend/mrl_loader.py` + 3 YAML tables + `tests/recommend/test_mrl_loader.py`.

YAML schema per table:

```yaml
metadata:
  source: "EU Pesticide Database, accessed 2026-05-30"
  url: "https://ec.europa.eu/food/plant/pesticides/eu-pesticides-database"
  crop: "Mango"
limits:
  hexaconazole:
    mrl_mg_per_kg: 0.05
  imidacloprid:
    mrl_mg_per_kg: 0.05
  # ... ≥30 entries per table
```

- [ ] **Step 1: Seed YAML tables** from EU pesticide DB, Japan MHLW positive list, FSSAI MRL regulations. ≥30 entries per table, covering common Indian mango pesticides.
- [ ] **Step 2: Write failing tests** — `test_loads_eu_table_yields_expected_active_ingredients`, `test_lookup_returns_mrl_mg_per_kg`, `test_unknown_active_ingredient_returns_none`, `test_all_3_tables_share_common_format`.
- [ ] **Step 3: Implement `load_mrl_table(market: str) -> dict[str, float]` + `lookup_mrl(market, active_ingredient) -> float | None`**.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(recommend): MRL tables loader for EU, Japan, FSSAI`

---

## Task 7: CIB&RC registered-pesticide parser

**Files:** `src/mangoguard/recommend/cibrc.py` + `data/cibrc_mango_registered.csv` + `tests/recommend/test_cibrc.py`.

Columns: `active_ingredient, formulation, dose_per_liter_water, target_pest_class, phi_days, registration_status`. ≥40 entries.

- [ ] **Step 1:** Scrape / download the CIB&RC mango list, save as CSV.
- [ ] **Step 2: Write failing tests** — `test_loads_csv`, `test_filters_by_target_pest`, `test_phi_days_is_int`.
- [ ] **Step 3: Implement `CIBRCRegistry`** with `pesticides_for_pathogen(pathogen)`, `get_phi_days(active_ingredient)`.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(recommend): CIB&RC registered-pesticide registry`

---

## Task 8: RASFF analyzer

**Files:** `src/mangoguard/recommend/rasff.py` + `data/rasff_mango_rejections.csv` + `tests/recommend/test_rasff.py` + `scripts/pull_rasff.py`.

Scrape RASFF + FDA Import Refusals + Japan MHLW for mango pesticide-residue notifications 2010-2025. CSV columns: `date, source_country, destination, active_ingredient, mrl_mg_per_kg, detected_mg_per_kg, severity`.

Compute `rasff_rejection_probability(active_ingredient, destination)` from frequencies with Bayesian beta-prior smoothing for low-count entries.

- [ ] **Step 1:** Write `scripts/pull_rasff.py` (one-time data pull, not in CI).
- [ ] **Step 2: Write failing tests** — `test_loads_rasff_csv`, `test_rejection_probability_in_0_1`, `test_unknown_pesticide_returns_default_prior_below_0_1`, `test_high_historical_freq_yields_high_probability`.
- [ ] **Step 3: Implement `RASFFAnalyzer`**.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(recommend): RASFF historical rejection-probability analyzer`

---

## Task 9: Market segment enum

**Files:** `src/mangoguard/recommend/markets.py` + `tests/recommend/test_markets.py`.

```python
class MarketSegment(str, Enum):
    EXPORT_EU = "export_eu_japan_us"
    EXPORT_GULF = "export_gulf_me_seasia"
    DOMESTIC_RETAIL = "domestic_retail_processor"
    DOMESTIC_MANDI = "domestic_mandi"

MARKET_MRL_TABLE = {
    MarketSegment.EXPORT_EU: ["eu", "japan"],
    MarketSegment.EXPORT_GULF: ["codex"],
    MarketSegment.DOMESTIC_RETAIL: ["fssai", "buyer_specific"],
    MarketSegment.DOMESTIC_MANDI: ["fssai"],
}
```

- [ ] **Step 1: Write failing tests** — `test_enum_covers_4_segments`, `test_each_segment_has_at_least_one_mrl_table`.
- [ ] **Step 2: Implement enum + mapping.**
- [ ] **Step 3: Commit:** `feat(recommend): MarketSegment enum + segment-to-MRL mapping`

---

## Task 10: Pesticide metadata

**Files:** `data/pesticide_metadata.yaml` + integrate in `ranker.py`.

Schema per entry: `active_ingredient, residue_half_life_days, cost_per_acre_inr, efficacy_per_pathogen: {anthracnose: 0.85, powdery_mildew: 0.10, hopper: 0.05}`. ≥30 entries.

- [ ] **Step 1: Seed metadata YAML** from agronomy literature + commercial pesticide labels. Document source per entry.
- [ ] **Step 2: Write validation test** — every metadata entry is also in `cibrc_mango_registered.csv`.
- [ ] **Step 3: Commit:** `data(recommend): pesticide metadata YAML (half-life, cost, efficacy)`

---

## Task 11: Recommender ranker

**Files:** `src/mangoguard/recommend/ranker.py` + `tests/recommend/test_ranker.py`.

Per spec §4.3 Module 3c step 5: `log_score = log(efficacy + 1e-6) - log(half_life + 1) - log(cost + 1)`.

- [ ] **Step 1: Write failing tests** — `test_high_efficacy_short_halflife_low_cost_ranks_first`, `test_long_halflife_demotes_rank`, `test_high_cost_demotes_rank`.
- [ ] **Step 2: Implement `rank_candidates(candidates) -> list[Pesticide]`** sorted desc.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(recommend): pesticide ranker by efficacy / (half_life × cost)`

---

## Task 12: Top-level `recommend()`

**Files:** `src/mangoguard/recommend/recommend.py` + `tests/recommend/test_recommend.py`.

```python
@dataclass(frozen=True, slots=True)
class Recommendation:
    block_id: str
    date: date
    ppi: float
    primary_pathogen: str
    target_market: MarketSegment
    pesticide: str | None
    dose: str | None
    phi_days: int | None
    harvest_date_constraint: date | None
    expected_rasff_rejection_p: float | None
    alternatives: list[str]
    rationale: str

def recommend(
    store: FeedStore,
    block_id: str,
    day: date,
    target_market: MarketSegment,
    days_until_harvest: int,
) -> Recommendation:
    ...
```

Flow per spec §4.3.3c:
1. `compute_ppi`. If `<50`, return no-spray.
2. Identify primary pathogen (max component).
3. Pull effective pesticides from `CIBRCRegistry.pesticides_for_pathogen`.
4. Filter by MRL: exclude if `phi_days > days_until_harvest` OR ingredient absent from target market's MRL table.
5. For export markets: exclude if `rasff_rejection_probability > 0.20`.
6. Rank survivors.
7. Return top + 2-3 alternatives.

- [ ] **Step 1: Write failing tests** — `test_low_ppi_returns_no_spray`, `test_export_eu_filters_out_high_rasff_pesticides`, `test_phi_constraint_excludes_short_window_pesticides`, `test_returns_alternatives`, `test_no_compliant_pesticide_returns_explanatory_rationale`.
- [ ] **Step 2: Implement `recommend`**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(recommend): top-level market-conditioned recommender`

---

## Task 13: Baseline schedule parsers

**Files:** `src/mangoguard/evaluation/baseline_schedule.py` + 2 YAML baselines + `tests/evaluation/test_baseline_schedule.py`.

YAML schema:

```yaml
metadata:
  source: "ICAR-CISH Mango Production Technology 2023"
schedule:
  - phenology_stage: "flowering"
    iso_week_range: [10, 14]
    pesticide: "carbendazim 50 WP"
    dose: "1 g/L"
    target: "anthracnose"
  # ... full schedule
```

`get_baseline_recommendation(source, iso_week, pathogen) -> str | None`.

- [ ] **Step 1: Seed both YAMLs** from the published documents.
- [ ] **Step 2: Write failing tests** — `test_loads_icar_cish_yaml`, `test_returns_pesticide_for_known_week_pathogen`, `test_returns_none_outside_schedule_window`.
- [ ] **Step 3: Implement parser + lookup.**
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(evaluation): ICAR-CISH + KVK Konkan baseline schedule parsers`

---

## Task 14: Retrospective backtest

**Files:** `src/mangoguard/evaluation/retrospective.py` + `tests/evaluation/test_retrospective.py`.

Per spec §4.6.1: backtest PPI vs CROPSAP 2018-2024. Compare ROC-AUC, precision, recall, Brier score against (a) seasonal-mean baseline and (b) ICAR-CISH schedule baseline.

```python
def run_retrospective_backtest(
    historical_obs: pd.DataFrame,
    cropsap_outbreaks: pd.DataFrame,
) -> dict[str, float]:
    """Returns metrics for mangoguard, seasonal baseline, and ICAR-CISH baseline."""
```

- [ ] **Step 1: Write failing tests** with synthetic data — `test_returns_metric_dict`, `test_metrics_in_valid_ranges`, `test_includes_both_baselines`.
- [ ] **Step 2: Implement** using `sklearn.metrics.roc_auc_score`, `precision_recall_curve`, `brier_score_loss`.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(evaluation): retrospective backtest vs CROPSAP 2018-2024`

---

## Task 15: RASFF counterfactual

**Files:** `src/mangoguard/evaluation/rasff_counterfactual.py` + `tests/evaluation/test_rasff_counterfactual.py`.

Per spec §4.6.3: for each historical RASFF rejection, replay the recommender on that pathogen + destination + reconstructed disease pressure profile. Check if MangoGuard's recommendation would have avoided the violating ingredient.

```python
def evaluate_rasff_counterfactual(rasff_rejections: pd.DataFrame) -> dict[str, float]:
    """Returns {'prevention_rate_mangoguard', 'prevention_rate_icar_baseline',
              'relative_improvement_pct', ...}.
    Success threshold (spec §4.6.3): relative_improvement_pct >= 30."""
```

- [ ] **Step 1: Write failing tests** with synthetic RASFF data — `test_prevention_rate_in_0_1`, `test_mangoguard_outperforms_baseline_on_known_evasion_cases`, `test_returns_relative_improvement_field`.
- [ ] **Step 2: Implement**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(evaluation): RASFF counterfactual prevention-rate evaluator`

---

## Task 16: Integration test — full Module 3 stack

**Files:** `tests/test_module3_integration.py`.

Synthetic FeedStore with 30 days of weather + 4 Sentinel-2 NDRE samples + 1 CROPSAP outbreak. Run `compute_ppi` then `recommend` for all 4 `MarketSegment` values. Assert:
1. PPI is high (>50) on the outbreak week.
2. EU recommendation differs from MANDI recommendation.
3. Every recommended pesticide is CIB&RC-registered.
4. Every recommended pesticide passes the destination's MRL filter.

- [ ] **Step 1: Write the test.**
- [ ] **Step 2: Verify PASS.**
- [ ] **Step 3: Commit:** `test(module3): full integration — PPI -> recommender across all 4 market segments`

---

## Task 17: Calibration + evaluation notebooks

**Files:** `notebooks/02_anthracnose_htr_calibration.ipynb` + `notebooks/05_recommender_evaluation.ipynb`.

Spec §4.4 lists these notebooks as required deliverables. They document the actual experiments whose results feed the CREST report Section 4 (Results).

- [ ] **Step 1: Notebook 02** — load 2018-2024 retrospective weather + CROPSAP outbreaks, run `calibrate_weights` from Task 5, plot ROC curves comparing default vs calibrated weights, save fitted weights to `artifacts/ppi_weights.yaml`.
- [ ] **Step 2: Notebook 05** — load RASFF rejections, run `run_retrospective_backtest` (Task 14) + `evaluate_rasff_counterfactual` (Task 15), save metric tables as `artifacts/eval_metrics.json` + 5 figures to `artifacts/figs/` (PPI vs outbreak ROC, RASFF prevention rate bar chart, baseline-vs-MangoGuard comparison, per-pathogen confusion matrix, per-market segment breakdown).
- [ ] **Step 3: Commit:** `notebooks(evaluation): HTR calibration + recommender evaluation notebooks`

---

## Task 18: Bump version + tag

- [ ] Bump to `0.4.0`, commit, tag `v0.4.0`.

---

## Acceptance criteria for Plan 4 complete

- [ ] All 3 disease-risk modules unit-tested with edge cases.
- [ ] PPI combiner has weight-calibration path.
- [ ] MRL loader covers EU + Japan + FSSAI with ≥30 active ingredients each.
- [ ] CIB&RC registry has ≥40 mango-registered pesticides.
- [ ] RASFF analyzer covers ≥150 historical rejections.
- [ ] Pesticide metadata covers ≥30 active ingredients.
- [ ] Recommender returns differentiated outputs across the 4 market segments.
- [ ] Retrospective backtest reports metrics + both baselines.
- [ ] RASFF counterfactual achieves ≥30% relative improvement.
- [ ] Tagged `v0.4.0`.
