# AamRakshak node firmware

ESP32 Arduino sketch for the leaf-wetness + microclimate node. It reads the
sensors, computes the Akem (2006) anthracnose infection risk **on-device**,
shows a risk band on the OLED, logs a daily CSV to flash, and (optionally)
POSTs JSON to the dashboard. Designed to run offline on a 18650 + small solar
panel via deep sleep.

## Libraries (Arduino IDE -> Library Manager)

| Library | Tested version | Used for |
|---|---|---|
| Adafruit SHT31 | 2.2.x | air temperature + humidity (I²C) |
| OneWire | 2.3.x | DS18B20 bus |
| DallasTemperature | 3.9.x | DS18B20 canopy/soil temp |
| Adafruit SSD1306 | 2.5.x | OLED driver |
| Adafruit GFX | 1.11.x | OLED text |
| ESP32 Arduino core | 3.0.x | WiFi, HTTPClient, LittleFS, deep sleep |

## Flashing

1. Arduino IDE -> Boards Manager -> install **esp32 by Espressif** (v3.0.x).
2. Board: **ESP32 Dev Module**. Tools -> Partition Scheme: any with LittleFS
   (e.g. "Default 4MB with spiffs"). Upload speed 921600.
3. Open `aamrakshak_node/aamrakshak_node.ino`. To run online, set `WIFI_SSID`,
   `WIFI_PASS`, `POST_URL` near the top; leave blank for fully offline use.
4. Upload. Open Serial Monitor at 115200 to watch the first readings.

## Calibration (leaf-wetness threshold)

The wet/dry decision uses `LEAFWET_WET_ADC_THRESHOLD` (default 2050). Calibrate
once per board:

1. Dry the grid with a cloth; note the ADC reading (Serial). Call it `adc_dry`.
2. Mist the grid with a spray bottle until evenly wet; note `adc_wet`.
3. Set the threshold to the midpoint `(adc_dry + adc_wet) / 2`.

Re-check every few weeks: DC excitation slowly corrodes the electrodes and
raises the wet reading (see the build guide's troubleshooting table). The
firmware already limits corrosion by energising the grid only during a reading.

## Model parity with the Python engine

The on-device model is the *same* maths and coefficients as
`src/aamrakshak/riskengine/anthracnose.py`. After flashing, you can sanity-check
your node by forcing these inputs (or just trust the shared formula). Expected
`risk_pct`:

| Inputs (Tmax, Tmin, RH_morning, leaf-wet h, sun h, wind m/s) | risk % |
|---|---|
| 31, 24, 94, 11, 4, 1.5  (humid wet day) | 39.2 |
| 34, 20, 60, 0, 10, 3    (dry clear day) | 0.3 |
| 30, 23, 82, 5, 7, 1.5   (moderate, dewy night) | 4.6 |
| 27, 27, 97, 13, 2, 1    (saturated overcast) | 100.0 |

The last row shows the saturated-microclimate limit: when Tmax == Tmin the
humid-thermal-ratio denominator is clamped, so a fully saturated day reads as
maximal risk.

## Risk bands shown on the OLED

- `LOW - SAFE` (< 12%) · `WATCH` (12–25%) · `HIGH - SPRAY WINDOW` (≥ 25%).
  The 25% spray threshold matches the dashboard's early-warning rule.
