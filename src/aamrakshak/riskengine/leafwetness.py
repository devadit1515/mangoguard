"""Leaf wetness: the decisive, hard-to-get signal.

Two pieces live here.

1. ``estimate_lw_hours_from_rh`` -- how a *free district feed* (which has no
   leaf-wetness sensor) is forced to GUESS leaf-wetness hours from relative
   humidity. This is the standard "RH threshold" proxy used in public agromet
   advisories. It is biased: it assumes wetness is a pure function of daytime
   RH and so misses dew on clear, calm nights (wet leaf, modest RH) and over-
   counts on humid-but-breezy days (high RH, dry leaf). The gap between this
   estimate and a real measurement is exactly what the node closes.

2. ``LeafWetnessSensor`` -- a model of the Rs.100 interdigitated resistive grid
   the node actually carries. A water film bridges the electrodes, dropping
   resistance; in the voltage divider that reads as a lower ADC count. The
   model captures the physics (sigmoid response), measurement noise, and the
   slow corrosion drift that DC excitation causes. It is used for the bench
   validation (success condition S3) and to add realistic node-grade noise to
   measured leaf wetness in the sensor-tier study.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --- 1. Free-feed estimate (no sensor) --------------------------------------

LW_RH_THRESHOLD_PCT = 88.0  # leaf assumed wet above this RH (advisory convention)
LW_RH_GAIN_HR_PER_PCT = 0.9  # hours of wetness gained per % RH above threshold
LW_MAX_HR = 16.0


def estimate_lw_hours_from_rh(rh_pct: float) -> float:
    """Estimate daily leaf-wetness hours from relative humidity alone.

    The proxy a free feed is stuck with. Monotone in RH, clipped to a day. It
    deliberately carries only RH's information -- it cannot recover the dew /
    rain component of real leaf wetness, which is why measuring beats guessing.
    """
    hours = LW_RH_GAIN_HR_PER_PCT * (rh_pct - LW_RH_THRESHOLD_PCT)
    return float(np.clip(hours, 0.0, LW_MAX_HR))


# --- 2. The DIY resistive leaf-wetness sensor -------------------------------

# ESP32 12-bit ADC: counts 0..4095. With the grid in the lower leg of a divider,
# a DRY (high-resistance) grid pulls the node high; a WET (low-resistance) grid
# pulls it low. These are bench-characterised anchors for the Rs.100 board.
ADC_DRY_MEAN = 2950.0
ADC_WET_MEAN = 1150.0
ADC_NOISE_SD = 470.0  # thermal + contact + contamination noise on a single read
ADC_RESPONSE_K = 0.18  # sigmoid steepness vs surface water fraction


@dataclass(frozen=True, slots=True)
class LeafWetnessSensor:
    """Model of the interdigitated resistive leaf-wetness grid.

    ``wetness_fraction`` in [0, 1] is the fraction of the grid bridged by a
    water film. ``drift_counts`` shifts the wet-state reading upward to model
    electrode corrosion over weeks of DC excitation (a real, documented limit;
    the firmware mitigates it with brief alternating-polarity excitation).
    """

    adc_dry: float = ADC_DRY_MEAN
    adc_wet: float = ADC_WET_MEAN
    noise_sd: float = ADC_NOISE_SD
    drift_counts: float = 0.0

    def read_adc(self, wetness_fraction: float, rng: np.random.Generator) -> float:
        """Single noisy ADC read for a given surface-water fraction."""
        # Sigmoid from dry (w=0) toward wet (w=1); +drift raises the wet end.
        s = 1.0 / (1.0 + np.exp(-(wetness_fraction - 0.5) / ADC_RESPONSE_K))
        clean = self.adc_dry + (self.adc_wet - self.adc_dry) * s + self.drift_counts * s
        return float(clean + rng.normal(0.0, self.noise_sd))

    def classify_wet(self, adc: float, threshold: float) -> bool:
        """Calibrated decision: below threshold (low resistance) == wet."""
        return adc < threshold

    def calibration_threshold(self) -> float:
        """Midpoint threshold from the two calibration anchors (wet/dry)."""
        return 0.5 * (self.adc_dry + self.adc_wet) + 0.5 * self.drift_counts

    def measured_lw_hours(
        self, true_lw_hours: float, rng: np.random.Generator, day_hours: float = 24.0
    ) -> float:
        """Node-measured leaf-wetness hours = hourly wet/dry calls integrated.

        The node samples through the day; each hour it calls wet or dry from the
        ADC. Measurement error in those calls makes the integrated duration a
        noisy-but-unbiased estimate of the truth -- far closer than the RH proxy.
        """
        n_hours = int(round(day_hours))
        wet_share = float(np.clip(true_lw_hours / day_hours, 0.0, 1.0))
        thr = self.calibration_threshold()
        wet_calls = 0
        for _ in range(n_hours):
            # Each hour is wet with probability wet_share; the sensor then reads
            # it with its own error. Surface-water fraction ~ high if wet.
            truly_wet = rng.random() < wet_share
            w = 0.85 if truly_wet else 0.12
            if self.classify_wet(self.read_adc(w, rng), thr):
                wet_calls += 1
        return float(wet_calls * day_hours / n_hours)
