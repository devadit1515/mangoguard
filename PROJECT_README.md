# AamParakh: run guide

A low-cost eight-wavelength near-infrared meter that reads mango dry matter content for harvest timing, and the analysis that designed it. Everything reproduces from one dataset and one script.

## Layout

```
src/aamparakh/      analysis package (data, sensors, models, evaluate, farm)
scripts/            run_evaluation.py -> artifacts/eval_metrics.json ; make_figures.py -> artifacts/figs/
tests/              pytest suite; metrics cross-checked against scikit-learn
firmware/           ESP32 sketch for the meter + firmware README
data/raw/           the public mango NIR dataset (CC BY 4.0)
data/farm/          on-orchard readings (placeholder until collected; see FARM_DATA_COLLECTION.md)
docs/               report, build guide, farm collection guide
artifacts/          eval_metrics.json, figures, exported device model weights
```

## Reproduce the results

```
python -m venv .venv
.venv/Scripts/activate            # Windows;  source .venv/bin/activate on macOS/Linux
pip install -e ".[dev,viz]"
python scripts/run_evaluation.py  # writes artifacts/eval_metrics.json (seed 20260704, ~20 s)
python scripts/make_figures.py    # redraws every figure in artifacts/figs/
pytest                            # runs the test suite
```

## The dataset

Anderson, Walsh and Subedi (2020), *Mango DMC and NIR spectra*, Mendeley Data, doi:10.17632/46htwnp833, CC BY 4.0. 11,691 scans, ten cultivars, four seasons, with laboratory oven-dry dry-matter values. The copy in `data/raw/` is pinned by SHA-256.

## Headline result

Eight near-infrared LEDs at 730 to 970 nm predict dry matter on an unseen season at R² 0.84, against 0.85 for the full 103-wavelength research spectrum, while the off-the-shelf AS7265x and AS7263 chips reach only 0.21 and −0.14 because their bands are placed wrongly. Full write-up in `CREST_REPORT.md`.
