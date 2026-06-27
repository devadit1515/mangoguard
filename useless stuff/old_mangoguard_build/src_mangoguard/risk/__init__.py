"""Disease-risk models: pure-function pathogen-pressure scoring.

Three pathogens covered:

- :mod:`anthracnose` -- Akem (2006) humid-thermal-ratio logistic regression.
- :mod:`powdery_mildew` -- temperature-band x RH-window Gaussian product.
- :mod:`hopper` -- CROPSAP regional pressure x local-temperature multiplier.

These modules are intentionally pure functions / dataclasses with no
FeedStore coupling -- they take primitive inputs and return floats in
[0, 1]. The :mod:`ppi` module combines them into a per-block-per-day
Pest Pressure Index that DOES read from the FeedStore.

All coefficients have a documented source. Where defaults are not
literature-pinned (e.g., the powdery-mildew Gaussian widths), the
default is documented as "engineering estimate" and is overridable via
function kwargs so the calibration notebook can swap in fitted values.
"""
