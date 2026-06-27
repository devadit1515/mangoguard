# AamRakshak — project run guide

Low-cost leaf-wetness early-warning for mango anthracnose. A sub-₹2,000 ESP32
sensor node + a Python risk/evaluation pipeline + a Streamlit dashboard.

> The repository's root `README.md` is the project *brief* (the build mission).
> This file is the practical "how to run it" guide. The locked design is
> `docs/DESIGN.md`; the report is `docs/report/`; the hardware manual is
> `docs/hardware/HARDWARE_BUILD_GUIDE.md`.

## Layout

```
src/aamrakshak/
  riskengine/   anthracnose (Akem HTR model) · leafwetness (sensor + estimate) · ppi (risk %, spray rules)
  sim/          weather (grounded multi-region generator) · outbreaks (independent labels) · sensors (tiers)
  eval/         metrics (from scratch) · tier_study · calibration · spray_reduction · leafwet_validation · ablation
  io/           ingest (node JSON/CSV -> Reading)
scripts/        run_evaluation.py · make_figures.py · make_sample_log.py
firmware/       aamrakshak_node/aamrakshak_node.ino  (ESP32; on-device Akem model)
app/            streamlit_app.py
tests/          33 tests; metrics cross-checked vs scikit-learn; pipeline asserts S1-S5
artifacts/      eval_metrics.json (+ figs/)
data/           sample_node_log.csv
```

## Setup

```bash
python -m venv .venv && . .venv/Scripts/activate    # Windows; use bin/activate on Unix
pip install -e ".[dev,viz,dashboard]"
```

## Run the pipeline

```bash
python scripts/run_evaluation.py     # -> artifacts/eval_metrics.json (all headline numbers)
python scripts/make_figures.py       # -> artifacts/figs/*.png (reads the JSON)
python scripts/make_sample_log.py    # -> data/sample_node_log.csv (dashboard demo data)
pytest                               # 33 tests
ruff check src tests scripts         # lint
```

`run_evaluation.py` is the single source of truth: it generates the ground truth
once (fixed seed), runs the sensor-tier study, Platt calibration, spray-reduction
analysis, leaf-wetness sensor validation, and ablation, then writes every number
the report quotes and prints a pass/fail for each success condition (S1-S5).

## Dashboard

```bash
streamlit run app/streamlit_app.py
```

Loads the bundled sample log (or upload your own node CSV/JSON), recomputes risk
with the same Akem model the node runs, and shows the current risk band, the
early-warning spray decision, and the season history.

## Hardware

Build the node from `docs/hardware/HARDWARE_BUILD_GUIDE.md` (≈ 8 h, ≈ ₹1,900) and
flash `firmware/` per `firmware/README.md`. The node logs the same CSV schema the
dashboard ingests.

## Data honesty

Weather and outbreak labels are **simulated** from documented climate normals and
an *independent* epidemiological generator (different from the model under test,
so the backtest is not circular). The leaf-wetness sensor is validated on an
emulated-but-physically-grounded bench model. All of this is stated in the report
and in `eval_metrics.json["meta"]`. Nothing is hand-typed; everything regenerates
from the seed.
