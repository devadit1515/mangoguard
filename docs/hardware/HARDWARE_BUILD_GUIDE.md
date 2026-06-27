# AamRakshak node — hardware build guide

A self-contained manual to build the leaf-wetness + microclimate node in **about
8 hours** with basic electronics skills (you can solder header pins and follow a
wiring table). The finished node measures air temperature and humidity, canopy
temperature, and leaf-surface wetness; computes anthracnose infection risk
on-device; shows a risk band on a small screen; and logs / uploads the data.

> Build it once, place it in the orchard canopy, and it tells you "spray / watch
> / safe" each day — no phone signal needed. Total parts cost ≈ **₹1,900**,
> versus ₹40,000+ for a commercial agro-met station that measures the same things.

---

## 1. What it is, and why this design

The single signal that makes mango anthracnose predictable is **leaf wetness** —
how many hours the leaf surface stays wet, which is when the fungus germinates and
infects. Commercial weather stations measure it but cost more than a smallholder
will ever spend. So the design goal was: get a trustworthy leaf-wetness signal
(plus the temperature and humidity the infection model needs) from the cheapest
parts that still work, and do the thinking on the device so it works offline.

Three choices follow from that:

- **A DIY resistive leaf-wetness grid**, not a commercial sensor. A water film
  bridges interlocking electrodes and drops the resistance; the ESP32 reads that
  as a voltage. It costs ~₹100 instead of ~₹10,000. The trade-off is corrosion
  drift, which the firmware and a simple recalibration handle (§7, §8).
- **On-device risk (edge compute)**, not cloud-only. The ESP32 runs the Akem
  model itself and drives an OLED, so a grower with no mobile data still gets a
  decision. WiFi upload is optional.
- **Solar + battery + deep sleep**, so it survives in a tree for a season without
  wiring or daily charging.

---

## 2. Bill of materials

Prices are indicative India retail (Robu.in / RoboticsDNA / Amazon India), 2026.
A UK/global fallback in brackets where the part name differs.

| # | Component | Spec | Qty | ₹ each | ₹ total | Where |
|---|---|---|---|---|---|---|
| 1 | ESP32 DevKit V1 | 38-pin, USB (CP2102) | 1 | 400 | 400 | Robu.in / Amazon.in |
| 2 | SHT31 module | I²C, T ±0.3 °C, RH ±2% | 1 | 250 | 250 | Robu.in |
| 3 | Leaf-wetness grid | interdigitated resistive board (or a repurposed "rain" board) | 1 | 100 | 100 | Robu.in / local |
| 4 | DS18B20 (waterproof) | 1-Wire temp probe, 1 m lead | 1 | 130 | 130 | Robu.in |
| 5 | SSD1306 OLED | 0.96″ 128×64, I²C | 1 | 160 | 160 | Robu.in |
| 6 | TP4056 module | USB-C Li-ion charger + protection | 1 | 40 | 40 | Robu.in |
| 7 | 18650 cell | 2600 mAh, protected | 1 | 150 | 150 | local / Robu.in |
| 8 | 18650 holder | single cell | 1 | 30 | 30 | Robu.in |
| 9 | Solar panel | 6 V 1 W mini | 1 | 180 | 180 | Robu.in |
| 10 | Enclosure | IP65 ~100×68×50 mm | 1 | 180 | 180 | Amazon.in |
| 11 | Radiation shield | stacked plastic plates (DIY) or 3D print | 1 | 120 | 120 | local / print |
| 12 | Resistor 4.7 kΩ | DS18B20 pull-up | 1 | 2 | 5 | local |
| 13 | Resistor 10 kΩ | leaf-wetness divider | 1 | 2 | 5 | local |
| 14 | Perfboard + headers + hookup wire + cable glands | — | 1 lot | 150 | 150 | local |
| | **Total** | | | | **≈ 1,900** | |

A "bench-only" build (skip items 6–11, power over USB) costs ≈ **₹1,300**.

**Why each part, and the alternative considered**

- **ESP32** over Arduino Uno: built-in WiFi, a 12-bit ADC for the leaf-wetness
  divider, and deep sleep for battery life — all on one ₹400 board.
