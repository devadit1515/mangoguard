"""Run the real MangoGuard evaluation harness and dump genuine metrics.

Run::

    python scripts/run_evaluation.py

Writes ``artifacts/eval_metrics.json`` with the *computed* outputs of the
project's own evaluators (``evaluation/retrospective.py``,
``evaluation/rasff_counterfactual.py``) plus a real XGBoost yield/price
benchmark. Every number the report quotes in Section 8 is read from this
file -- nothing is hand-typed.

DATA PROVENANCE (read this -- it is what makes the results honest):

* The RASFF counterfactual runs on ``data/rasff_mango_rejections.csv``,
  compiled from the *documented* active ingredients behind real Indian-mango
  EU border rejections (chlorpyrifos, carbendazim, etc.). Exact row counts
  are representative, pending a live RASFF-portal pull (future work).
* The retrospective backtest and connector-tier study run on a SIMULATED
  multi-season weather record generated from documented Konkan climate
  normals. Outbreak labels are drawn from an INDEPENDENT noisy epidemiological
  generator (different coefficients + Bernoulli noise) so the PPI does not
  trivially reproduce them -- the backtest measures whether the pipeline
  *recovers* the signal. This validates the implementation; field-accuracy on
  real outbreak data is future work.
* Yield/price uses a synthetic dataset with a documented-relationship signal
  plus noise; the model and metrics are real.

Deterministic: seeded NumPy, fixed dates. Re-running reproduces the JSON.
"""

from __future__ import annotations

import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, roc_auc_score
from xgboost import XGBRegressor

from mangoguard.evaluation.baseline_schedule import load_baseline
from mangoguard.evaluation.retrospective import run_retrospective_backtest
from mangoguard.recommend import mrl_loader, rasff
from mangoguard.recommend.markets import MarketSegment, mrl_tables_for
from mangoguard.risk.ppi import compute_ppi
from mangoguard.schema import BlockObservation, ConnectorSource
from mangoguard.store import FeedStore

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

SEED = 20260622
BLOCKS = ["ratnagiri_b1", "ratnagiri_b2", "devgad_b1", "sindhudurg_b1"]
SEASONS = [2019, 2020, 2021, 2022, 2023, 2024]
ISO_WEEKS = range(2, 22)  # flowering -> harvest window (Jan-late May)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _week_monday(year: int, iso_week: int) -> datetime:
    # ISO week -> the Monday of that week, at UTC midnight.
    d = datetime.fromisocalendar(year, iso_week, 1)
    return datetime.combine(d.date(), time.min, tzinfo=timezone.utc)


def _konkan_weather(rng: np.random.Generator, iso_week: int) -> dict[str, float]:
    """One block-week of Konkan-normal weather (flowering->harvest).

    Temperature climbs from ~24C (Jan) to ~33C (May); humid spells become
    more frequent toward the pre-monsoon. Returns daily-aggregate values the
    PPI window will see.
    """
    season_frac = (iso_week - 2) / 20.0
    t_mean = 24.0 + 9.0 * season_frac + rng.normal(0, 1.0)
    diurnal = rng.uniform(7.0, 12.0)
    t_max = t_mean + diurnal / 2
    t_min = t_mean - diurnal / 2
    # humid spell: Bernoulli, more likely later in season
    humid_spell = rng.random() < (0.25 + 0.35 * season_frac)
    rh = rng.uniform(82, 95) if humid_spell else rng.uniform(55, 72)
    leaf_wet = rng.uniform(6, 11) if humid_spell else rng.uniform(0, 3)
    wind = rng.uniform(0.6, 3.5)
    solar = rng.uniform(45, 90) if humid_spell else rng.uniform(90, 160)
    return {
        "t_max_c": float(t_max),
        "t_min_c": float(t_min),
        "rh_pct": float(rh),
        "leaf_wetness_hr": float(leaf_wet),
        "wind_speed_ms": float(wind),
        "solar_w_m2": float(solar),
    }


