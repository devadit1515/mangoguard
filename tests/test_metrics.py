"""Hand-rolled metrics must agree with scikit-learn (the independent oracle)."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import brier_score_loss, confusion_matrix, roc_auc_score

from aamrakshak.eval.metrics import (
    brier_score,
    classification_report,
    confusion_counts,
    roc_auc,
)


@pytest.fixture
def rng():
    return np.random.default_rng(0)


def test_roc_auc_matches_sklearn(rng):
    for _ in range(20):
        y = rng.integers(0, 2, 200)
        if y.sum() in (0, len(y)):
            continue
        s = rng.random(200)
        assert roc_auc(y, s) == pytest.approx(roc_auc_score(y, s), abs=1e-9)


def test_roc_auc_handles_ties(rng):
    # Scores with heavy ties must still match sklearn's tie handling.
    y = rng.integers(0, 2, 300)
    s = rng.integers(0, 5, 300).astype(float)  # many ties
    assert roc_auc(y, s) == pytest.approx(roc_auc_score(y, s), abs=1e-9)


def test_roc_auc_perfect_and_chance():
    y = np.array([0, 0, 1, 1])
    assert roc_auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == pytest.approx(1.0)
    assert roc_auc(y, np.array([0.9, 0.8, 0.2, 0.1])) == pytest.approx(0.0)


def test_brier_matches_sklearn(rng):
    y = rng.integers(0, 2, 200)
    p = rng.random(200)
    assert brier_score(y, p) == pytest.approx(brier_score_loss(y, p), abs=1e-12)


def test_confusion_matches_sklearn(rng):
    y = rng.integers(0, 2, 200)
    p = rng.integers(0, 2, 200)
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    c = confusion_counts(y, p)
    assert (c["tn"], c["fp"], c["fn"], c["tp"]) == (tn, fp, fn, tp)


def test_classification_report_consistency(rng):
    y = rng.integers(0, 2, 500)
    p = rng.integers(0, 2, 500)
    r = classification_report(y, p)
    # Confusion cells sum to n; accuracy derivable from cells.
    assert r["tp"] + r["tn"] + r["fp"] + r["fn"] == 500
    assert r["accuracy"] == pytest.approx((r["tp"] + r["tn"]) / 500)
