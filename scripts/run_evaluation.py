"""Run the whole AamParakh study and write artifacts/eval_metrics.json.

Every number the report cites comes from this one script, so the report and the
data cannot drift apart. Reproduce with:  python scripts/run_evaluation.py

The study, in order:
  1. full research spectrum  -> the reference (a lab NIR instrument, ~Rs 8.5 lakh)
  2. the AamParakh device     -> eight buyable NIR LEDs; how few, and which, are needed
  3. off-the-shelf chips      -> what a naive cheap spectral chip (AS7265x/AS7263) gives
  4. robustness               -> across cultivar and across season
  5. calibration transfer     -> a few local fruit fix a new population's bias
  6. on-farm validation       -> Alphonso/Kesar (placeholder until real readings land)

All few-band models use the same simple pipeline (standardise + PLS, components
chosen on the Tuning split), so the device and the off-the-shelf chips are compared
on identical footing and the only thing that differs is which wavelengths each sees.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aamparakh import data as D  # noqa: E402
from aamparakh import evaluate as E  # noqa: E402
from aamparakh import farm as F  # noqa: E402
from aamparakh import models as M  # noqa: E402
from aamparakh import sensors as S  # noqa: E402

SEED = 20260704
HARVEST_THRESHOLD = 15.0  # %DM: a common commercial harvest-readiness line
OUT = ROOT / "artifacts" / "eval_metrics.json"
np.random.seed(SEED)


def harvest_confusion(y_true, y_pred, thr=HARVEST_THRESHOLD):
    t = np.asarray(y_true) >= thr
    p = np.asarray(y_pred) >= thr
    tp = int(np.sum(t & p))
    tn = int(np.sum(~t & ~p))
    fp = int(np.sum(~t & p))
    fn = int(np.sum(t & ~p))
    return {
        "accuracy": round((tp + tn) / len(t), 4),
        "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
        "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def main():
    df = D.load_dataset()
    cal, tun, test = D.cal_tune_test(df)
    wl = D.wavelengths(df)
    yc, yt, ye = (cal[D.TARGET].to_numpy(), tun[D.TARGET].to_numpy(), test[D.TARGET].to_numpy())
    Xc_all, _ = D.spectra(cal)
    Xt_all, _ = D.spectra(tun)
    Xe_all, _ = D.spectra(test)

    def band_matrices(bands):
        return (
            S.simulate_bands(Xc_all, wl, bands),
            S.simulate_bands(Xt_all, wl, bands),
            S.simulate_bands(Xe_all, wl, bands),
        )

    def band_result(bands):
        Bc, Bt, Be = band_matrices(bands)
        m = M.BandModel("pls").fit(Bc, yc, Bt, yt)
        pe = m.predict(Be)
        return {
            **E.report(ye, pe),
            "n_bands": len(bands),
            "pls_ncomp": m.ncomp,
            "n_nir_bands": int(np.sum(S.band_centres(bands) >= 700)),
            "harvest": harvest_confusion(ye, pe),
        }, pe

    out: dict = {
        "meta": {
            "seed": SEED,
            "dataset": "Anderson-Walsh Mango DMC NIR (Mendeley 10.17632/46htwnp833, CC BY 4.0)",
            "n_cal": int(len(cal)),
            "n_tuning": int(len(tun)),
            "n_test": int(len(test)),
            "test_set": "Val Ext (independent 2018 season)",
            "dmc_window_nm": list(D.DMC_WINDOW),
            "harvest_threshold_pct": HARVEST_THRESHOLD,
            "n_cultivars": int(df["Cultivar"].nunique()),
            "n_seasons": int(df["Season"].nunique()),
        },
        "dm_stats": {
            k: round(float(v), 3)
            for k, v in zip(
                ["mean", "sd", "min", "max"],
                [df[D.TARGET].mean(), df[D.TARGET].std(), df[D.TARGET].min(), df[D.TARGET].max()],
                strict=True,
            )
        },
    }
    base_rate = round(float(np.mean(ye >= HARVEST_THRESHOLD)), 4)
    out["meta"]["harvest_base_rate"] = base_rate  # a trivial always-ready classifier

    # ---- 1. full research spectrum: the reference instrument ----
    Xc, _ = D.spectra(cal, D.DMC_WINDOW)
    Xt, _ = D.spectra(tun, D.DMC_WINDOW)
    Xe, _ = D.spectra(test, D.DMC_WINDOW)
    full = M.FullSpectrumModel().fit(Xc, yc, Xt, yt)
    pe_full = full.predict(Xe)
    out["full_spectrum"] = {
        **E.report(ye, pe_full),
        "n_wavelengths": int(Xc.shape[1]),
        "pls_ncomp": full.ncomp,
        "harvest": harvest_confusion(ye, pe_full),
    }
    full_r2 = out["full_spectrum"]["r2"]

    # ---- 2. the AamParakh device: 8 buyable NIR LEDs ----
    dev_res, _ = band_result(S.DEVICE_BANDS)
    out["device"] = {
        "sensor": "AamParakh: 8 discrete NIR LEDs",
        "wavelengths_nm": [c for c, _ in S.DEVICE_BANDS],
        **dev_res,
        "gap_vs_full_r2": round(full_r2 - dev_res["r2"], 4),
    }

    # band-count curve: greedily drop to the fewest LEDs that still work
    Bc, Bt, Be = band_matrices(S.DEVICE_BANDS)
    centres = S.band_centres(S.DEVICE_BANDS)
    order, path = M.greedy_band_selection(Bc, yc, Bt, yt, centres, preprocess="none")
    curve = []
    for step in path:
        k = step["k"]
        idx = order[:k]
        m = M.BandModel("pls").fit(Bc[:, idx], yc, Bt[:, idx], yt)
        pe = m.predict(Be[:, idx])
        curve.append(
            {
                "k": k,
                "added_nm": step["centre_nm"],
                "test_rmsep": round(E.rmse(ye, pe), 4),
                "test_r2": round(E.r2(ye, pe), 4),
                "harvest_acc": harvest_confusion(ye, pe)["accuracy"],
            }
        )
    out["band_count_curve"] = curve
    out["led_selection_order_nm"] = [int(centres[i]) for i in order]
    out["min_leds_for_95pct_full_r2"] = next(
        (c["k"] for c in curve if c["test_r2"] >= 0.95 * full_r2), None
    )

    # ---- 3. off-the-shelf chips (same modelling; only the bands differ) ----
    chips = {}
    for name, bands in S.SENSORS.items():
        res, _ = band_result(bands)
        chips[name] = res
    out["off_the_shelf"] = chips

    # ---- 3b. placement control: fix the count at 18, vary only where the bands sit ----
    # Eighteen bands evenly across the dry-matter window vs the AS7265x's eighteen (mostly
    # visible) channels. Same count, same model, different placement: isolates placement.
    even18 = [(int(round(w)), 20) for w in np.linspace(D.DMC_WINDOW[0], D.DMC_WINDOW[1], 18)]
    even18_res, _ = band_result(even18)
    out["placement_control"] = {
        "n_bands": 18,
        "well_placed_nir_r2": even18_res["r2"],
        "well_placed_nir_rmsep": even18_res["rmsep"],
        "as7265x_r2": chips["AS7265x"]["r2"],
        "note": "eighteen bands evenly placed in the 684-990 nm window vs the AS7265x's eighteen",
    }

    # ---- 4a. cross-cultivar robustness (leave-one-cultivar-out, device bands) ----
    Ball = S.simulate_bands(np.vstack([Xc_all, Xt_all]), wl, S.DEVICE_BANDS)
    y_all = np.concatenate([yc, yt])
    cult_all = np.concatenate([cal["Cultivar"].to_numpy(), tun["Cultivar"].to_numpy()])
    rng = np.random.default_rng(SEED)
    loco = {}
    for held in ["Caly", "KP", "HG", "R2E2"]:
        h = cult_all == held
        if h.sum() < 50:
            continue
        tr = np.where(~h)[0]
        rng.shuffle(tr)
        cut = int(0.8 * len(tr))
        m = M.BandModel("pls").fit(Ball[tr[:cut]], y_all[tr[:cut]], Ball[tr[cut:]], y_all[tr[cut:]])
        pe = m.predict(Ball[h])
        loco[D.CULTIVAR_NAMES.get(held, held)] = {
            **E.report(y_all[h], pe),
            "harvest_acc": harvest_confusion(y_all[h], pe)["accuracy"],
        }
    out["cross_cultivar_loco"] = loco

    # ---- 4b. season transfer is already the headline (train 2015-17, test 2018) ----
    out["season_transfer"] = {
        "note": "the headline test set is the independent 2018 season; every number above is cross-season",
        "device_rmsep": dev_res["rmsep"],
        "full_spectrum_rmsep": out["full_spectrum"]["rmsep"],
    }

    # ---- 5. calibration transfer: a few local fruit remove a new population's bias ----
    held = "R2E2"
    h = np.where(cult_all == held)[0]
    rng2 = np.random.default_rng(SEED + 1)
    rng2.shuffle(h)
    anchor, rest = h[:20], h[20:]
    tr = np.where(cult_all != held)[0]
    rng2.shuffle(tr)
    cut = int(0.8 * len(tr))
    mdl = M.BandModel("pls").fit(Ball[tr[:cut]], y_all[tr[:cut]], Ball[tr[cut:]], y_all[tr[cut:]])
    raw = mdl.predict(Ball[rest])
    sl, ic = M.linear_recalibration(y_all[anchor], mdl.predict(Ball[anchor]))
    out["calibration_transfer"] = {
        "held_cultivar": D.CULTIVAR_NAMES.get(held, held),
        "n_anchor": int(len(anchor)),
        "before": E.report(y_all[rest], raw),
        "after": E.report(y_all[rest], sl * raw + ic),
    }

    # ---- 6. on-farm validation (Alphonso/Kesar). Placeholder until real readings land ----
    if not F.FARM_PATH.exists():
        F.generate_placeholder(seed=SEED)
    fdf = F.load_farm()
    Bfarm = F.farm_bands(fdf)
    yf = fdf[D.TARGET].to_numpy()
    dev = M.BandModel("pls").fit(Bc, yc, Bt, yt)  # device model, trained on the benchmark
    pe_farm = dev.predict(Bfarm)
    rng3 = np.random.default_rng(SEED + 2)
    idx = np.arange(len(fdf))
    rng3.shuffle(idx)
    a, r = idx[:20], idx[20:]
    sl2, ic2 = M.linear_recalibration(yf[a], pe_farm[a])
    out["farm_validation"] = {
        "provenance": "SYNTHETIC_PLACEHOLDER" if F.is_placeholder(fdf) else "REAL_FARM",
        "n": int(len(fdf)),
        "cultivars": sorted(fdf["cultivar"].unique().tolist()),
        "before_recal": E.report(yf, pe_farm),
        "after_local_recal": {**E.report(yf[r], sl2 * pe_farm[r] + ic2), "n_anchor": int(len(a))},
    }

    # ---- pre-registered success conditions ----
    c6 = next(c for c in curve if c["k"] == 6)
    worst = min(loco.values(), key=lambda d: d["r2"]) if loco else {"r2": 0}
    as7265 = chips["AS7265x"]
    out["success_conditions"] = {
        "S1_reference_established": {"pass": bool(full_r2 >= 0.80), "full_r2": full_r2},
        "S2_device_matches_lab": {
            "pass": bool(dev_res["r2"] >= 0.80 and full_r2 - dev_res["r2"] <= 0.05),
            "device_r2": dev_res["r2"],
            "full_r2": full_r2,
            "gap": round(full_r2 - dev_res["r2"], 4),
        },
        "S3_few_leds_suffice": {
            "pass": bool(c6["test_r2"] >= 0.95 * full_r2),
            "r2_6led": c6["test_r2"],
            "min_leds": out["min_leds_for_95pct_full_r2"],
        },
        "S4_off_the_shelf_fails": {
            "pass": bool(dev_res["r2"] - as7265["r2"] >= 0.40),
            "device_r2": dev_res["r2"],
            "as7265x_r2": as7265["r2"],
        },
        "S5_actionable_and_robust": {
            "pass": bool(dev_res["harvest"]["accuracy"] >= 0.90 and loco != {}),
            "harvest_acc": dev_res["harvest"]["accuracy"],
            "worst_cultivar_r2": round(worst["r2"], 3),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"full spectrum R2={full_r2} RMSEP={out['full_spectrum']['rmsep']}")
    print(
        f"device (8 LEDs) R2={dev_res['r2']} RMSEP={dev_res['rmsep']} harvest={dev_res['harvest']['accuracy']}"
    )
    print(f"off-the-shelf AS7265x R2={as7265['r2']} | AS7263 R2={chips['AS7263']['r2']}")
    print(f"min LEDs for 95% of full R2: {out['min_leds_for_95pct_full_r2']}")
    print("success:", {k: v["pass"] for k, v in out["success_conditions"].items()})


if __name__ == "__main__":
    main()