def _outbreak_prob(w: dict[str, float]) -> float:
    """INDEPENDENT epidemiological generator (NOT the PPI formula).

    Uses a different functional form/coefficients from Akem's logistic model
    so the backtest is not circular. Anthracnose is favoured by high RH and
    long leaf wetness with a small diurnal range; sun suppresses it.
    """
    rng_range = max(0.1, w["t_max_c"] - w["t_min_c"])
    z = (
        -3.1
        + 3.8 * (w["rh_pct"] / 100.0)
        + 0.22 * w["leaf_wetness_hr"]
        - 0.05 * rng_range
        - 0.012 * w["solar_w_m2"]
    )
    return float(_sigmoid(np.array(z)))


def generate_truth() -> list[dict]:
    """Generate the ground-truth weather + outbreak labels ONCE.

    Crucially separate from sensor-noise generation so every connector tier
    sees the *same* underlying seasons -- only sensor quality differs. This
    is what makes the tier comparison valid (and monotonic).
    """
    rng = np.random.default_rng(SEED)
    records: list[dict] = []
    for season in SEASONS:
        for block in BLOCKS:
            taluka = block.split("_")[0]
            for wk in ISO_WEEKS:
                truth = _konkan_weather(rng, wk)
                p = _outbreak_prob(truth)
                outbreak = int(rng.random() < p)
                day = _week_monday(season, wk) + timedelta(days=6)
                records.append(
                    {
                        "season": season,
                        "block": block,
                        "taluka": taluka,
                        "wk": wk,
                        "day": day,
                        "truth": truth,
                        "hopper": float(rng.uniform(10, 45)),
                        "outbreak": outbreak,
                    }
                )
    return records


def build_obs_df(
    truth_records: list[dict], noise_sigma: float, include_lw: bool, noise_seed: int = SEED + 1
):
    """Compute the real PPI for every record at a given sensor-noise level.

    ``noise_sigma`` models sensor quality (free district feed = noisy;
    commercial micro-station = clean); ``include_lw`` models that the
    cheapest tier has no leaf-wetness sensor. Returns (obs_df, out_df).
    """
    noise = np.random.default_rng(noise_seed)  # noise rng independent of truth
    ppi_rows, out_rows = [], []
    for rec in truth_records:
        truth, day, block = rec["truth"], rec["day"], rec["block"]
        store = FeedStore(":memory:")
        for back in range(8):
            ts = day - timedelta(days=back)
            store.insert(
                BlockObservation(
                    block_id=block,
                    ts=ts,
                    source=ConnectorSource.IMD,
                    t_air_c=truth["t_max_c"] + noise.normal(0, noise_sigma),
                    rh_pct=float(
                        np.clip(truth["rh_pct"] + noise.normal(0, noise_sigma * 3), 0, 100)
                    ),
                    leaf_wetness_hr=(
                        max(0.0, truth["leaf_wetness_hr"] + noise.normal(0, noise_sigma))
                        if include_lw
                        else None
                    ),
                    wind_speed_ms=truth["wind_speed_ms"],
                    solar_w_m2=truth["solar_w_m2"],
                )
            )
        store.insert(
            BlockObservation(
                block_id=f"{rec['taluka']}_hopper",
                ts=day,
                source=ConnectorSource.CROPSAP,
                cropsap_pest_pressure=rec["hopper"],
            )
        )
        comp = compute_ppi(store, block, day.date())
        store.close()
        key = {"block_id": block, "date": day.date().isoformat()}
        ppi_rows.append({**key, "ppi": comp["ppi"]})
        out_rows.append({**key, "outbreak": rec["outbreak"]})
    return pd.DataFrame(ppi_rows), pd.DataFrame(out_rows)


def run_retrospective(truth_records: list[dict]) -> dict:
    obs, out = build_obs_df(truth_records, noise_sigma=1.0, include_lw=True)
    result = run_retrospective_backtest(obs, out)
    result["meta"]["outbreak_rate"] = float(out["outbreak"].mean())
    return result


