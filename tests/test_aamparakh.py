"""Tests for the AamParakh pipeline: split integrity, band simulation, metrics, models.

Metrics are cross-checked against scikit-learn so the from-scratch implementations
are trustworthy. Run with:  pytest
"""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aamparakh import data as D  # noqa: E402
from aamparakh import evaluate as E  # noqa: E402
from aamparakh import farm as F  # noqa: E402
from aamparakh import models as M  # noqa: E402
from aamparakh import sensors as S  # noqa: E402

DATA_PRESENT = D.DATA_PATH.exists()
needs_data = pytest.mark.skipif(not DATA_PRESENT, reason="benchmark CSV not present")


# ---- metrics vs scikit-learn ----
def test_metrics_match_sklearn():
    from sklearn.metrics import mean_squared_error, r2_score

    rng = np.random.default_rng(0)
    y = rng.normal(16, 2, 500)
    p = y + rng.normal(0, 1, 500)
    assert E.rmse(y, p) == pytest.approx(np.sqrt(mean_squared_error(y, p)), rel=1e-9)
    assert E.r2(y, p) == pytest.approx(r2_score(y, p), rel=1e-9)
    assert E.bias(y, p) == pytest.approx(np.mean(p - y), rel=1e-9)


def test_rpd_and_sep_definitions():
    rng = np.random.default_rng(1)
    y = rng.normal(16, 3, 300)
    p = y + 0.5 + rng.normal(0, 1, 300)  # deliberate bias
    resid = p - y
    assert E.sep(y, p) == pytest.approx(np.sqrt(np.mean((resid - resid.mean()) ** 2)))
    assert E.rpd(y, p) == pytest.approx(np.std(y, ddof=1) / E.sep(y, p))
    assert E.sep(y, p) <= E.rmse(y, p) + 1e-9  # SEP never exceeds RMSEP


# ---- band simulation ----
def test_band_response_normalised():
    wl = np.arange(400, 1001, 3)
    R = S.band_response_matrix(wl, S.DEVICE_BANDS)
    assert R.shape == (8, len(wl))
    assert np.allclose(R.sum(axis=1), 1.0)  # each channel integrates to one


def test_simulate_bands_shape_and_smoothness():
    wl = np.arange(400, 1001, 3)
    spectra = np.ones((5, len(wl)))
    B = S.simulate_bands(spectra, wl, S.DEVICE_BANDS)
    assert B.shape == (5, 8)
    assert np.allclose(B, 1.0)  # a flat spectrum integrates to its constant in every band


def test_device_bands_are_nir_and_detectable():
    centres = S.band_centres(S.DEVICE_BANDS)
    assert centres.min() >= 700  # all near-infrared
    assert centres.max() <= 980  # silicon-photodiode detectable


# ---- split integrity ----
@needs_data
def test_standard_split_sizes_and_disjoint():
    df = D.load_dataset()
    cal, tun, test = D.cal_tune_test(df)
    assert (len(cal), len(tun), len(test)) == (7413, 2830, 1448)
    assert len(cal) + len(tun) + len(test) == len(df)


@needs_data
def test_test_set_is_a_held_out_season():
    df = D.load_dataset()
    _, test = D.standard_split(df)
    # the external validation set is a single independent season
    assert test["Season"].nunique() == 1


# ---- models ----
@needs_data
def test_full_spectrum_beats_naive_and_is_bounded():
    df = D.load_dataset()
    cal, tun, test = D.cal_tune_test(df)
    Xc, _ = D.spectra(cal, D.DMC_WINDOW)
    Xt, _ = D.spectra(tun, D.DMC_WINDOW)
    Xe, _ = D.spectra(test, D.DMC_WINDOW)
    yc, yt, ye = cal[D.TARGET].to_numpy(), tun[D.TARGET].to_numpy(), test[D.TARGET].to_numpy()
    m = M.FullSpectrumModel().fit(Xc, yc, Xt, yt)
    pe = m.predict(Xe)
    assert E.r2(ye, pe) > 0.75  # clearly better than the mean
    assert 8 < pe.mean() < 26  # predictions are in a physical DM range


def test_greedy_selection_orders_by_improvement():
    rng = np.random.default_rng(2)
    n, b = 400, 6
    B = rng.normal(0, 1, (n, b))
    y = 3 * B[:, 2] + 0.5 * B[:, 4] + rng.normal(0, 0.3, n)  # band 2 most informative
    order, path = M.greedy_band_selection(B, y, B, y, np.arange(b) * 10.0)
    assert order[0] == 2  # the strongest band is chosen first
    assert len(path) == b
    assert path[0]["tuning_rmse"] >= path[-1]["tuning_rmse"]  # error never worsens overall


# ---- farm placeholder ----
@needs_data
def test_placeholder_schema_and_flagged(tmp_path):
    p = tmp_path / "farm.csv"
    df = F.generate_placeholder(n_per_cultivar=10, path=p)
    assert list(df.columns) == F.SCHEMA
    assert len(df) == 20
    assert F.is_placeholder(df)
    with pytest.raises(ValueError):
        F.load_farm(p, allow_placeholder=False)  # refuses to pass placeholder as real
