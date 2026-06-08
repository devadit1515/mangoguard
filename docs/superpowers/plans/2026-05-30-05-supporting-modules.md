# MangoGuard Plan 5: Supporting Modules — Disease Detector, Orchard-Health Dashboard, Yield/Price, AskHapus Chatbot

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. **Prerequisites:** Plan 1 (`v0.1.0`) + Plan 2 (`v0.2.0`). Can run in parallel with Plan 4.

**Goal:** Implement the four non-focal modules — **M1** disease detector (MobileNetV3-Small + Grad-CAM), **M2** orchard-health dashboard data layer (Sentinel-2 NDVI/NDRE/NDMI queries), **M4** XGBoost yield + price estimators, **M5** AskHapus RAG chatbot.

**Architecture:** Each module is independently testable Python. M1 trains via notebook and exposes `predict_image()`. M2 is a thin query layer over `FeedStore`. M4 trains via notebook and exposes `predict_*()`. M5 ingests PDFs to ChromaDB and exposes `query()`.

**Tech Stack:** PyTorch 2.x + torchvision (M1), `pytorch-grad-cam` (M1), XGBoost + SHAP + pandas (M4), LangChain + ChromaDB + Gemini 1.5 Flash (M5).

**Scope discipline (per spec §1.2 O5 amendment):** M5 (chatbot) is the first to descope if Plans 1-4 slip — highest engineering surface for least research credit.

---

## File Structure

```
src/mangoguard/disease_detector/
├── __init__.py
├── data.py            # MangoLeafBD + Alphonso Visit-1 loaders
├── model.py           # MobileNetV3-Small + custom head
├── train.py           # two-phase fine-tuning
├── infer.py           # single-image inference + Grad-CAM
└── gradcam.py         # Grad-CAM++ implementation with fallback

src/mangoguard/orchard_health/
├── __init__.py
├── queries.py         # block-level NDVI/NDRE/NDMI time-series + anomaly detection
└── trend.py           # seasonal NDVI integral + cross-season trend

src/mangoguard/yield_price/
├── __init__.py
├── features.py
├── yield_xgb.py
├── price_xgb.py
└── shap_explain.py

src/mangoguard/chatbot/
├── __init__.py
├── ingest.py
├── rag.py
└── corpus.py

data/
├── chatbot_corpus/MANIFEST.yaml
├── alphonso_visit1/   # (.gitignore'd; 300-500 photos from Visit 1)
└── chatbot_acceptance_questions.yaml

notebooks/
├── 03_disease_detector_training.ipynb
└── 04_yield_price_model.ipynb

artifacts/
├── mango_classifier_mobilenetv3_v1.pth
├── yield_xgb_v1.json
└── price_xgb_v1.json

tests/disease_detector/   tests/orchard_health/   tests/yield_price/   tests/chatbot/
```

---

## Task 1: MangoLeafBD dataset loader

**Files:** `src/mangoguard/disease_detector/data.py` + `tests/disease_detector/test_data.py` + `scripts/pull_mangoleafbd.py`.

MangoLeafBD: 4000 images, 8 classes (Anthracnose, Bacterial Canker, Cutting Weevil, Die Back, Gall Midge, Healthy, Powdery Mildew, Sooty Mould). Download once to `data/mangoleafbd/`; loader returns `torchvision.datasets.ImageFolder`-compatible 80/10/10 stratified split.