def run_connector_tiers(truth_records: list[dict], n_seeds: int = 8) -> dict:
    """AUC at three integration tiers = same seasons, decreasing sensor noise.

    AUC is averaged over ``n_seeds`` independent noise realisations so the
    tier comparison reflects sensor quality, not single-sample variance.
    """
    tiers = [
        ("free_feeds_only", 5.0, False, 3),  # coarse district data, no leaf wetness
        ("plus_one_commercial", 2.0, True, 4),  # add a micro-station
        ("multi_system_fusion", 0.7, True, 5),  # add a second, denser feed
    ]
    results = {}
    for name, sigma, lw, n_sys in tiers:
        aucs = []
        for s in range(n_seeds):
            obs, out = build_obs_df(
                truth_records, noise_sigma=sigma, include_lw=lw, noise_seed=SEED + 100 + s
            )
            y_true = out["outbreak"].to_numpy()
            y_score = (obs["ppi"].to_numpy() / 100.0).clip(0, 1)
            aucs.append(float(roc_auc_score(y_true, y_score)))
        results[name] = {
            "n_systems": n_sys,
            "roc_auc": round(float(np.mean(aucs)), 3),
            "roc_auc_std": round(float(np.std(aucs)), 3),
        }
    return results


# Destinations the recommender's export filters apply to, mapped to MarketSegment.
_EXPORT_DEST = {"EU": MarketSegment.EXPORT_EU, "GULF": MarketSegment.EXPORT_GULF}


def _mangoguard_would_exclude(ai: str, dest: str, cutoff: float) -> bool:
    """Faithful model of recommend.recommend()'s export filters: an AI is
    excluded if it is NOT MRL-listed for the destination market OR its
    smoothed RASFF rejection probability exceeds the cutoff.
    """
    seg = _EXPORT_DEST.get(dest)
    if seg is None:
        return False  # non-export destination: recommender does not RASFF/MRL-gate
    mrl_unlisted = mrl_loader.strictest_mrl(mrl_tables_for(seg), ai) is None
    rasff_high = rasff.rejection_probability(ai, dest) > cutoff
    return mrl_unlisted or rasff_high


def run_rasff(*, cutoff: float = 0.20) -> dict:
    """Faithful counterfactual: would each policy have prevented the rejection?

    MangoGuard prevents R(ai, dest) if it would NOT recommend ``ai`` for the
    export market (MRL non-listing OR RASFF probability). The ICAR-CISH /
    KVK calendars prevent R if they would not have prescribed ``ai`` that week.
    Restricted to export rows (EU/Gulf), which is where the recommender's
    residue filters apply. Also reports direct MRL-exclusion coverage.
    """
    rows = [r for r in rasff.all_rows() if r.destination in _EXPORT_DEST]
    icar = load_baseline("icar_cish")
    kvk = load_baseline("kvk_konkan")

    def calendar_would_prescribe(schedule, ai: str, iso_week: int) -> bool:
        return any(e.pesticide == ai and e.covers_week(iso_week) for e in schedule.entries)

    n = len(rows)
    mg_prevented = icar_prevented = kvk_prevented = 0
    distinct_ai = sorted({r.active_ingredient for r in rows})
    mrl_excluded_ai = [
        ai
        for ai in distinct_ai
        if mrl_loader.strictest_mrl(mrl_tables_for(MarketSegment.EXPORT_EU), ai) is None
    ]
    for r in rows:
        iso_week = datetime.fromisoformat(r.date).isocalendar().week
        if _mangoguard_would_exclude(r.active_ingredient, r.destination, cutoff):
            mg_prevented += 1
        if not calendar_would_prescribe(icar, r.active_ingredient, iso_week):
            icar_prevented += 1
        if not calendar_would_prescribe(kvk, r.active_ingredient, iso_week):
            kvk_prevented += 1

    mg_rate = mg_prevented / n
    icar_rate = icar_prevented / n
    kvk_rate = kvk_prevented / n
    return {
        "n_export_rejections": n,
        "prevention_rate_mangoguard": round(mg_rate, 3),
        "prevention_rate_icar_cish": round(icar_rate, 3),
        "prevention_rate_kvk_konkan": round(kvk_rate, 3),
        "rel_improvement_vs_icar_pct": round(100 * (mg_rate - icar_rate) / icar_rate, 1)
        if icar_rate
        else None,
        "rel_improvement_vs_kvk_pct": round(100 * (mg_rate - kvk_rate) / kvk_rate, 1)
        if kvk_rate
        else None,
        "n_distinct_ai": len(distinct_ai),
        "distinct_ai": distinct_ai,
        "n_mrl_excluded_ai_eu": len(mrl_excluded_ai),
        "mrl_excluded_ai_eu": mrl_excluded_ai,
        "cutoff": cutoff,
    }


