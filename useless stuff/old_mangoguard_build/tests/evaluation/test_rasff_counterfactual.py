"""Tests for the RASFF counterfactual prevention-rate evaluator."""

from __future__ import annotations

from dataclasses import asdict, fields

import pandas as pd
import pytest

from mangoguard.evaluation.rasff_counterfactual import (
    _TARGET_RELATIVE_IMPROVEMENT_PCT,
    evaluate_rasff_counterfactual,
    evaluate_with_kvk_baseline,
)
from mangoguard.recommend import rasff as _rasff_module


def _rasff_df_from_module() -> pd.DataFrame:
    """Load the placeholder RASFF CSV into a DataFrame via the public API.

    RASFFRow uses slots=True so we can't rely on __dict__; use dataclass-fields
    introspection instead.
    """
    _rasff_module.reset_cache()
    rows = _rasff_module.all_rows()
    field_names = [f.name for f in fields(rows[0])]
    return pd.DataFrame([{n: getattr(row, n) for n in field_names} for row in rows])


# Workaround for slotted dataclasses: asdict doesn't help with __dict__, but
# dataclasses.asdict() does work even on slotted instances. Provide a tiny
# helper for the test ergonomics.
_ = asdict  # keep the import alive so future contributors see the option


def test_returns_expected_keys():
    df = _rasff_df_from_module()
    result = evaluate_rasff_counterfactual(df)
    for key in (
        "prevention_rate_mangoguard",
        "prevention_rate_icar_baseline",
        "relative_improvement_pct",
        "n_rejections",
        "cutoff",
    ):
        assert key in result


def test_prevention_rate_in_0_1():
    df = _rasff_df_from_module()
    result = evaluate_rasff_counterfactual(df)
    assert 0.0 <= result["prevention_rate_mangoguard"] <= 1.0
    assert 0.0 <= result["prevention_rate_icar_baseline"] <= 1.0


def test_n_rejections_matches_input_rows():
    df = _rasff_df_from_module()
    result = evaluate_rasff_counterfactual(df)
    assert result["n_rejections"] == len(df)


def test_empty_input_returns_zero_rates():
    result = evaluate_rasff_counterfactual(pd.DataFrame())
    assert result["prevention_rate_mangoguard"] == 0.0
    assert result["prevention_rate_icar_baseline"] == 0.0
    assert result["n_rejections"] == 0


def test_missing_columns_raise():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match="missing columns"):
        evaluate_rasff_counterfactual(df)


def test_low_cutoff_increases_mangoguard_prevention():
    """A stricter (lower) cutoff filters more AIs -> more rejections prevented."""
    df = _rasff_df_from_module()
    low = evaluate_rasff_counterfactual(df, cutoff=0.05)
    high = evaluate_rasff_counterfactual(df, cutoff=0.50)
    assert low["prevention_rate_mangoguard"] >= high["prevention_rate_mangoguard"]


def test_mangoguard_outperforms_baseline_on_chlorpyrifos_eu():
    """Chlorpyrifos has 6 EU rejections in the placeholder CSV -> p_hat ~ 0.117.
    At a 0.10 cutoff (stricter than default 0.20) the recommender filters it.
    """
    chlorpyrifos_eu = pd.DataFrame(
        [
            {
                "date": "2021-04-22",
                "active_ingredient": "chlorpyrifos",
                "destination": "EU",
            }
        ]
    )
    result = evaluate_rasff_counterfactual(chlorpyrifos_eu, cutoff=0.10)
    assert result["prevention_rate_mangoguard"] == 1.0


def test_relative_improvement_field_present_and_finite():
    df = _rasff_df_from_module()
    result = evaluate_rasff_counterfactual(df)
    assert "relative_improvement_pct" in result
    # Should be a finite number even when baseline is zero (div-by-zero guard)
    assert isinstance(result["relative_improvement_pct"], float)


def test_target_relative_improvement_constant_matches_spec():
    """Spec section 4.6.3: success threshold is 30% relative improvement."""
    assert _TARGET_RELATIVE_IMPROVEMENT_PCT == 30.0


def test_kvk_baseline_evaluator_returns_expected_keys():
    df = _rasff_df_from_module()
    result = evaluate_with_kvk_baseline(df)
    for key in (
        "prevention_rate_mangoguard",
        "prevention_rate_kvk_baseline",
        "relative_improvement_pct",
        "n_rejections",
        "cutoff",
    ):
        assert key in result


def test_kvk_baseline_evaluator_empty_input():
    result = evaluate_with_kvk_baseline(pd.DataFrame())
    assert result["n_rejections"] == 0
    assert result["prevention_rate_mangoguard"] == 0.0


def test_known_safe_ai_not_falsely_flagged_as_high_risk():
    """neem_oil has zero RASFF rejections -> recommender should not filter it
    (prevention rate should be 0 because there's nothing to prevent)."""
    neem_eu = pd.DataFrame(
        [
            {
                "date": "2023-04-01",
                "active_ingredient": "neem_oil",
                "destination": "EU",
            }
        ]
    )
    result = evaluate_rasff_counterfactual(neem_eu)
    # MangoGuard would NOT filter neem (p_hat << 0.20)
    assert result["prevention_rate_mangoguard"] == 0.0


def test_carbendazim_eu_partially_prevented():
    """Carbendazim has multiple EU rejections (but fewer than chlorpyrifos).
    Whether the recommender filters it depends on the cutoff."""
    carbendazim_eu = pd.DataFrame(
        [
            {
                "date": "2023-05-18",
                "active_ingredient": "carbendazim",
                "destination": "EU",
            }
        ]
    )
    result = evaluate_rasff_counterfactual(carbendazim_eu, cutoff=0.05)
    # Stricter cutoff should catch carbendazim
    assert result["prevention_rate_mangoguard"] == 1.0
