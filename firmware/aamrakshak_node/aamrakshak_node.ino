/*
 * AamRakshak node firmware  (ESP32 Arduino)
 * -----------------------------------------
 * A sub-Rs.2,000 leaf-wetness + microclimate node that predicts mango
 * anthracnose infection risk ON-DEVICE and shows it on an OLED, so a grower
 * with no phone signal still gets "spray / watch / safe" guidance.
 *
 * What it does each wake cycle (deep-sleep between cycles to save battery):
 *   1. read air temperature + humidity (SHT31, I2C)
 *   2. read canopy/soil temperature (DS18B20, 1-Wire)
 *   3. read leaf-surface wetness (DIY interdigitated resistive grid -> ADC),
 *      energised only briefly to limit electrode corrosion
 *   4. update the day's running Tmax / Tmin / morning-RH / leaf-wetness-hours
 *      (kept in RTC memory so they survive deep sleep)
 *   5. once per day, evaluate the Akem (2006) humid-thermal-ratio infection
 *      model -- the SAME maths and coefficients as the Python risk engine
 *      (src/aamrakshak/riskengine/anthracnose.py) -- show the risk band on the
 *      OLED, append a CSV line to flash, and optionally POST JSON over WiFi.
 *
 * Libraries (install via Arduino Library Manager; tested versions in comments):
 *   - Adafruit SHT31        v2.2.x
 *   - OneWire               v2.3.x   + DallasTemperature v3.9.x
 *   - Adafruit SSD1306      v2.5.x   + Adafruit GFX v1.11.x
 *   - (ESP32 Arduino core   v3.0.x  provides WiFi, HTTPClient, LittleFS, esp_sleep)
 *
 * Board: "ESP32 Dev Module". Flash size 4MB, partition with LittleFS.
 */

#include <Adafruit_SHT31.h>
#include <Adafruit_SSD1306.h>
#include <DallasTemperature.h>
#include <HTTPClient.h>
#include <LittleFS.h>
#include <OneWire.h>
#include <WiFi.h>
#include <math.h>

// ---------------------------------------------------------------- pin map ----
#define PIN_LEAFWET_ADC   34   // ADC1_CH6: leaf-wetness divider output (input-only pin)
#define PIN_LEAFWET_PWR   25   // drives the divider HIGH only during a reading
#define PIN_ONEWIRE       4    // DS18B20 data
#define PIN_SDA           21   // I2C (SHT31 + OLED)
#define PIN_SCL           22

// ---------------------------------------------------------------- config -----
static const char*  WIFI_SSID     = "";     // leave blank to run fully offline
static const char*  WIFI_PASS     = "";
static const char*  POST_URL      = "";     // e.g. http://192.168.1.50:8000/ingest
static const char*  NODE_ID       = "AR-01";

static const uint64_t SAMPLE_INTERVAL_S = 15 * 60;   // wake every 15 min
static const int      SAMPLES_PER_DAY   = (24 * 3600) / SAMPLE_INTERVAL_S; // 96
static const float    LEAFWET_WET_ADC_THRESHOLD = 2050.0; // below = wet (calibrate!)
static const float    SPRAY_RISK_PCT    = 25.0;      // matches the dashboard rule
static const float    WATCH_RISK_PCT    = 12.0;

// Akem (2006) coefficients -- identical to the Python DEFAULT_COEFFS.
static const float B0 = -4.2f, B_HTR = 0.085f, B_LW = 0.32f, B_SUN = -0.18f, B_WIND = -0.12f;
static const float MIN_DIURNAL_RANGE_C = 0.1f;
// The node has no light/wind sensor; it uses neutral climatological defaults
// (the same fallbacks as io/ingest.py). A deployment can override from a feed.
static const float DEFAULT_SUNSHINE_HR = 7.0f, DEFAULT_WIND_MS = 1.5f;

