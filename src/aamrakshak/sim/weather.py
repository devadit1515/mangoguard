"""Grounded synthetic weather for mango risk seasons across regions.

The generator produces a daily panel (region x season x block x day) for the
~100-day pre-harvest window when anthracnose pressure builds. It is anchored on
documented climate normals:

- *konkan_humid* (Ratnagiri / Konkan, Alphonso): warm and very humid through
  the pre-monsoon; high leaf wetness, modest diurnal range.
- *gujarat_drier* (Saurashtra, Kesar): hotter and markedly drier; big diurnal
  swing, much less leaf wetness -- the contrasting region for the
  generalisation test (success condition S5).

Two design choices make the later sensor-tier comparison meaningful and honest:

1. **Leaf wetness carries information beyond RH.** ``lw_true`` has a dew
   component (clear, calm nights wet the leaf even when daytime RH is moderate)
   that is *independent* of morning RH. A free feed that estimates wetness from
   RH alone cannot recover it; a node that measures it can.
2. **Blocks differ; districts smooth.** Each block has a small persistent
   microclimate offset. The free "district feed" is the across-block daily mean
   plus coarse measurement error, so it averages away exactly the local signal
   the node keeps.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SEASON_DAYS = 100


@dataclass(frozen=True, slots=True)
class RegionProfile:
    """Climate parameters for one growing region over the risk season."""

    name: str
    variety: str
    t_base_c: float  # season-start mean temperature
    t_rise_c: float  # mean temperature rise across the season
    diurnal_lo: float
    diurnal_hi: float
    humid_base: float  # humid-spell probability at season start
    humid_rise: float  # increase by season end
    rh_humid: tuple[float, float]
    rh_dry: tuple[float, float]
    lw_humid: tuple[float, float]  # leaf-wetness hours on a humid day
    dew_prob: float  # chance of a dewy night on a non-humid day
    lw_dew: tuple[float, float]  # leaf-wetness hours from dew
    sun_humid: tuple[float, float]
    sun_dry: tuple[float, float]
    wind: tuple[float, float]


REGIONS: dict[str, RegionProfile] = {
    "konkan_humid": RegionProfile(
        name="konkan_humid",
        variety="alphonso",
        t_base_c=26.0,
        t_rise_c=6.0,
        diurnal_lo=6.0,
        diurnal_hi=11.0,
        humid_base=0.30,
        humid_rise=0.45,
        rh_humid=(85.0, 96.0),
        rh_dry=(62.0, 78.0),
        lw_humid=(8.0, 13.0),
        dew_prob=0.45,
        lw_dew=(3.0, 7.0),
        sun_humid=(3.0, 6.0),
        sun_dry=(7.0, 10.0),
        wind=(0.5, 3.5),
    ),
    "gujarat_drier": RegionProfile(
        name="gujarat_drier",
        variety="kesar",
        t_base_c=30.0,
        t_rise_c=6.0,
        diurnal_lo=9.0,
        diurnal_hi=14.0,
        humid_base=0.12,
        humid_rise=0.28,
        rh_humid=(72.0, 86.0),
        rh_dry=(40.0, 60.0),
        lw_humid=(5.0, 9.0),
        dew_prob=0.20,
        lw_dew=(0.0, 3.0),
        sun_humid=(5.0, 8.0),
        sun_dry=(9.0, 12.0),
        wind=(1.0, 4.5),
    ),
}


def _generate_block(
    region: RegionProfile,
    season: int,
    block: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """One block's daily weather for one season."""
    days = np.arange(SEASON_DAYS)
    f = days / SEASON_DAYS  # 0 at season start, ~1 at harvest

    # Persistent block microclimate offsets (a valley block runs more humid).
    rh_offset = rng.normal(0.0, 3.0)
    lw_offset = rng.normal(0.0, 0.8)

    t_mean = region.t_base_c + region.t_rise_c * f + rng.normal(0.0, 1.0, SEASON_DAYS)
    diurnal = rng.uniform(region.diurnal_lo, region.diurnal_hi, SEASON_DAYS)
    t_max = t_mean + diurnal / 2.0
    t_min = t_mean - diurnal / 2.0

    humid_p = np.clip(region.humid_base + region.humid_rise * f, 0.0, 0.95)
    humid_spell = rng.random(SEASON_DAYS) < humid_p

    rh = (
        np.where(
            humid_spell,
            rng.uniform(*region.rh_humid, SEASON_DAYS),
            rng.uniform(*region.rh_dry, SEASON_DAYS),
        )
        + rh_offset
    )
    rh = np.clip(rh, 25.0, 100.0)

    # Leaf wetness: humid-day film OR independent dew on a calm clear night.
    dewy = (~humid_spell) & (rng.random(SEASON_DAYS) < region.dew_prob)
    lw = np.where(humid_spell, rng.uniform(*region.lw_humid, SEASON_DAYS), 0.0)
    lw = np.where(dewy, rng.uniform(*region.lw_dew, SEASON_DAYS), lw)
    lw = np.clip(lw + lw_offset, 0.0, 18.0)

    sunshine = np.where(
        humid_spell,
        rng.uniform(*region.sun_humid, SEASON_DAYS),
        rng.uniform(*region.sun_dry, SEASON_DAYS),
    )
    wind = rng.uniform(*region.wind, SEASON_DAYS)
    precip = np.where(humid_spell, rng.exponential(6.0, SEASON_DAYS), 0.0)

    return pd.DataFrame(
        {
            "region": region.name,
            "variety": region.variety,
            "season": season,
            "block": block,
            "day": days,
            "f": f,
            "t_max": t_max,
            "t_min": t_min,
            "rh_morning": rh,
            "leaf_wetness_true": lw,
            "sunshine": sunshine,
            "wind": wind,
            "precip": precip,
        }
    )


