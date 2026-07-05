"""Models for dry-matter prediction.

Two regimes:
  * full spectrum - the research instrument. Savitzky-Golay second derivative to
    flatten baseline drift, then partial least squares (PLS). This is the reference
    the cheap sensor is measured against.
  * few bands - a cheap sensor, or a hand-picked subset of wavelengths. The readings
    are optionally scatter-corrected (standard normal variate), standardised, and
    fed to PLS. Derivatives are pointless on a handful of bands, so scatter
    correction does the job the SG derivative does on the full spectrum.

Component counts are always chosen on the Tuning split, never on the test season,
so the reported error stays honest.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter
from sklearn.cross_decomposition import PLSRegression
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .evaluate import rmse


def sg_deriv(X: np.ndarray, window: int = 17, poly: int = 2, deriv: int = 2) -> np.ndarray:
    return savgol_filter(X, window, poly, deriv=deriv, axis=1)


def snv(B: np.ndarray) -> np.ndarray:
    """Standard normal variate per row. Left unchanged if fewer than 2 columns."""
    B = np.asarray(B, float)
    if B.ndim == 1:
        B = B[:, None]
    if B.shape[1] < 2:
        return B
    m = B.mean(axis=1, keepdims=True)
    s = B.std(axis=1, keepdims=True)
    s[s == 0] = 1.0
    return (B - m) / s


def select_ncomp(cal_X, cal_y, tun_X, tun_y, max_nc: int = 30) -> int:
    """Pick the PLS component count that minimises Tuning-set RMSE."""
    best_nc, best_err = 1, np.inf
    upper = min(max_nc, cal_X.shape[1], cal_X.shape[0] - 1)
    for nc in range(1, upper + 1):
        m = PLSRegression(nc).fit(cal_X, cal_y)
        err = rmse(tun_y, m.predict(tun_X).ravel())
        if err < best_err:
            best_nc, best_err = nc, err
    return best_nc


class FullSpectrumModel:
    """SG second-derivative + PLS on the full research spectrum."""

    def __init__(self, window: int = 17, poly: int = 2, deriv: int = 2):
        self.window, self.poly, self.deriv = window, poly, deriv
        self.model: PLSRegression | None = None
        self.ncomp: int | None = None

    def _pp(self, X):
        return sg_deriv(X, self.window, self.poly, self.deriv)

    def fit(self, cal_X, cal_y, tun_X, tun_y):
        pc, pt = self._pp(cal_X), self._pp(tun_X)
        self.ncomp = select_ncomp(pc, cal_y, pt, tun_y)
        self.model = PLSRegression(self.ncomp).fit(
            np.vstack([pc, pt]), np.concatenate([cal_y, tun_y])
        )
        return self

    def predict(self, X):
        return self.model.predict(self._pp(X)).ravel()


class BandModel:
    """Standardise (optionally SNV first) + PLS or a small MLP on a few bands."""

    def __init__(self, kind: str = "pls", preprocess: str = "none"):
        self.kind, self.preprocess = kind, preprocess
        self.pipe = None
        self.ncomp: int | None = None

    def _pp(self, B):
        B = np.asarray(B, float)
        return snv(B) if self.preprocess == "snv" else B

    def fit(self, cal_B, cal_y, tun_B, tun_y):
        cal_B, tun_B = self._pp(cal_B), self._pp(tun_B)
        X = np.vstack([cal_B, tun_B])
        y = np.concatenate([cal_y, tun_y])
        if self.kind == "pls":
            sc = StandardScaler().fit(cal_B)
            self.ncomp = select_ncomp(
                sc.transform(cal_B),
                cal_y,
                sc.transform(tun_B),
                tun_y,
                max_nc=min(15, cal_B.shape[1]),
            )
            self.pipe = make_pipeline(StandardScaler(), PLSRegression(self.ncomp)).fit(X, y)
        else:
            self.pipe = make_pipeline(
                StandardScaler(),
                MLPRegressor(
                    hidden_layer_sizes=(32, 16),
                    max_iter=2000,
                    early_stopping=True,
                    alpha=1e-3,
                    random_state=0,
                ),
            ).fit(X, y)
        return self

    def predict(self, B):
        return np.asarray(self.pipe.predict(self._pp(B))).ravel()


def greedy_band_selection(
    cal_B, cal_y, tun_B, tun_y, centres, preprocess: str = "none", max_bands: int | None = None
):
    """Add bands one at a time, each the one that most cuts Tuning RMSE.

    Returns (order, path). `path` lists dicts of k, the added band index, its centre
    nm, and the Tuning RMSE at k bands. Answers 'how few bands' and 'which bands'.
    """
    n_bands = cal_B.shape[1]
    max_bands = max_bands or n_bands
    chosen: list[int] = []
    remaining = list(range(n_bands))
    path = []
    while remaining and len(chosen) < max_bands:
        best = None
        for j in remaining:
            idx = chosen + [j]
            m = BandModel("pls", preprocess).fit(cal_B[:, idx], cal_y, tun_B[:, idx], tun_y)
            err = rmse(tun_y, m.predict(tun_B[:, idx]))
            if best is None or err < best[1]:
                best = (j, err)
        chosen.append(best[0])
        remaining.remove(best[0])
        path.append(
            {
                "k": len(chosen),
                "band_index": int(best[0]),
                "centre_nm": int(centres[best[0]]),
                "tuning_rmse": round(best[1], 4),
            }
        )
    return chosen, path


def linear_recalibration(y_true, y_pred):
    """Slope/intercept least-squares correction; removes population bias, keeps ranking."""
    A = np.vstack([np.asarray(y_pred, float), np.ones(len(y_pred))]).T
    slope, intercept = np.linalg.lstsq(A, np.asarray(y_true, float), rcond=None)[0]
    return float(slope), float(intercept)