// ------------------------------------------------- state across deep sleep ---
RTC_DATA_ATTR int   rtc_sample_count = 0;
RTC_DATA_ATTR float rtc_t_max        = -100.0f;
RTC_DATA_ATTR float rtc_t_min        =  100.0f;
RTC_DATA_ATTR float rtc_rh_morning   = -1.0f;   // RH captured in the morning window
RTC_DATA_ATTR int   rtc_wet_samples  = 0;       // count of "wet" readings today
RTC_DATA_ATTR float rtc_last_risk    = 0.0f;

Adafruit_SHT31     sht = Adafruit_SHT31();
OneWire            oneWire(PIN_ONEWIRE);
DallasTemperature  ds18b20(&oneWire);
Adafruit_SSD1306   oled(128, 64, &Wire, -1);

// ------------------------------------------------------------- model maths ---
// Numerically stable logistic, identical to the Python implementation.
static float sigmoid(float z) {
  if (z >= 0) return 1.0f / (1.0f + expf(-z));
  float ez = expf(z);
  return ez / (1.0f + ez);
}

// Akem humid-thermal-ratio anthracnose infection probability (0..1).
static float anthracnose_risk(float t_max, float t_min, float rh_morning,
                              float lw_hr, float sun_hr, float wind_ms) {
  float range = t_max - t_min;
  if (range < MIN_DIURNAL_RANGE_C) range = MIN_DIURNAL_RANGE_C; // saturated-day clamp
  float htr = rh_morning / range;
  float z = B0 + B_HTR * htr + B_LW * lw_hr + B_SUN * sun_hr + B_WIND * wind_ms;
  return sigmoid(z);
}

// ------------------------------------------------------------ sensor reads ---
// Energise the resistive grid only during the read (low duty cycle) to limit
// DC electrolysis/corrosion -- the documented mitigation; a capacitive sensor
// is the longer-term upgrade. Returns a 12-bit ADC count (0..4095).
static float read_leafwet_adc() {
  pinMode(PIN_LEAFWET_PWR, OUTPUT);
  digitalWrite(PIN_LEAFWET_PWR, HIGH);
  delay(20);                       // let the divider settle
  long acc = 0;
  for (int i = 0; i < 16; i++) { acc += analogRead(PIN_LEAFWET_ADC); delay(2); }
  digitalWrite(PIN_LEAFWET_PWR, LOW);   // de-energise immediately
  return acc / 16.0f;              // averaged to suppress single-read noise
}

static bool in_morning_window() {
  // Without an RTC clock we approximate "morning" as the first reading of the
  // day (sample 0). With an NTP/RTC fix this would check local 06:00-09:00.
  return rtc_sample_count == 0;
}

// ------------------------------------------------------------- output legs ---
static const char* risk_band(float pct) {
  if (pct >= SPRAY_RISK_PCT) return "HIGH - SPRAY WINDOW";
  if (pct >= WATCH_RISK_PCT) return "WATCH";
  return "LOW - SAFE";
}

static void show_oled(float t, float rh, float lw_hr, float risk) {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);
  oled.setCursor(0, 0);  oled.printf("AamRakshak  %s", NODE_ID);
  oled.setCursor(0, 14); oled.printf("T %.1fC  RH %.0f%%", t, rh);
  oled.setCursor(0, 26); oled.printf("Leaf wet %.1f h", lw_hr);
  oled.setTextSize(2);
  oled.setCursor(0, 42); oled.printf("%.0f%%", risk);
  oled.setTextSize(1);
  oled.setCursor(50, 48); oled.print(risk_band(risk));
  oled.display();
}

static void append_log(const char* date, float t_max, float t_min, float rh,
                       float lw_hr, float risk) {
  File f = LittleFS.open("/aamrakshak_log.csv", FILE_APPEND);
  if (!f) return;                              // fail safe: skip logging, keep running
  if (f.size() == 0)
    f.println("node_id,date,t_max_c,t_min_c,rh_morning_pct,leaf_wetness_hr,risk_pct");
  f.printf("%s,%s,%.1f,%.1f,%.0f,%.1f,%.1f\n", NODE_ID, date, t_max, t_min, rh, lw_hr, risk);
  f.close();
}

