"""Loading and splitting the public mango NIR dry-matter benchmark.

Dataset: Anderson, Walsh & Subedi, "Mango DMC and NIR spectra", Mendeley Data
(DOI 10.17632/46htwnp833), CC BY 4.0. One row per fruit scan: metadata columns
plus one reflectance column per wavelength (309-1140 nm, 3 nm step). The target is
oven-dry dry matter content, `DM`, as a percentage of fresh weight.

The authors ship an explicit three-way partition in the `Set` column:
  Cal      (7413) - calibration
  Tuning   (2830) - model/hyper-parameter selection
  Val Ext  (1448) - an independent later season (2018), the honest test set.
The community convention builds on Cal+Tuning and reports on Val Ext; we follow it
so our numbers sit next to the published ones.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TARGET = "DM"
META_COLS = ["Set", "Season", "Region", "Date", "Type", "Cultivar", "Pop", "Temp", "DM"]
DMC_WINDOW = (684, 990)  # the wavelength window the Walsh group recommend for DMC
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "mango_dmc_nir.csv"

# Short cultivar codes in the dataset -> readable names (for figures/tables).
CULTIVAR_NAMES = {
    "Caly": "Calypso",
    "KP": "Kensington Pride",
    "HG": "Honey Gold",
    "R2E2": "R2E2",
    "Keitt": "Keitt",
    "LadyJ": "Lady Jane",
    "LadyG": "Lady Grace",
}


def load_dataset(path: Path | str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    if TARGET not in df.columns:
        raise ValueError(f"target column {TARGET!r} missing from {path}")
    return df


def wl_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.isdigit()]


def wavelengths(df: pd.DataFrame) -> np.ndarray:
    return np.array([int(c) for c in wl_columns(df)])


def spectra(df: pd.DataFrame, wl_range: tuple[int, int] | None = None):
    """Return (X, wl): the reflectance matrix and its wavelength axis."""
    cols = wl_columns(df)
    wl = np.array([int(c) for c in cols])
    if wl_range is not None:
        keep = (wl >= wl_range[0]) & (wl <= wl_range[1])
        cols = [c for c, k in zip(cols, keep, strict=True) if k]
        wl = wl[keep]
    return df[cols].to_numpy(dtype=float), wl


def standard_split(df: pd.DataFrame):
    """(train, test) with train = Cal+Tuning, test = Val Ext (independent season)."""
    train = df[df["Set"].isin(["Cal", "Tuning"])].reset_index(drop=True)
    test = df[df["Set"] == "Val Ext"].reset_index(drop=True)
    return train, test


def cal_tune_test(df: pd.DataFrame):
    """(cal, tuning, test) kept separate so component selection never touches the test."""
    return (
        df[df["Set"] == "Cal"].reset_index(drop=True),
        df[df["Set"] == "Tuning"].reset_index(drop=True),
        df[df["Set"] == "Val Ext"].reset_index(drop=True),
    )


def nearest_wl_cols(df: pd.DataFrame, centres) -> list[str]:
    """Column names of the wavelengths nearest to each requested centre (nm)."""
    cols = wl_columns(df)
    wl = np.array([int(c) for c in cols])
    return [cols[int(np.argmin(np.abs(wl - c)))] for c in centres]


def narrow_picks(df: pd.DataFrame, centres) -> np.ndarray:
    """Reflectance sampled at single wavelengths nearest each centre (a narrow-band pick)."""
    return df[nearest_wl_cols(df, centres)].to_numpy(dtype=float)