def generate_panel(
    seed: int,
    regions: list[str] | None = None,
    n_seasons: int = 3,
    n_blocks: int = 4,
) -> pd.DataFrame:
    """Generate the full ground-truth weather panel and the district feed.

    Returns a long DataFrame with one row per (region, season, block, day),
    plus ``district_*`` columns: the across-block daily mean for the region-
    season-day with added coarse measurement error, standing in for a free
    district forecast that cannot see a single block.
    """
    regions = regions or list(REGIONS)
    rng = np.random.default_rng(seed)
    frames = [
        _generate_block(REGIONS[r], s, b, rng)
        for r in regions
        for s in range(n_seasons)
        for b in range(n_blocks)
    ]
    panel = pd.concat(frames, ignore_index=True)

    # District feed = mean across blocks per (region, season, day) + coarse noise.
    keys = ["region", "season", "day"]
    dist = (
        panel.groupby(keys)[["t_max", "t_min", "rh_morning", "sunshine", "wind"]]
        .mean()
        .reset_index()
        .rename(
            columns={
                "t_max": "district_t_max",
                "t_min": "district_t_min",
                "rh_morning": "district_rh",
                "sunshine": "district_sunshine",
                "wind": "district_wind",
            }
        )
    )
    panel = panel.merge(dist, on=keys, how="left")
    # Coarse forecast error on the district feed (deterministic given the seed).
    dn = np.random.default_rng(seed + 7)
    n = len(panel)
    panel["district_t_max"] += dn.normal(0.0, 1.3, n)
    panel["district_t_min"] += dn.normal(0.0, 1.3, n)
    panel["district_rh"] = np.clip(panel["district_rh"] + dn.normal(0.0, 5.0, n), 25.0, 100.0)
    panel["district_sunshine"] = np.clip(
        panel["district_sunshine"] + dn.normal(0.0, 1.0, n), 0.0, 13.0
    )
    panel["district_wind"] = np.clip(panel["district_wind"] + dn.normal(0.0, 0.8, n), 0.0, None)
    return panel