- [ ] **Step 1:** Write `scripts/pull_mangoleafbd.py` to fetch from Mendeley DOI `10.17632/hxsnvwty3r.1`.
- [ ] **Step 2: Write failing tests** — `test_loader_returns_8_classes`, `test_stratified_split_preserves_class_proportions`, `test_returns_torchvision_datasets`.
- [ ] **Step 3: Implement loader** with `torchvision.transforms` (resize 224, ImageNet normalize, training augmentation: random horizontal flip, ±15° rotation, 10% zoom).
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(disease_detector): MangoLeafBD loader + stratified split`

---

## Task 2: Alphonso Visit-1 dataset loader

**Files:** Extend `data.py` + `tests/disease_detector/test_alphonso_dataset.py`.

300-500 photos from Visit 1 organized: `data/alphonso_visit1/{anthracnose,powdery_mildew,hopper,sooty_mould,healthy}/img_NNN.jpg`. 80/20 train/test. **This is the original-data artifact central to CREST 4.3 (creativity).**

- [ ] **Step 1: Write failing tests** — `test_loader_handles_5_classes`, `test_skips_corrupt_images_with_warning`, `test_split_is_deterministic_with_seed`.
- [ ] **Step 2: Extend `data.py`** with `load_alphonso_visit1(root: Path, seed: int = 42) -> tuple[Dataset, Dataset]`.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(disease_detector): Alphonso Visit-1 dataset loader (original data)`

---

## Task 3: MobileNetV3-Small architecture

**Files:** `src/mangoguard/disease_detector/model.py` + `tests/disease_detector/test_model.py`.

Backbone: `torchvision.models.mobilenet_v3_small(weights="IMAGENET1K_V1")`. Custom head: `nn.Sequential(AdaptiveAvgPool2d(1), Flatten, Linear(576, 256), ReLU, Dropout(0.5), Linear(256, n_classes))`.

`build_model(n_classes: int, freeze_backbone: bool = True) -> nn.Module`.

- [ ] **Step 1: Write failing tests** — `test_model_accepts_224x224_input`, `test_output_shape_matches_n_classes`, `test_freeze_backbone_locks_base_params`.
- [ ] **Step 2: Implement.**
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(disease_detector): MobileNetV3-Small + custom head`

---

## Task 4: Two-phase fine-tuning trainer

**Files:** `src/mangoguard/disease_detector/train.py` + `notebooks/03_disease_detector_training.ipynb` + `tests/disease_detector/test_training_smoke.py`.

**Phase 1:** backbone frozen, Adam `lr=1e-3`, 5 epochs.
**Phase 2:** full unfreeze, Adam `lr=1e-5`, 15 epochs, early-stop patience 5.
**Loss:** `nn.CrossEntropyLoss(weight=class_weights)` via `sklearn.utils.class_weight.compute_class_weight`.
**Checkpoint:** save best val accuracy to `artifacts/mango_classifier_mobilenetv3_v1.pth`.

Two stages: A. train on MangoLeafBD (8 classes). B. fine-tune on Visit-1 Alphonso (5 classes, mapped). Document class-mapping table in comments.

- [ ] **Step 1: Implement `train_phase1`, `train_phase2`, `train_full_pipeline`** with epoch / patience / checkpoint params.
- [ ] **Step 2: Create the Colab notebook** that loads MangoLeafBD, runs both phases, evaluates on test set, saves checkpoint + `metrics.json`.
- [ ] **Step 3: Write smoke test** running 1 epoch on 20 random-tensor "images"; assert loss decreases.
- [ ] **Step 4: Verify smoke test passes.**
- [ ] **Step 5: Commit:** `feat(disease_detector): two-phase fine-tuning trainer + Colab notebook`

---

## Task 5: Grad-CAM++ heatmap

**Files:** `src/mangoguard/disease_detector/gradcam.py` + `tests/disease_detector/test_gradcam.py`.

Primary: `pytorch-grad-cam`. Fallback: hand-rolled using `torch.autograd.grad` on last conv layer if library import fails or version conflict.

`generate_heatmap(model, image_tensor) -> np.ndarray` returns `(H, W, 3)` uint8 overlay.

- [ ] **Step 1: Write failing tests** — `test_heatmap_shape_matches_input_image`, `test_heatmap_values_in_0_1`, `test_fallback_used_when_library_unavailable` (monkeypatch import).
- [ ] **Step 2: Implement primary + fallback paths.**
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(disease_detector): Grad-CAM++ heatmap with hand-rolled fallback`

