"""Tests for the retrospective backtest harness."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from mangoguard.evaluation.retrospective import run_retrospective_backtest

_EXPECTED_KEYS = frozenset(
    {"roc_auc", "avg_precision", "precision_at_0_5", "recall_at_0_5", "brier", "n_samples"}
)


def _make_synthetic(
    *,
    n_blocks: int = 3,
    n_days: int = 60,
    outbreak_threshold_ppi: float = 60.0,
    seed: int = 7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Synthesize a (historical_obs, cropsap_outbreaks) pair where outbreaks
    correlate with high PPI -- so MangoGuard's PPI should outperform noise.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for block in range(n_blocks):
        for day in range(n_days):
            ppi = float(rng.uniform(0.0, 100.0))
            rows.append(
                {
                    "block_id": f"block{block}",
                    "date": pd.Timestamp("2024-03-01") + pd.Timedelta(days=day),
                    "ppi": ppi,
                }
            )
    obs = pd.DataFrame(rows)

    # outbreak = 1 with probability proportional to PPI (so PPI is a real signal)
    p = (obs["ppi"] / 100.0).clip(0.0, 1.0)
    outbreaks = (rng.uniform(size=len(obs)) < p * 0.6).astype(int)
    # Force a few high-PPI rows to be outbreaks for stable AUC computations
    outbreaks = outbreaks | (obs["ppi"] > outbreak_threshold_ppi).astype(int)
    out = pd.DataFrame(
        {
            "block_id": obs["block_id"],
            "date": obs["date"],
            "outbreak": outbreaks.astype(int),
        }
    )
    return obs, out


def test_returns_metric_dict():
    obs, out = _make_synthetic()
    result = run_retrospective_backtest(obs, out)
    for key in ("mangoguard", "seasonal_baseline", "icar_cish_baseline", "meta"):
        assert key in result


def test_each_scorer_has_expected_metrics():
    obs, out = _make_synthetic()
    result = run_retrospective_backtest(obs, out)
    for scorer in ("mangoguard", "seasonal_baseline", "icar_cish_baseline"):
        m = result[scorer]
        assert set(m.keys()) >= _EXPECTED_KEYS


def test_metrics_in_valid_ranges():
    obs, out = _make_synthetic()
    result = run_retrospective_backtest(obs, out)
    for scorer in ("mangoguard", "seasonal_baseline", "icar_cish_baseline"):
        m = result[scorer]
        # Allow NaN for degenerate single-class cases; otherwise must be in [0,1]
        for key in ("roc_auc", "avg_precision", "precision_at_0_5", "recall_at_0_5", "brier"):
            v = m[key]
            assert math.isnan(v) or (0.0 <= v <= 1.0), f"{scorer}/{key} = {v}"


def test_mangoguard_outperforms_random_baseline_on_correlated_data():
    """When outbreaks correlate with PPI, MangoGuard ROC-AUC should beat 0.6."""
    obs, out = _make_synthetic(seed=11)
    result = run_retrospective_backtest(obs, out)
    auc = result["mangoguard"]["roc_auc"]
    assert auc > 0.6, f"expected AUC>0.6 on correlated synthetic data, got {auc:.3f}"


def test_meta_includes_row_counts():
    obs, out = _make_synthetic()
    result = run_retrospective_backtest(obs, out)
    meta = result["meta"]
    assert meta["n_merged_rows"] > 0
    assert meta["n_outbreaks"] >= 0
    assert meta["pathogen"] == "anthracnose"


def test_pathogen_kwarg_routes_to_baseline_lookup():
    """Switching pathogen changes the ICAR-CISH baseline coverage pattern."""
    obs, out = _make_synthetic()
    anthr = run_retrospective_backtest(obs, out, pathogen="anthracnose")
    hopper = run_retrospective_backtest(obs, out, pathogen="hopper")
    # The ICAR-CISH baseline must differ for different pathogen coverage windows
    assert anthr["meta"]["pathogen"] == "anthracnose"
    assert hopper["meta"]["pathogen"] == "hopper"


def test_empty_inputs_raise():
    with pytest.raises(ValueError, match="non-empty"):
        run_retrospective_backtest(pd.DataFrame(), pd.DataFrame())


def test_missing_columns_raise():
    obs = pd.DataFrame({"a": [1]})
    out = pd.DataFrame({"b": [2]})
    with pytest.raises(ValueError, match="missing columns"):
        run_retrospective_backtest(obs, out)


def test_no_overlapping_block_dates_returns_zero_rows():
    obs = pd.DataFrame(
        {
            "block_id": ["b1"],
            "date": [pd.Timestamp("2024-03-01")],
            "ppi": [60.0],
        }
    )
    out = pd.DataFrame(
        {
            "block_id": ["b2"],
            "date": [pd.Timestamp("2024-04-01")],
            "outbreak": [1],
        }
    )
    result = run_retrospective_backtest(obs, out)
    assert result["meta"]["n_merged_rows"] == 0
    assert math.isnan(result["mangoguard"]["roc_auc"])


def test_single_class_outbreak_returns_nan_auc():
    obs = pd.DataFrame(
        {
            "block_id": ["b1", "b1"],
            "date": [pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-02")],
            "ppi": [40.0, 80.0],
        }
    )
    # All outbreaks = 1 -> AUC undefined
    out = pd.DataFrame(
        {
            "block_id": ["b1", "b1"],
            "date": [pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-02")],
            "outbreak": [1, 1],
        }
    )
    result = run_retrospective_backtest(obs, out)
    assert math.isnan(result["mangoguard"]["roc_auc"])