- **SHT31** over the cheaper DHT22: the humid-thermal ratio is sensitive to RH
  accuracy, and DHT22 is noisy and slow. SHT31 is the cheapest *accurate* digital
  T/RH part. (DHT22 works as a ₹150 budget substitute if needed.)
- **DS18B20** over a thermistor: digital, waterproof, no calibration, daisy-chainable.
- **Resistive leaf-wetness grid** over a commercial dielectric sensor: 1% of the
  cost. Over a capacitive DIY sensor: simpler (a plain ADC read, no oscillator) —
  at the cost of corrosion drift, which we mitigate rather than eliminate.
- **OLED**: the offline-first decision display; the whole point is no dependence
  on a phone.
- **Solar + TP4056 + 18650**: a season of unattended operation. Alternative (a
  USB power bank) needs swapping and fails in the field.

---

## 3. Tools

Soldering iron + solder, wire cutters/strippers, a small Phillips screwdriver, a
multimeter (for checking continuity and the divider voltage), a drill or hot
nail (for cable-gland holes in the enclosure), a spray bottle of water (for
calibration), and a computer with the Arduino IDE.

---

## 4. Wiring

All logic is **3.3 V** — the ESP32's GPIO pins are **not 5 V tolerant**, so power
every sensor from the board's 3V3 pin, never 5 V. The ADC pin reads 0–3.3 V.

| Component | Pin → ESP32 | Notes |
|---|---|---|
| SHT31 | VCC→3V3, GND→GND, SDA→GPIO21, SCL→GPIO22 | I²C address 0x44 |
| SSD1306 OLED | VCC→3V3, GND→GND, SDA→GPIO21, SCL→GPIO22 | shares the I²C bus; address 0x3C |
| DS18B20 | VCC→3V3, GND→GND, DATA→GPIO4 | **4.7 kΩ between DATA and 3V3** (pull-up) |
| Leaf-wetness grid | see divider below | excitation on GPIO25, read on GPIO34 |
| Power | TP4056 OUT+ → ESP32 5V/VIN, OUT− → GND | 18650 on TP4056 B+/B−; solar on TP4056 IN |

**Leaf-wetness divider** (energised only during a reading, to slow corrosion):

```
GPIO25 ──[ 10 kΩ ]──┬── GPIO34 (ADC)
                    │
                 [ grid electrode A ]
                 [ grid electrode B ]
                    │
                   GND
```

When the grid is **dry** its resistance is high, so GPIO34 sits near 3.3 V (high
ADC count). When **wet**, the resistance drops and GPIO34 falls toward 0 V (low
ADC count). The firmware drives GPIO25 high only for the ~40 ms of a reading, so
the electrodes are not under constant DC (the main cause of corrosion).

See `artifacts/figs/fig02_hardware.png` for the block diagram.

---

## 5. Assembly, step by step (≈ 8 h total)

| Step | Task | Time |
|---|---|---|
| 1 | Lay out and identify all parts; read this guide through once | 0.5 h |
| 2 | Solder header pins to the ESP32 (if not pre-soldered); plan the perfboard layout | 0.75 h |
| 3 | Wire SHT31 + OLED on the I²C bus; power up and confirm both are detected | 1.0 h |
| 4 | Wire DS18B20 with its 4.7 kΩ pull-up; confirm a sensible temperature | 0.5 h |
| 5 | Build the leaf-wetness divider; wire the grid; check the ADC swings between wet and dry by hand | 1.0 h |
| 6 | Flash the firmware (§6); watch the Serial Monitor for live readings | 1.0 h |
| 7 | Calibrate the leaf-wetness threshold (§7) | 0.5 h |
| 8 | Wire TP4056 + 18650 + solar; confirm it charges and the node runs on battery | 1.0 h |
| 9 | Build the radiation shield, mount everything in the enclosure, fit cable glands and a drip loop | 1.25 h |
| 10 | Final end-to-end test in shade; check the OLED risk band and the flash log | 0.5 h |
| | **Total** | **8.0 h** |