---

## Task 6: Inference module

**Files:** `src/mangoguard/disease_detector/infer.py` + `tests/disease_detector/test_infer.py`.

```python
@dataclass(frozen=True, slots=True)
class DiseasePrediction:
    class_name: str
    confidence: float
    class_probabilities: dict[str, float]
    heatmap_overlay: np.ndarray

def predict_image(
    image_path: Path,
    model_path: Path = Path("artifacts/mango_classifier_mobilenetv3_v1.pth"),
) -> DiseasePrediction:
    """Single-image inference + Grad-CAM. Used by Streamlit dashboard."""
```

- [ ] **Step 1: Write failing tests** — `test_predict_image_returns_expected_class_for_known_anthracnose_sample`, `test_confidence_in_0_1`, `test_low_confidence_below_0_8_triggers_warning_flag`.
- [ ] **Step 2: Implement `predict_image`**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(disease_detector): single-image inference with Grad-CAM`

---

## Task 7: Orchard-health queries

**Files:** `src/mangoguard/orchard_health/queries.py` + `tests/orchard_health/test_queries.py`.

```python
def block_ndvi_timeseries(store: FeedStore, block_id: str, days_back: int = 90) -> pd.DataFrame:
    """Returns DataFrame[ts, ndvi, ndre, ndmi], oldest first."""

def block_anomalies(store: FeedStore, block_id: str) -> list[dict]:
    """Returns list of {ts, index, deviation_sd, ...} for points >1 SD below 30-day rolling mean."""
```

- [ ] **Step 1: Write failing tests** — `test_timeseries_sorted_oldest_first`, `test_handles_block_with_no_data`, `test_anomaly_detector_flags_known_drop`.
- [ ] **Step 2: Implement.**
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(orchard_health): NDVI/NDRE/NDMI queries + anomaly detection`

---

## Task 8: Seasonal trend + cross-season aggregation

**Files:** `src/mangoguard/orchard_health/trend.py` + `tests/orchard_health/test_trend.py`.

```python
def season_ndvi_integral(store: FeedStore, block_id: str, year: int) -> float:
    """Sum NDVI April 1 - June 30 (Alphonso growing season). Used by yield model."""

def cross_season_trend(store: FeedStore, block_id: str, years: list[int]) -> pd.DataFrame:
    """One row per year: [year, ndvi_integral, mean_ndre, peak_ndmi_drop_days]."""
```

- [ ] **Step 1: Write failing tests** — `test_ndvi_integral_returns_finite_positive`, `test_cross_season_yields_one_row_per_year`.
- [ ] **Step 2: Implement.**
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(orchard_health): seasonal NDVI integral + cross-season trend`

---

## Task 9: Yield/price feature engineering

**Files:** `src/mangoguard/yield_price/features.py` + `tests/yield_price/test_features.py`.

`build_features(store, block_id, season_year, block_meta) -> dict` returns:
- `acreage, tree_count, mean_tree_age` (block_meta)
- `ndvi_integral_apr_jun` (orchard_health.trend)
- `cum_gdd_above_10c`, `total_rainfall_mm`, `mean_rh_pct` (weather aggregation)
- `soil_texture_class`, `soil_ph` (block_meta from SoilGrids cache)
- `prev_season_yield_kg_per_acre` (optional)

- [ ] **Step 1: Write failing tests** — `test_features_dict_has_all_required_keys`, `test_ndvi_integral_uses_apr_jun_window`, `test_handles_missing_prev_season_yield`.
- [ ] **Step 2: Implement.**
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(yield_price): feature engineering for yield + price models`

---

## Task 10: Yield XGBoost

**Files:** `src/mangoguard/yield_price/yield_xgb.py` + notebook section + `tests/yield_price/test_yield_xgb.py`.

Target: `yield_kg_per_acre`. Baseline: seasonal mean. Spec O5 success: ≥15% MAE improvement.

