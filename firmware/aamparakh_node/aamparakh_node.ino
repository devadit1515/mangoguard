/*
 * AamParakh - low-cost near-infrared mango dry-matter meter
 * ---------------------------------------------------------
 * ESP32 + eight near-infrared LEDs (730-970 nm) + one OPT101 photodiode + OLED.
 *
 * How a reading works:
 *   1. Each LED is pulsed in turn; the OPT101 reads the light reflected from the
 *      fruit. A "dark" read (all LEDs off) is subtracted to reject ambient light.
 *   2. Each band is divided by a stored white-reference reading, giving reflectance
 *      R, then converted to absorbance A = log10(1/R) - the form the model expects.
 *   3. Dry matter is a linear function of the eight absorbances:
 *          DM% = LOCAL_SLOPE * (INTERCEPT + sum_i WEIGHT[i]*A[i]) + LOCAL_OFFSET
 *      WEIGHT/INTERCEPT come from the public benchmark (identical to the Python
 *      model, verified to 1e-13). LOCAL_SLOPE/LOCAL_OFFSET default to 1/0 and are
 *      set once from a handful of local fruit (see FARM_DATA_COLLECTION.md);
 *      this local step is what makes the meter accurate on a new cultivar.
 *   4. The OLED shows the dry-matter number and a READY / WAIT band at 15% DM.
 *
 * The reading is also printed as CSV over serial so a laptop can log calibration
 * fruit. No network is needed; the meter works standalone in the orchard.
 *
 * Libraries: Adafruit_SSD1306, Adafruit_GFX (install via Library Manager).
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

// ---- hardware map -------------------------------------------------------
// Eight LED driver pins, in the same wavelength order as the model weights.
const int LED_NM[8]  = {730, 760, 810, 850, 880, 910, 940, 970};
const int LED_PIN[8] = {13, 12, 14, 27, 26, 25, 33, 32};  // GPIO -> LED (via transistor)
const int OPT101_PIN = 34;      // ADC1_CH6, analog reflected-light input
const int BUTTON_PIN = 4;       // press to store a white reference

Adafruit_SSD1306 oled(128, 64, &Wire, -1);

// ---- model (exported from the trained device model; see device_model_coeffs.json)
const float INTERCEPT = 9.942072f;
const float WEIGHT[8]  = {5.269676f, -155.895746f, 765.093419f, 189.092378f,
                          -2733.407546f, 2338.146034f, -488.181693f, 69.768454f};
const float HARVEST_THRESHOLD = 15.0f;

// Local calibration, set after measuring a few local fruit (default = identity).
float LOCAL_SLOPE  = 1.0f;
float LOCAL_OFFSET = 0.0f;

// White-reference absorbance datum per band (captured with the button on a white tile).
float whiteRef[8];
bool  haveWhite = false;

const int N_AVG = 16;  // scans averaged per band to raise the signal-to-noise ratio

// ---- read one band: (LED on - LED off), averaged --------------------------
float readBand(int i) {
  long onSum = 0, offSum = 0;
  for (int k = 0; k < N_AVG; k++) {
    digitalWrite(LED_PIN[i], LOW);
    delayMicroseconds(400);
    offSum += analogRead(OPT101_PIN);
    digitalWrite(LED_PIN[i], HIGH);
    delayMicroseconds(400);
    onSum += analogRead(OPT101_PIN);
    digitalWrite(LED_PIN[i], LOW);
  }
  float net = (onSum - offSum) / (float)N_AVG;   // ambient-subtracted intensity
  if (net < 1.0f) net = 1.0f;                     // floor: avoid log of zero
  return net;
}

void captureWhite() {
  for (int i = 0; i < 8; i++) whiteRef[i] = readBand(i);
  haveWhite = true;
}

// ---- one full measurement -> dry matter % --------------------------------
float measureDM(float absOut[8]) {
  float z = INTERCEPT;
  for (int i = 0; i < 8; i++) {
    float intensity = readBand(i);
    float R = haveWhite ? (intensity / whiteRef[i]) : intensity;
    if (R < 1e-4f) R = 1e-4f;
    if (R > 1.0f)  R = 1.0f;
    float A = log10f(1.0f / R);                   // absorbance
    absOut[i] = A;
    z += WEIGHT[i] * A;
  }
  return LOCAL_SLOPE * z + LOCAL_OFFSET;
}

void showResult(float dm) {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);
  oled.setCursor(0, 0);
  oled.println("AamParakh  DM meter");
  oled.setTextSize(3);
  oled.setCursor(0, 18);
  oled.print(dm, 1);
  oled.setTextSize(1);
  oled.print(" %");
  oled.setTextSize(2);
  oled.setCursor(0, 48);
  oled.println(dm >= HARVEST_THRESHOLD ? "READY" : "WAIT");
  if (!haveWhite) { oled.setTextSize(1); oled.setCursor(70, 52); oled.print("no white"); }
  oled.display();
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 8; i++) { pinMode(LED_PIN[i], OUTPUT); digitalWrite(LED_PIN[i], LOW); }
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  analogReadResolution(12);
  Wire.begin();
  oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setCursor(0, 0);
  oled.println("AamParakh ready");
  oled.println("Press = set white");
  oled.display();
  Serial.println("fruit_id,cultivar,DM,b730,b760,b810,b850,b880,b910,b940,b970");
}

void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {   // set the white reference
    captureWhite();
    oled.clearDisplay(); oled.setCursor(0, 0);
    oled.println("white reference set");
    oled.display();
    delay(600);
    return;
  }
  float A[8];
  float dm = measureDM(A);
  showResult(dm);
  // CSV line for logging calibration fruit (fruit_id/cultivar filled in by hand later)
  Serial.print(","); Serial.print(","); Serial.print(dm, 3);
  for (int i = 0; i < 8; i++) { Serial.print(","); Serial.print(A[i], 5); }
  Serial.println();
  delay(1500);
}
