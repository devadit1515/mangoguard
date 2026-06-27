"""Classification metrics, implemented from their definitions.

These are hand-rolled (not imported from scikit-learn) for two reasons: it is
direct evidence of understanding for the report's science section, and it keeps
the headline numbers transparent and dependency-light. The test suite checks
each one against the scikit-learn equivalent so the implementations are trusted.

- ``roc_auc``  -- via the rank statistic (equivalent to the Mann-Whitney U),
  with average ranks for ties. AUC is the probability the model scores a random
  positive above a random negative; 0.5 is chance, 1.0 is perfect ranking.
- ``brier_score`` -- mean squared error of probability forecasts; measures
  calibration, which AUC ignores.
- ``confusion_counts`` / ``reliability_curve`` -- for figures and S3/S4.
"""

from __future__ import annotations

import numpy as np


def roc_auc(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Area under the ROC curve via the rank (Mann-Whitney) statistic."""
    y_true = np.asarray(y_true, dtype=float)
    scores = np.asarray(scores, dtype=float)
    n_pos = float(np.sum(y_true == 1))
    n_neg = float(np.sum(y_true == 0))
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    # Average ranks (1-based) handle tied scores correctly.
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    sorted_scores = scores[order]
    i = 0
    n = len(scores)
    while i < n:
        j = i
        while j + 1 < n and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        avg_rank = 0.5 * (i + j) + 1.0  # mean of ranks (i+1 .. j+1)
        ranks[order[i : j + 1]] = avg_rank
        i = j + 1
    sum_ranks_pos = float(np.sum(ranks[y_true == 1]))
    return (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def roc_curve(y_true: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """False-positive and true-positive rates over all thresholds."""
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)
    order = np.argsort(-scores, kind="mergesort")
    y_sorted = y_true[order]
    tp = np.cumsum(y_sorted)
    fp = np.cumsum(1 - y_sorted)
    n_pos = tp[-1] if len(tp) else 0
    n_neg = fp[-1] if len(fp) else 0
    if n_pos == 0 or n_neg == 0:
        return np.array([0.0, 1.0]), np.array([0.0, 1.0])
    tpr = np.concatenate([[0.0], tp / n_pos])
    fpr = np.concatenate([[0.0], fp / n_neg])
    return fpr, tpr


def brier_score(y_true: np.ndarray, prob: np.ndarray) -> float:
    """Mean squared error between predicted probability and binary outcome."""
    y_true = np.asarray(y_true, dtype=float)
    prob = np.asarray(prob, dtype=float)
    return float(np.mean((prob - y_true) ** 2))


def confusion_counts(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    """2x2 confusion counts for binary predictions."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def classification_report(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Accuracy, precision, recall, F1 from the confusion counts."""
    c = confusion_counts(y_true, y_pred)
    tp, tn, fp, fn = c["tp"], c["tn"], c["fp"], c["fn"]
    total = tp + tn + fp + fn
    acc = (tp + tn) / total if total else float("nan")
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec and rec and (prec + rec) else float("nan")
    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1, **c}


def reliability_curve(
    y_true: np.ndarray, prob: np.ndarray, n_bins: int = 10
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Binned (predicted, observed) frequencies for a calibration plot."""
    y_true = np.asarray(y_true, dtype=float)
    prob = np.asarray(prob, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(prob, edges) - 1, 0, n_bins - 1)
    pred_mean = np.full(n_bins, np.nan)
    obs_mean = np.full(n_bins, np.nan)
    counts = np.zeros(n_bins, dtype=int)
    for b in range(n_bins):
        m = idx == b
        counts[b] = int(np.sum(m))
        if counts[b] > 0:
            pred_mean[b] = float(np.mean(prob[m]))
            obs_mean[b] = float(np.mean(y_true[m]))
    return pred_mean, obs_mean, counts
