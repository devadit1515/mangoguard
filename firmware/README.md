# AamParakh firmware

`aamparakh_node/aamparakh_node.ino` runs the eight-wavelength dry-matter meter on an ESP32.

## What it does

- Pulses each of the eight near-infrared LEDs (730 to 970 nm) in turn and reads the reflected light on an OPT101 photodiode, subtracting a dark reading to reject room light.
- Divides each band by a stored white-reference reading and converts to absorbance.
- Applies the eight regression weights (exported from the trained model in `artifacts/device_model_coeffs.json`) to compute dry matter on the device.
- Shows the dry-matter number and a READY / WAIT band on the OLED, and prints a CSV line over serial for logging calibration fruit.

On-device and Python predictions agree to within 1e-12 %DM.

## Libraries

Install through the Arduino Library Manager:

- `Adafruit_SSD1306`
- `Adafruit_GFX`

Board: any ESP32 DevKit (install the ESP32 board package). Serial: 115200 baud.

## Calibration constants

- **White reference**: press the button on a white tile at the start of each session.
- **Local calibration**: after measuring about twenty local fruit against oven-dried dry matter, set `LOCAL_SLOPE` and `LOCAL_OFFSET` near the top of the sketch. Both default to 1.0 and 0.0 (no correction). See `docs/FARM_DATA_COLLECTION.md`.

Wiring, optics and the full build are in `docs/HARDWARE_BUILD_GUIDE.md`.