static void post_json(float t_max, float t_min, float rh, float lw_hr, float risk) {
  if (strlen(WIFI_SSID) == 0 || strlen(POST_URL) == 0) return;  // offline mode
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  for (int i = 0; i < 20 && WiFi.status() != WL_CONNECTED; i++) delay(500);
  if (WiFi.status() != WL_CONNECTED) { WiFi.disconnect(true); return; } // give up quietly
  HTTPClient http;
  http.begin(POST_URL);
  http.addHeader("Content-Type", "application/json");
  char body[256];
  snprintf(body, sizeof(body),
    "{\"node_id\":\"%s\",\"t_max_c\":%.1f,\"t_min_c\":%.1f,\"rh_morning_pct\":%.0f,"
    "\"leaf_wetness_hr\":%.1f,\"risk_pct\":%.1f}",
    NODE_ID, t_max, t_min, rh, lw_hr, risk);
  http.POST((uint8_t*)body, strlen(body));
  http.end();
  WiFi.disconnect(true);
}

// ----------------------------------------------------------------- runtime ---
void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  analogReadResolution(12);                 // 0..4095
  analogSetPinAttenuation(PIN_LEAFWET_ADC, ADC_11db); // full ~0-3.3 V range

  bool oled_ok = oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  bool sht_ok  = sht.begin(0x44);
  ds18b20.begin();
  LittleFS.begin(true);

  // --- read sensors (with fallbacks so a single bad read never crashes) ---
  float t_air = sht_ok ? sht.readTemperature() : NAN;
  float rh    = sht_ok ? sht.readHumidity()    : NAN;
  ds18b20.requestTemperatures();
  float t_leaf = ds18b20.getTempCByIndex(0);
  if (t_leaf == DEVICE_DISCONNECTED_C) t_leaf = NAN;
  if (isnan(t_air) && !isnan(t_leaf)) t_air = t_leaf;   // degrade gracefully
  if (isnan(t_air)) t_air = 28.0f;                      // last-resort neutral
  if (isnan(rh))    rh    = 70.0f;

  float lw_adc = read_leafwet_adc();
  bool  wet    = lw_adc < LEAFWET_WET_ADC_THRESHOLD;

  // --- update the day's running aggregates (persist across deep sleep) ---
  if (t_air > rtc_t_max) rtc_t_max = t_air;
  if (t_air < rtc_t_min) rtc_t_min = t_air;
  if (in_morning_window()) rtc_rh_morning = rh;
  if (rtc_rh_morning < 0) rtc_rh_morning = rh;          // until morning is seen
  if (wet) rtc_wet_samples++;
  rtc_sample_count++;

  // --- once per day: compute risk, display, log, (optionally) upload ---
  if (rtc_sample_count >= SAMPLES_PER_DAY) {
    float lw_hr = (float)rtc_wet_samples * 24.0f / SAMPLES_PER_DAY;
    float risk  = 100.0f * anthracnose_risk(rtc_t_max, rtc_t_min, rtc_rh_morning,
                                            lw_hr, DEFAULT_SUNSHINE_HR, DEFAULT_WIND_MS);
    rtc_last_risk = risk;
    if (oled_ok) show_oled(t_air, rh, lw_hr, risk);
    append_log("today", rtc_t_max, rtc_t_min, rtc_rh_morning, lw_hr, risk);
    post_json(rtc_t_max, rtc_t_min, rtc_rh_morning, lw_hr, risk);

    // reset the day
    rtc_sample_count = 0; rtc_t_max = -100.0f; rtc_t_min = 100.0f;
    rtc_rh_morning = -1.0f; rtc_wet_samples = 0;
  } else if (oled_ok) {
    // mid-day refresh: show live readings + the last computed daily risk
    float lw_hr_so_far = (float)rtc_wet_samples * 24.0f / SAMPLES_PER_DAY;
    show_oled(t_air, rh, lw_hr_so_far, rtc_last_risk);
  }

  // --- sleep until the next sample ---
  esp_sleep_enable_timer_wakeup(SAMPLE_INTERVAL_S * 1000000ULL);
  delay(2500);                 // keep the OLED readable briefly before sleeping
  esp_deep_sleep_start();
}

void loop() { /* unused: all work happens in setup() before deep sleep */ }
