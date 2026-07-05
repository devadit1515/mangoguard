# AamParakh hardware build guide

This guide builds the eight-wavelength near-infrared mango dry-matter meter from scratch. It assumes you can solder and have used an Arduino or ESP32 before. Total build time is about eight hours spread over a weekend, most of it patient wiring and calibration rather than anything difficult. The parts come to roughly ₹2,300.

The meter works by shining eight near-infrared LEDs, one at a time, onto a mango and measuring how much of each colour bounces back with a single light sensor. Fruit with more dry matter absorbs and reflects these wavelengths differently, and the eight numbers together predict the dry-matter percentage. The wavelengths were not chosen by guesswork; they are the ones a search over 11,691 real fruit found to carry the signal (see the report, Section 5.3).

---

## 1. Bill of materials

| Component | Qty | Notes |
|---|---|---|
| ESP32 DevKit V1 | 1 | Any ESP32 board with a spare ADC pin and eight free GPIOs |
| Near-infrared LEDs: 730, 760, 810, 850, 880, 910, 940, 970 nm | 1 each | 5 mm through-hole; buy from an optoelectronics supplier by peak wavelength |
| OPT101 photodiode-amplifier | 1 | A photodiode with a built-in amplifier; simplest reliable detector |
| SSD1306 0.96" OLED (I2C) | 1 | The offline readout |
| NPN transistors (2N2222 or similar) | 8 | One per LED, to switch it from a GPIO |
| Resistors: 220 Ω (×8, LED current), 1 kΩ (×8, transistor base) | 16 | |
| Perfboard, hook-up wire, header pins | 1 lot | |
| Opaque tube or 3D-printed housing + white reference tile | 1 | Holds the LEDs and sensor against the fruit and blocks room light |
| USB power bank + cable | 1 | Field power |

The eight LED wavelengths are the heart of the design. If a supplier is out of one, 940 nm is the only one that is truly fixed (it is the cheapest and most available); the others can shift by 10 to 20 nm at a small cost in accuracy, but do not substitute anything below 700 nm or above 980 nm.

---

## 2. Wiring

The idea is simple. Each LED is switched by one transistor driven by one ESP32 pin, so the firmware can turn each wavelength on alone. The OPT101 sits in the middle of the ring of LEDs and its output goes to one analog input.

**LED drivers (repeat for all eight).** For LED *i*:

```
ESP32 GPIO --[1 kΩ]-- transistor base
transistor emitter -- GND
transistor collector -- LED cathode
LED anode --[220 Ω]-- 3V3
```

Use these GPIOs, in wavelength order, to match the firmware:

| LED (nm) | 730 | 760 | 810 | 850 | 880 | 910 | 940 | 970 |
|---|---|---|---|---|---|---|---|---|
| GPIO | 13 | 12 | 14 | 27 | 26 | 25 | 33 | 32 |

**Sensor.** OPT101 output to GPIO 34 (an input-only ADC pin), its supply to 3V3 and ground to GND.

**Display.** SSD1306 SDA to GPIO 21, SCL to GPIO 22, power to 3V3 and GND.

**Button.** A push button from GPIO 4 to GND, used to capture the white reference. The firmware enables the internal pull-up, so no extra resistor is needed.

---

## 3. Optics: the most important physical step

The measurement lives or dies on geometry, not on the electronics. The eight LEDs and the sensor must sit at the end of a short opaque tube that presses flat against the fruit and keeps room light out. Arrange the LEDs in a ring around the OPT101 so each one lights the same patch of fruit the sensor sees. Keep the LED-to-fruit and sensor-to-fruit distances the same for every reading; a 3D-printed housing that fixes these distances is worth the effort, because a hand-held gap that changes between fruit is the single largest source of error.

Paint or line the inside of the tube matte black so stray reflections do not reach the sensor. Cut a small white tile (a piece of white PTFE or matte white plastic) to hold against the aperture when you set the white reference.

---

## 4. Flashing the firmware

1. Install the Arduino IDE and the ESP32 board package.
2. Install the `Adafruit_SSD1306` and `Adafruit_GFX` libraries from the Library Manager.
3. Open `firmware/aamparakh_node/aamparakh_node.ino`, select your ESP32 board, and upload.
4. Open the Serial Monitor at 115200 baud. You should see the CSV header line and, once you take a reading, a line of eight band values and a dry-matter estimate.

The eight model weights are already in the firmware, exported from the trained model (`artifacts/device_model_coeffs.json`), so the meter computes dry matter on the device with no laptop needed. On-device and Python predictions agree to within a rounding error.

---

## 5. Calibration

Two calibrations matter, and they are different.

**White reference (every session).** Hold the white tile against the aperture and press the button. This tells the meter what "all the light comes back" looks like, so it can turn raw sensor readings into reflectance. Redo it whenever the ambient light changes or every twenty fruit.

**Local calibration (once per cultivar).** The model was trained on Australian fruit, so on Alphonso or Kesar it reads with a small, consistent bias. Measure about twenty local fruit against oven-dried dry matter (the procedure is in `FARM_DATA_COLLECTION.md`), fit a single slope and offset, and set `LOCAL_SLOPE` and `LOCAL_OFFSET` at the top of the firmware. This one step is what turns a biased reading into an accurate one, and the report (Section 5.6) shows it cuts the error by more than half.

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Every band reads near zero | LED not lighting, or sensor not powered | Check the transistor wiring; near-infrared LEDs look dark to the eye, so test with a phone camera, which sees the glow |
| Readings jump between fruit | Changing geometry or stray light | Use the housing; keep pressure and distance constant; redo the white reference |
| Dry matter reads far too high or low | White reference not set, or local calibration wrong | Set the white reference; redo the local slope and offset |
| Display blank | I2C address or wiring | Confirm the SSD1306 is at address 0x3C and SDA/SCL are on GPIO 21/22 |

---

## 7. Safety

The whole device runs at 3.3 to 5 volts from a USB power bank; there is no mains and no shock hazard. Near-infrared LEDs are invisible but low-power; point them into the fruit housing and do not stare into the aperture. Take the usual care with a hot soldering iron and ventilate the room while soldering.
