"""Turning a full research spectrum into what a cheap spectral sensor would see.

A research spectrometer reports reflectance every 3 nm. A hobby spectral chip
reports one number per filtered channel, each channel a roughly Gaussian window of
about 20 nm full width at half maximum centred on a fixed wavelength. To find out
what such a chip would measure on the same fruit, we integrate the research
spectrum through each channel's response. This is the standard way to emulate a
multiband sensor from hyperspectral data, and it lets us ask the cost-of-cheap
question on real spectra before committing to hardware.

Channel centres and widths are taken from the AMS AS7265x and AS7263 datasheets.
"""

from __future__ import annotations

import numpy as np

# (centre_nm, fwhm_nm) per channel.
AS7265X_BANDS = [
    (410, 20),
    (435, 20),
    (460, 20),
    (485, 20),
    (510, 20),
    (535, 20),
    (560, 20),
    (585, 20),
    (610, 20),
    (645, 20),
    (680, 20),
    (705, 20),
    (730, 20),
    (760, 20),
    (810, 20),
    (860, 20),
    (900, 20),
    (940, 20),
]
AS7263_BANDS = [(610, 20), (680, 20), (730, 20), (760, 20), (810, 20), (860, 20)]

SENSORS = {"AS7265x": AS7265X_BANDS, "AS7263": AS7263_BANDS}

# The purpose-built AamParakh device: eight discrete near-infrared LEDs at wavelengths
# a student can buy, chosen for mango dry matter. Each LED emits over roughly 30 nm.
# These are what the analysis of the public benchmark selected (all silicon-detectable,
# <=970 nm), unlike the general-purpose chips above whose bands sit mostly in the visible.
DEVICE_BANDS = [
    (730, 30),
    (760, 30),
    (810, 30),
    (850, 30),
    (880, 30),
    (910, 30),
    (940, 30),
    (970, 30),
]
NIR_LED_PALETTE = [c for c, _ in DEVICE_BANDS]

_FWHM_TO_SIGMA = 1.0 / 2.3548200450309493  # a Gaussian's sigma = FWHM / (2*sqrt(2 ln2))


def _channel_weights(wl: np.ndarray, centre: float, fwhm: float) -> np.ndarray:
    sigma = fwhm * _FWHM_TO_SIGMA
    w = np.exp(-0.5 * ((wl - centre) / sigma) ** 2)
    total = w.sum()
    if total == 0:
        raise ValueError(f"channel {centre} nm falls outside the spectrum {wl.min()}-{wl.max()} nm")
    return w / total


def band_response_matrix(wl: np.ndarray, bands) -> np.ndarray:
    """(n_bands, n_wl) matrix of normalised channel responses."""
    return np.vstack([_channel_weights(wl, c, f) for c, f in bands])


def simulate_bands(spectra: np.ndarray, wl: np.ndarray, bands) -> np.ndarray:
    """(n_samples, n_bands) sensor readings from full spectra."""
    return spectra @ band_response_matrix(wl, bands).T


def band_centres(bands) -> np.ndarray:
    return np.array([c for c, _ in bands])
