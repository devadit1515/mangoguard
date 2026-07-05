"""AamParakh: low-cost multispectral estimation of mango dry matter content (DMC).

The package answers one question: how far can the wavelength count of a mango
dry-matter model be collapsed, from a full research spectrum down to the handful
of bands a cheap ESP32 spectral sensor provides, before harvest calls stop being
reliable? Every number is produced from the public Anderson-Walsh mango NIR
benchmark (real spectra) plus a clearly-labelled on-farm validation set.
"""

__all__ = ["data", "sensors", "models", "evaluate", "farm"]