- [ ] **Step 1: Implement `train_yield_model(X, y) -> xgb.XGBRegressor` + `predict_yield(features: dict) -> float`**.
- [ ] **Step 2: Write failing tests** — `test_model_beats_seasonal_mean_on_synthetic_separable_data`, `test_predict_yield_returns_float`, `test_loads_saved_model`.
- [ ] **Step 3: Add notebook section** that fits on real data, computes MAE, saves to `artifacts/yield_xgb_v1.json`.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(yield_price): XGBoost yield model + Colab notebook`

---

## Task 11: Mandi-price XGBoost

**Files:** `src/mangoguard/yield_price/price_xgb.py` + `tests/yield_price/test_price_xgb.py`.

Target: `mandi_modal_price_inr_per_quintal` at harvest week. Features: ISO week, mandi one-hot, 4-week-lag prices, 4-week-lag arrivals, weather aggregates. Train on AGMARKNET 2001-2025. Spec O5 success: ≥15% MAE improvement vs seasonal-mean baseline.

- [ ] **Step 1: Implement `train_price_model(X, y) -> xgb.XGBRegressor` + `predict_price(mandi, harvest_week, features) -> float`**.
- [ ] **Step 2: Write failing tests** — `test_beats_seasonal_mean_on_synthetic`, `test_handles_unknown_mandi_falls_back_to_avg`, `test_predict_returns_positive_float`.
- [ ] **Step 3: Add notebook section** that fits on AGMARKNET, computes MAE, saves model.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(yield_price): XGBoost mandi-price model on AGMARKNET 2001-2025`

---

## Task 12: SHAP explainability

**Files:** `src/mangoguard/yield_price/shap_explain.py` + `tests/yield_price/test_shap_explain.py`.

```python
def explain_prediction(model, features: dict) -> dict[str, float]:
    """{feature_name: shap_value} for one prediction."""

def top_n_features(model, X_train: pd.DataFrame, n: int = 5) -> list[tuple[str, float]]:
    """Global top-N by mean(|shap|)."""
```

- [ ] **Step 1: Write failing tests** — `test_explain_returns_dict_with_feature_keys`, `test_shap_values_sum_close_to_prediction_minus_baseline`, `test_top_n_returns_n_items`.
- [ ] **Step 2: Implement using `shap.TreeExplainer`**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(yield_price): SHAP explainability wrapper`

---

## Task 13: Chatbot corpus manifest

**Files:** `src/mangoguard/chatbot/corpus.py` + `data/chatbot_corpus/MANIFEST.yaml` + `tests/chatbot/test_corpus.py` + `scripts/pull_chatbot_corpus.py`.

`MANIFEST.yaml` lists every PDF: filename, source URL, publication date, license, language (en/mr/hi), topic tags. ≥50 PDFs covering ICAR-CISH IPM bulletins, KVK Konkan pamphlets, DBSKKV Dapoli guides, NHB handbook, FAO production manual.

- [ ] **Step 1: Seed `MANIFEST.yaml`** with ≥50 entries.
- [ ] **Step 2: Write failing tests** — `test_manifest_yaml_loads`, `test_every_entry_has_required_fields`, `test_at_least_5_marathi_sources_present`.
- [ ] **Step 3: Implement `load_manifest() -> list[CorpusDoc]`** with pydantic validation.
- [ ] **Step 4: Verify tests pass.**
- [ ] **Step 5: Commit:** `feat(chatbot): corpus manifest with ≥50 PDFs`

---

## Task 14: PDF ingest pipeline

**Files:** `src/mangoguard/chatbot/ingest.py` + `tests/chatbot/test_ingest.py`.

Pipeline:
1. `pdfplumber` text extraction; `pytesseract` fallback when text missing (scanned PDFs).
2. Chunk: 1000 tokens, 200-token overlap.
3. Embed: Gemini `text-embedding-004` if `GEMINI_API_KEY` set, else local `nomic-embed-text` via Ollama (`http://localhost:11434`).
4. Upsert to ChromaDB collection `mango_agronomy` at `data/chroma/`.