The radiation shield (step 9) matters: an air-temperature sensor in direct sun
reads several degrees too high and would corrupt the humid-thermal ratio. Stack
4–5 white plastic plates (or saucers) with spacers so air flows through but
sunlight does not reach the SHT31. Mount the leaf-wetness grid at a slight angle
in the canopy so water runs off the way it does off a real leaf.

---

## 6. Firmware

Full instructions and the sketch are in `firmware/` (see `firmware/README.md`).
In brief: install the Arduino IDE, add the **esp32** board package, install the
five libraries listed there, open `firmware/aamrakshak_node/aamrakshak_node.ino`,
set WiFi/upload values (or leave blank for offline use), and upload to "ESP32 Dev
Module". The on-device model is identical to the project's Python risk engine; a
parity table in the firmware README lets you verify your node.

---

## 7. Calibration

1. Open the Serial Monitor (115200 baud). Dry the grid with a cloth and note the
   ADC value: `adc_dry` (expect a high number, ~2900).
2. Mist the grid evenly with the spray bottle and note `adc_wet` (a low number,
   ~1150).
3. Set `LEAFWET_WET_ADC_THRESHOLD` in the sketch to the midpoint
   `(adc_dry + adc_wet) / 2` and re-upload.
4. The SHT31 and DS18B20 are factory-calibrated; no step needed. Sanity-check the
   SHT31 RH against a second hygrometer if you have one.

How the reading feeds the software: each daily reading becomes a `Reading`
record (`node_id, date, t_max_c, t_min_c, rh_morning_pct, leaf_wetness_hr,
risk_pct`) — the exact schema the dashboard and `src/aamrakshak/io/ingest.py`
parse. Upload the flash CSV, or let the node POST JSON.

---

## 8. Testing and troubleshooting

**Expected readings (shade, daytime):** air temp 22–38 °C, RH 40–98%, leaf-wet
ADC high when dry / low when misted, daily risk 0–100% (high after a humid,
long-wetness night).

**End-to-end test:** mist the grid, wait for the next sample, and confirm the
OLED leaf-wetness hours rise and the risk band moves toward WATCH/HIGH.

| Symptom | Likely cause | Fix |
|---|---|---|
| OLED blank | wrong I²C address / wiring | confirm 0x3C; check SDA/SCL not swapped |
| SHT31 not found | address / wiring | confirm 0x44; both devices share SDA/SCL |
| DS18B20 reads −127 °C | missing pull-up | add the 4.7 kΩ resistor DATA→3V3 |
| Leaf-wet always "wet" or "dry" | bad threshold / corrosion | recalibrate (§7); clean or replace the grid |
| Wet readings drift up over weeks | electrode corrosion | recalibrate; switch to a capacitive grid for v2 |
| ESP32 not detected by PC | USB driver | install the CP2102 driver |
| Random reboots | brownout under WiFi | check battery/solar; add a 470 µF cap across 3V3/GND |

The corrosion drift is real and documented: in bench testing, wet/dry accuracy
fell from ~99% fresh to ~68% after eight weeks of continuous DC excitation, but a
simple monthly recalibration held it above ~95% (`artifacts/figs/fig09_sensor_drift.png`).

---

## 9. Photographs to capture (for your own appendix)

Each sensor wired to the ESP32; the breadboard prototype; the Serial Monitor
showing live readings; the spray-bottle calibration; the assembled radiation
shield; the closed enclosure with cable glands; and the node mounted in the
orchard canopy.

---

## 10. Safety

- **Battery:** use a *protected* 18650 and the TP4056 (it has over-charge /
  over-discharge / short protection). Observe polarity. Never puncture or short a
  Li-ion cell; charge where a fire could not spread.
- **Soldering:** work in ventilation, rest the hot iron on its stand, wash hands
  after handling solder.
- **Electrical:** the whole node runs at 3.3–4.2 V — there is no mains voltage and
  no shock hazard. Keep the ADC input within 0–3.3 V.
- **Weatherproofing:** seal the enclosure (IP65), use cable glands, and leave a
  downward drip loop on every cable so water cannot track inside. Keep the SHT31
  vented but shaded.
- **Field use:** mount the node away from the direct path of pesticide spray, and
  wear gloves when servicing it in a recently sprayed orchard. Secure it so it
  cannot fall onto a person below.
