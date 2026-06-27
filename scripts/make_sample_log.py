"""Generate a realistic sample node log (one Konkan Alphonso block, one season).

Writes data/sample_node_log.csv in the exact format the firmware logs to flash,
so the dashboard has demo data out of the box. The values are the node-tier
sensor readings over a simulated 100-day risk season (clearly simulated).
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from aamrakshak.riskengine.anthracnose import AnthracnoseInputs, anthracnose_risk  # noqa: E402
from aamrakshak.riskengine.leafwetness import LeafWetnessSensor  # noqa: E402
from aamrakshak.sim.weather import REGIONS, _generate_block  # noqa: E402

SEED = 20260627
START = date(2026, 2, 1)  # Konkan Alphonso flowering-to-harvest window


def main() -> None:
    rng = np.random.default_rng(SEED)
    block = _generate_block(REGIONS["konkan_humid"], season=0, block=0, rng=rng)
    sensor = LeafWetnessSensor()
    noise = np.random.default_rng(SEED + 100)

    rows = ["node_id,date,t_max_c,t_min_c,rh_morning_pct,leaf_wetness_hr,risk_pct"]
    for _, r in block.iterrows():
        t_max = r["t_max"] + noise.normal(0, 0.4)
        t_min = r["t_min"] + noise.normal(0, 0.4)
        rh = float(np.clip(r["rh_morning"] + noise.normal(0, 2.5), 25, 100))
        lw = sensor.measured_lw_hours(r["leaf_wetness_true"], noise)
        risk = 100 * anthracnose_risk(
            AnthracnoseInputs(
                t_max_c=t_max,
                t_min_c=t_min,
                rh_morning_pct=rh,
                leaf_wetness_hr=lw,
                sunshine_hr=7.0,
                wind_speed_ms=1.5,
            )
        )
        d = START + timedelta(days=int(r["day"]))
        rows.append(f"AR-01,{d.isoformat()},{t_max:.1f},{t_min:.1f},{rh:.0f},{lw:.1f},{risk:.1f}")

    out = ROOT / "data" / "sample_node_log.csv"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(rows) - 1} days)")


if __name__ == "__main__":
    main()