- [ ] **Step 1: Write failing tests** with a tiny fixture PDF (mock embedder) — `test_extracts_text_from_pdf`, `test_falls_back_to_ocr_when_text_missing`, `test_chunks_with_overlap`, `test_upserts_to_chroma_collection_count_increases`.
- [ ] **Step 2: Implement `ingest_pdf(path, collection)` and `ingest_corpus(manifest_path)`**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Commit:** `feat(chatbot): PDF ingest + chunk + embed -> ChromaDB pipeline`

---

## Task 15: RAG query with citations

**Files:** `src/mangoguard/chatbot/rag.py` + `tests/chatbot/test_rag.py`.

```python
@dataclass(frozen=True, slots=True)
class ChatbotResponse:
    answer: str
    citations: list[dict]    # [{"pdf": str, "page": int, "snippet": str}, ...]
    language: str            # "en" / "mr" / "hi"

def query(
    question: str,
    collection: chromadb.Collection,
    k: int = 5,
    target_language: str = "en",
) -> ChatbotResponse:
    """Retrieve k chunks; ask Gemini 1.5 Flash with system prompt requiring citations.
    Fall back to local Llama-3-8B (Ollama) if Gemini unavailable."""
```

System prompt enforces: answer ONLY from provided context; cite source PDF + page for every factual claim; refuse to answer outside retrieved context; output language matches `target_language`.

- [ ] **Step 1: Write failing tests** with mocked Gemini — `test_answer_includes_citations_for_factual_claims`, `test_refuses_to_answer_without_context`, `test_marathi_target_language_produces_marathi_answer`, `test_falls_back_to_ollama_when_gemini_unavailable`.
- [ ] **Step 2: Implement `query`**.
- [ ] **Step 3: Verify tests pass.**
- [ ] **Step 4: Add integration test** `@pytest.mark.integration_llm` against real Gemini + ingested ChromaDB.
- [ ] **Step 5: Commit:** `feat(chatbot): RAG query with citation-enforced Gemini + Ollama fallback`

---

## Task 16: 20-question acceptance test

**Files:** `tests/chatbot/test_chatbot_acceptance.py` + `data/chatbot_acceptance_questions.yaml`.

Per spec O5 success metric: chatbot answers 20 pre-defined Alphonso agronomy questions with source citations. Seed 20 questions (5 Marathi, 5 Hindi, 10 English) covering anthracnose, powdery mildew, fruit fly, harvest timing, MRL, post-harvest, irrigation, pruning.

Test asserts per question: response has ≥1 citation; citation points to a real PDF in the manifest; response language matches question language.

- [ ] **Step 1: Seed the 20-question YAML.**
- [ ] **Step 2: Write the acceptance test** marked `@pytest.mark.integration_llm`.
- [ ] **Step 3: Verify it passes once corpus is ingested.**
- [ ] **Step 4: Commit:** `test(chatbot): 20-question acceptance suite per spec O5`

---

## Task 17: Bump version + tag

- [ ] Bump to `0.5.0`, commit, tag `v0.5.0`.

---

## Acceptance criteria for Plan 5 complete

- [ ] Disease detector: MangoLeafBD + Alphonso Visit-1 loaders, MobileNetV3-Small architecture, two-phase trainer, Grad-CAM++ explanation, inference module. Trained checkpoint saved.
- [ ] Orchard-health: NDVI/NDRE/NDMI queries + anomaly + seasonal integral + cross-season trend.
- [ ] Yield/price: features, XGBoost yield + price, SHAP. Both beat seasonal-mean baseline by ≥15% MAE.
- [ ] Chatbot: manifest with ≥50 PDFs, ingest pipeline, RAG query with citations, 20-question acceptance test passes.
- [ ] Tagged `v0.5.0`.
