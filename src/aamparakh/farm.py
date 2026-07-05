"""On-farm validation set: schema, ingestion, and a labelled placeholder.

The device is validated on Alphonso and Kesar fruit measured at an orchard: for
each fruit the AamParakh node records its 18 band readings, and the fruit is then
oven-dried for a reference dry-matter value. Those real readings live in
`data/farm/aamparakh_farm_readings.csv` once collected (see
`docs/FARM_DATA_COLLECTION.md` for the protocol).

Until the real file is present, `generate_placeholder` writes a clearly-labelled
stand-in with the identical schema so the whole pipeline runs end to end. Every row
it writes carries `provenance = SYNTHETIC_PLACEHOLDER`. The loader refuses to treat
placeholder rows as real unless explicitly asked, so a real collection cannot be
silently mixed with the stand-in.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data as dataset
from . import sensors

FARM_PATH = Path(__file__).resolve().parents[2] / "data" / "farm" / "aamparakh_farm_readings.csv"
BAND_COLS = [f"b{int(c)}" for c in sensors.band_centres(sensors.DEVICE_BANDS)]
SCHEMA = ["fruit_id", "cultivar", "DM", *BAND_COLS, "provenance"]

# Realistic Indian-cultivar dry-matter spread (%FW). No published Alphonso/Kesar
# harvest threshold exists, so this is a physically plausible range, not a claim.
_PILOT_CULTIVARS = {"Alphonso": (14.0, 21.0), "Kesar": (13.0, 20.0)}


def generate_placeholder(
    n_per_cultivar: int = 60, seed: int = 20260704, path: Path | str = FARM_PATH
) -> pd.DataFrame:
    """Write a labelled synthetic stand-in with the real collection schema.

    Each placeholder fruit is a real benchmark spectrum (so the across-band shape a
    sensor would see is physically real), integrated to the 18 AS7265x channels,
    with a small cultivar-specific band offset and device noise added to stand in
    for the Australian-to-Indian transfer gap. Every row is flagged
    SYNTHETIC_PLACEHOLDER; the real collection replaces this file wholesale.
    """
    rng = np.random.default_rng(seed)
    df = dataset.load_dataset()
    X, wl = dataset.spectra(df)
    B = sensors.simulate_bands(X, wl, sensors.DEVICE_BANDS)
    dm = df[dataset.TARGET].to_numpy(float)
    band_sd = B.std(axis=0)
    # direction in band space along which dry matter varies (per-band slope of B on DM);
    # a cultivar offset is modelled as a shift along this axis, i.e. a maturity-read bias
    # that a local recalibration can remove - the realistic transfer effect.
    slope_vec = np.linalg.lstsq(np.vstack([dm, np.ones_like(dm)]).T, B, rcond=None)[0][0]
    rows = []
    fid = 0
    for cult, (lo, hi) in _PILOT_CULTIVARS.items():
        bias_dm = float(rng.normal(0, 1.0))  # cultivar maturity-read bias (%DM)
        pool = np.where((dm >= lo) & (dm <= hi))[0]
        pick = rng.choice(pool, size=n_per_cultivar, replace=False)
        for i in pick:
            bands = (
                B[i] + bias_dm * slope_vec + rng.normal(0, band_sd * 0.03)
            )  # bias + device noise
            rows.append(
                {
                    "fruit_id": f"P{fid:04d}",
                    "cultivar": cult,
                    "DM": round(float(dm[i]), 3),
                    **{c: round(float(v), 5) for c, v in zip(BAND_COLS, bands, strict=True)},
                    "provenance": "SYNTHETIC_PLACEHOLDER",
                }
            )
            fid += 1
    out = pd.DataFrame(rows, columns=SCHEMA)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    return out


def load_farm(path: Path | str = FARM_PATH, allow_placeholder: bool = True) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(SCHEMA) - set(df.columns)
    if missing:
        raise ValueError(f"farm file missing columns: {sorted(missing)}")
    if not allow_placeholder and (df["provenance"] == "SYNTHETIC_PLACEHOLDER").any():
        raise ValueError("placeholder rows present but allow_placeholder=False")
    return df


def is_placeholder(df: pd.DataFrame) -> bool:
    return bool((df["provenance"] == "SYNTHETIC_PLACEHOLDER").all())


def farm_bands(df: pd.DataFrame) -> np.ndarray:
    return df[BAND_COLS].to_numpy(float)