def run_yield_price() -> dict:
    """Real XGBoost yield + price benchmark vs seasonal-mean, synthetic data."""
    rng = np.random.default_rng(SEED)
    n = 600
    # documented-relationship synthetic features
    ndvi_int = rng.uniform(40, 95, n)
    prev_yield = rng.uniform(2000, 6000, n)
    rainfall = rng.uniform(1800, 3500, n)
    age = rng.uniform(8, 40, n)
    gdd = rng.uniform(1500, 2600, n)
    season = rng.integers(2015, 2025, n)
    # true yield signal + noise (kg/acre)
    yield_true = (
        900
        + 28 * ndvi_int
        + 0.35 * prev_yield
        - 6 * np.abs(age - 22)
        + 0.4 * gdd
        + rng.normal(0, 350, n)
    )
    x_all = np.column_stack([ndvi_int, prev_yield, rainfall, age, gdd, season])
    split = int(0.8 * n)
    x_tr, x_te = x_all[:split], x_all[split:]
    ytr, yte = yield_true[:split], yield_true[split:]

    model = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=SEED)
    model.fit(x_tr, ytr)
    yield_mae = float(mean_absolute_error(yte, model.predict(x_te)))
    yield_base_mae = float(mean_absolute_error(yte, np.full_like(yte, ytr.mean())))

    # price: lagged AGMARKNET-style series
    weeks = 520
    base = 4000 + 1500 * np.sin(np.arange(weeks) / 8.0) + rng.normal(0, 250, weeks)
    feats, targs = [], []
    for t in range(4, weeks):
        feats.append([base[t - 1], base[t - 2], base[t - 3], base[t - 4]])
        targs.append(base[t])
    feats, targs = np.array(feats), np.array(targs)
    psplit = int(0.8 * len(feats))
    pm = XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, random_state=SEED)
    pm.fit(feats[:psplit], targs[:psplit])
    # convert quintal price to per-kg (AGMARKNET modal is INR/quintal -> /100)
    price_mae = float(mean_absolute_error(targs[psplit:], pm.predict(feats[psplit:])) / 100.0)
    price_base_mae = float(
        mean_absolute_error(targs[psplit:], np.full(len(targs) - psplit, targs[:psplit].mean()))
        / 100.0
    )

    return {
        "yield_mae_kg_per_acre": round(yield_mae, 1),
        "yield_baseline_mae_kg_per_acre": round(yield_base_mae, 1),
        "yield_improvement_pct": round(100 * (yield_base_mae - yield_mae) / yield_base_mae, 1),
        "price_mae_inr_per_kg": round(price_mae, 2),
        "price_baseline_mae_inr_per_kg": round(price_base_mae, 2),
        "price_improvement_pct": round(100 * (price_base_mae - price_mae) / price_base_mae, 1),
    }


def main() -> None:
    print("Generating ground-truth seasons (once)...")
    truth = generate_truth()
    print("Running retrospective backtest (real compute_ppi on simulated seasons)...")
    retro = run_retrospective(truth)
    print("Running connector-tier ablation (same seasons, decreasing sensor noise)...")
    tiers = run_connector_tiers(truth)
    print("Running RASFF counterfactual (faithful recommender exclusion)...")
    rasff_res = run_rasff()
    print("Running yield/price XGBoost benchmark...")
    yp = run_yield_price()

    metrics = {
        "_provenance": (
            "Computed by scripts/run_evaluation.py. Retrospective + tier study use "
            "simulated Konkan-climate weather with INDEPENDENT noisy outbreak labels "
            "(pipeline validation, not field accuracy). RASFF runs on compiled public "
            "rejection data. Yield/price on documented-relationship synthetic data. "
            "Live-portal curation + field-season validation are future work."
        ),
        "retrospective": retro,
        "connector_tiers": tiers,
        "rasff_counterfactual": rasff_res,
        "yield_price": yp,
    }
    path = ARTIFACTS / "eval_metrics.json"
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nWrote {path}\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
