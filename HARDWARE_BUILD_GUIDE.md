# AamParakh hardware build guide

This guide builds the eight-wavelength near-infrared mango dry-matter meter one small step at a time. It assumes you have **never built an electronic circuit before**. Every step is spelled out, and after each stage there is a check so you know it worked before you move on.

Two rules make this easy instead of hard:

1. **Build it on a breadboard first.** A breadboard lets you push parts into holes with no soldering, so nothing is permanent and any mistake is a two-second fix. You only pick up a soldering iron at the very end, after the whole thing already works.
2. **Test after every stage.** You will build the light sensor first and prove it reacts to light before you add anything else. Then one LED. Then the rest. If a stage fails you know exactly which one, because everything before it already passed.

An adult should be nearby for two jobs only: the hot soldering iron near the end, and the oven work during data collection (a separate guide). Everything else is safe, low-voltage, and cannot shock you.

Take your time. A beginner should expect a weekend or two, most of it careful checking rather than anything difficult. The parts come to roughly ₹2,300.

**How the meter works, in one paragraph.** It shines eight near-infrared LEDs, one at a time, onto a mango and measures how much of each colour bounces back with one light sensor. Fruit with more dry matter reflects these wavelengths differently, and the eight numbers together predict the dry-matter percentage. The wavelengths were not guessed; they are the ones a search over 11,691 real fruit found to carry the signal (see the report, Section 5.3).

---

## 1. What you need before you start

**Tools (you supply these):**

- A **multimeter**. Any cheap one with a diode-test setting (the symbol that looks like an arrow pointing at a line) and a DC-volts setting. You will use it constantly to check parts and readings.
- A **solderless breadboard** and a **pack of jumper wires** (the kind with pins on both ends). Half-size is fine; full-size is easier.
- A computer with a free USB port, for programming the ESP32.
- Later, for the permanent version: a **soldering iron and solder**, wire cutters, and an adult to supervise.

**A phone with a camera.** Near-infrared LEDs are invisible to your eyes, so you cannot tell if one is lit. A phone camera can see the glow. You will use this to test the LEDs.

---

## 2. Bill of materials

| Component | Qty | What it is and what to watch for |
|---|---|---|
| ESP32 DevKit V1 | 1 | The small computer that runs everything. Any ESP32 board with a spare analog pin and eight free GPIO pins works. Note whether yours has a Micro-USB or USB-C socket, and get the matching cable. |
| Near-infrared LEDs: 730, 760, 810, 850, 880, 910, 940, 970 nm | 1 each (buy 2 each) | The eight light sources. **Buy by peak wavelength from an optoelectronics supplier.** Generic "IR LED" almost always means 850 or 940 nm only, which will not work. The odd wavelengths (730, 760, 810, 880, 910, 970) are specialty parts. |
| BPW34 silicon PIN photodiode | 1 (buy 2) | The light sensor. It turns light into a tiny electric current. It responds well from 730 to 970 nm, so it suits this meter. |
| LM358 dual op-amp (8-pin DIP) | 1 (buy 2) | The amplifier chip. It turns the photodiode's tiny current into a voltage the ESP32 can read. |
| 8-pin DIP socket | 1 | You solder the socket to the board and push the LM358 into it, so the chip never touches the hot iron. |
| SSD1306 0.96" OLED, I2C type | 1 | The little screen that shows the result in the field. |
| NPN transistors (2N2222 / KN2222A / PN2222A) | 8 (buy 10) | One per LED. They act as switches so the ESP32 can turn each LED on alone. |
| Resistor 220 Ω | 8 | One per LED, sets how bright each LED runs. |
| Resistor 1 kΩ | 8 | One per transistor, protects the ESP32 pin. |
| Resistor 1 MΩ | 1 | Sets the amplifier's gain. Keep a 470 kΩ and a 2.2 MΩ nearby too, for tuning in Section 8. |
| Resistor 100 kΩ and 6.8 kΩ | 1 each | Together they make the small reference voltage the amplifier rests at. |
| Capacitor 10 pF (ceramic) | 1 | Stops the amplifier from buzzing/oscillating. |
| Capacitor 0.1 µF (ceramic) | 2 | Steady the power and the reference voltage. |
| Push button, small tactile (4-pin) | 1 | Press it to set the white reference. |
| Perfboard / general-purpose PCB | 1 | The permanent home for the circuit, used only at the end. |
| Hook-up wire and header pins | 1 lot | For the permanent version. |
| Opaque tube or 3D-printed housing + white tile | 1 | Holds the LEDs and sensor against the fruit and blocks room light. A scrap of matte-white plastic or PTFE is the white tile. |
| USB power bank + cable | 1 | Powers the meter in the orchard. |

**The eight LED wavelengths are the heart of the design.** If a supplier is out of one, 940 nm is the only one that is truly fixed; the others can shift by 10 to 20 nm at a small cost in accuracy, but do not substitute anything below 700 nm or above 980 nm.

**Simpler alternative for the sensor.** If building the amplifier turns out to be too fiddly, an **OPT101 module** is a drop-in replacement for the BPW34, the LM358, the socket, and the six small parts around them (the 1 MΩ, 100 kΩ, 6.8 kΩ, 10 pF, and one 0.1 µF). The OPT101 is a photodiode and amplifier already built into one part; you just wire its output to GPIO 34, its power to 3V3, and its ground to GND, and skip Section 5. Everything else in this guide is written for the BPW34 + LM358 build, because that is what most students will have.

---

## 3. Get to know your parts

Spend twenty minutes here. Knowing which leg is which now saves hours of confusion later. You will use the multimeter's **diode-test** setting, where the **red** lead is the positive one.

### The transistors (find Emitter, Base, Collector)

A 2N2222-family transistor in the small black half-round package (TO-92) almost always has its legs, with the **flat face toward you and legs pointing down**, in the order **E, B, C** from left to right. Confirm it once on one transistor (they are all the same):

1. Set the meter to diode-test.
2. Put the **red** probe on the **middle leg (Base)** and touch the black probe to each outer leg in turn. Both should read about **0.6 to 0.7 V**. That confirms the middle leg is the Base and the part is the right type (NPN).
3. Of the two outer legs, the one that reads slightly **higher** from the Base is the **Emitter**; the slightly **lower** one is the **Collector**.

```
   ___
  /   \
  |2222|      flat face toward you, legs down
  |____|
   | | |
   E B C
```

### The LEDs (find + and -, and prove they light)

Every LED has a **long leg (the + side, anode)** and a **short leg (the - side, cathode)**. The plastic rim is also flattened on the cathode side. Because these LEDs are infrared, your eyes see nothing when they are on, so use a phone camera to prove one works:

1. Take any one LED. Connect its long leg through a 220 Ω resistor to 3V3, and its short leg straight to GND (you can do this on the breadboard, or just hold the legs to the ESP32's 3V3 and GND pins with the resistor in line).
2. Point a phone camera at the front of the LED. On the phone screen you should see a faint purple or white glow. That is the infrared light your eyes cannot see. If you see it, the LED is good and you know which way round it goes.

Do this for all eight at least once, so you never wonder later whether a dark-looking LED is faulty.

### The BPW34 photodiode (find + and -)

The BPW34 looks like a small clear or blue-tinted square with two legs. One leg is the cathode (the - side), usually marked on the case. Confirm it with the meter:

1. Diode-test setting. Touch the red probe to one leg and black to the other. When you get a reading of roughly **0.3 to 0.6 V**, the leg under the **red** probe is the **anode (+)** and the leg under the **black** probe is the **cathode (-)**.
2. To be completely sure, switch the meter to DC volts, hold the two probes on the two legs, and shine a bright light on the BPW34. A small positive voltage appears with the **red probe on the cathode**. Mark the cathode leg with a dot of marker.

### The LM358 chip (know its pins)

The LM358 is an 8-pin chip with a small notch or dot at one end. **Hold it so the notch is on your left; pin 1 is the bottom-left pin, and the numbers run counter-clockwise.** You do not have to memorise this; just keep this map beside you:

| Pin | Name | Pin | Name |
|---|---|---|---|
| 1 | Output A | 8 | **Power +** (to 3V3) |
| 2 | Input A - | 7 | Output B |
| 3 | Input A + | 6 | Input B - |
| 4 | **Power -** (to GND) | 5 | Input B + |

The chip has two amplifiers inside, called A and B. This build uses **A as the light amplifier** and **B to hold a steady reference voltage**.

---

## 4. Build the light sensor and test it first

This is the most important stage and the one that makes or breaks the meter, so you build it alone and prove it works before adding anything else. Push the LM358 into the breadboard so it straddles the centre gap. Then make these connections. Take them one line at a time and tick each one off.

**Power the chip:**

1. LM358 **pin 8** to the breadboard **+ rail**; connect the + rail to the ESP32 **3V3**.
2. LM358 **pin 4** to the breadboard **- rail**; connect the - rail to the ESP32 **GND**.
3. A **0.1 µF** capacitor between pin 8 and the - rail, pushed in close to the chip. (Capacitors of this value have no polarity, so either way round is fine.)

**Make the reference voltage (amplifier B):**

4. A **100 kΩ** resistor from the + rail to an empty row; call that row **REF**.
5. A **6.8 kΩ** resistor from **REF** to the - rail.
6. A **0.1 µF** capacitor from **REF** to the - rail.
7. A wire from **REF** to LM358 **pin 5**.
8. A wire from LM358 **pin 7** to LM358 **pin 6**.

> **Check now:** power the ESP32 by USB, set the meter to DC volts, black probe on the - rail, red probe on **pin 7**. You should read about **0.2 V**. If you do, the reference is working. If you read 0 V or 3.3 V, recheck steps 4 to 8.

**Make the light amplifier (amplifier A):**

9. A wire from LM358 **pin 7** to LM358 **pin 3**.
10. The **BPW34 cathode (-)** to LM358 **pin 7**.
11. The **BPW34 anode (+)** to LM358 **pin 2**.
12. A **1 MΩ** resistor from LM358 **pin 1** to LM358 **pin 2**.
13. A **10 pF** capacitor from LM358 **pin 1** to LM358 **pin 2**, right beside the 1 MΩ resistor (they sit in parallel).

> **Check now, the big one:** meter on DC volts, black on the - rail, red on **pin 1**. Cover the BPW34 completely with your finger; the reading should fall to about **0.2 V**. Now uncover it and shine your phone torch on it; the reading should **jump up** (it may shoot all the way to about 1.8 V, which just means lots of light, and that is fine). If the number moves with light, **your sensor works.** This is the hard part done.

Leave **pin 1** connected by a jumper wire to the ESP32 **GPIO 34** now; that is where the ESP32 reads the light.

If pin 1 sits stuck at the top or the bottom and never moves with light, go to Troubleshooting; the usual causes are the BPW34 in backwards or a missing reference voltage.

---

## 5. Add one LED and its switch, then test it

Each LED is turned on by one transistor acting as a switch. Build **one** channel first. Use the 730 nm LED, which is driven by GPIO 13.

1. Put the transistor in the breadboard. Identify its E, B, C legs from Section 3.
2. **Emitter** to the **- rail** (GND).
3. **1 kΩ** resistor from **GPIO 13** to the transistor **Base**.
4. **Collector** to the LED's **short leg (cathode, -)**.
5. LED's **long leg (anode, +)** through a **220 Ω** resistor to the **+ rail** (3V3).

> **Check now:** you cannot run firmware yet, so test by hand. Briefly touch a jumper from **GPIO 13's row to the 3V3 rail** to force the pin high (or just move the 1 kΩ resistor's top end from GPIO 13 to the 3V3 rail for a moment). Point the phone camera at the LED. It should glow on the phone screen. Move the jumper back to GND and the glow goes out. That proves the switch and the LED both work.

When that one channel works, you understand the pattern. The other seven are identical.

---

## 6. Add the remaining seven LEDs

Repeat Section 5 exactly for each LED. The only thing that changes is which GPIO pin drives it and which LED you use. Wire them in this order and keep the order, because the firmware expects it:

| LED (nm) | 730 | 760 | 810 | 850 | 880 | 910 | 940 | 970 |
|---|---|---|---|---|---|---|---|---|
| GPIO pin | 13 | 12 | 14 | 27 | 26 | 25 | 33 | 32 |

For each LED you add: one transistor, one 1 kΩ from the GPIO to the Base, Emitter to GND, Collector to the LED cathode, and the LED anode through one 220 Ω to 3V3. That is eight transistors, eight 1 kΩ resistors, and eight 220 Ω resistors in total.

Arrange the eight LEDs in a rough ring with the BPW34 in the middle. You will fix this geometry properly in the housing later (Section 11); for now on the breadboard just keep them grouped together pointing the same way.

---

## 7. Add the screen and the button

**The OLED screen (four wires):**

1. OLED **VCC** to **3V3**.
2. OLED **GND** to **GND**.
3. OLED **SDA** to **GPIO 21**.
4. OLED **SCL** to **GPIO 22**.

**The button (two wires):**

5. One leg of the button to **GPIO 4**.
6. The opposite leg of the button to **GND**.

The button needs no resistor; the firmware switches on the ESP32's own internal pull-up. The screen needs no extra parts.

---

## 8. Load the firmware

The eight prediction weights are already inside the firmware, so once it is loaded the meter works on its own with no computer attached.

1. Install the **Arduino IDE** on your computer (free, from arduino.cc).
2. Add ESP32 support: open **File > Preferences**, and in "Additional boards manager URLs" paste `https://espressif.github.io/arduino-esp32/package_esp32_index.json`. Then open **Tools > Board > Boards Manager**, search **esp32**, and install the one by Espressif Systems.
3. Install two libraries: open **Tools > Manage Libraries**, and install **Adafruit SSD1306** and **Adafruit GFX Library**. If it offers to install extra dependencies, say yes.
4. Open the sketch `firmware/aamparakh_node/aamparakh_node.ino`.
5. Plug in the ESP32. Under **Tools > Board** pick "ESP32 Dev Module" (or "DOIT ESP32 DEVKIT V1"), and under **Tools > Port** pick the port that appeared when you plugged it in.
6. Click **Upload** (the arrow button). If it says "Connecting..." for a long time, hold the **BOOT** button on the ESP32 down while it connects, then let go.
7. Open **Tools > Serial Monitor** and set the speed to **115200**. You should see a line of column headings, and then a new line of numbers every time the meter takes a reading.

---

## 9. First light, and tuning the amplifier

**First reading.** With the Serial Monitor open, hold the white tile (or any piece of white paper) over the LEDs and sensor and press the button once. The screen should say the white reference is set. Now hold the sensor against a mango. The screen shows a dry-matter number and either READY or WAIT, and the Serial Monitor prints eight band values.

**Tune the gain (one-time).** The 1 MΩ resistor sets how strongly the amplifier responds. You want the white tile to give a strong reading without maxing out:

- Watch the eight band values in the Serial Monitor while you hold the white tile.
- If several bands read at or very near their ceiling and will not change, the gain is too high: swap the **1 MΩ** for **470 kΩ**.
- If the bands are tiny and noisy, the gain is too low: swap the **1 MΩ** for **2.2 MΩ**.
- Most builds are happy at 1 MΩ. Change it only if the readings are clearly pinned or clearly tiny.

Once the white tile gives clean, mid-range readings, the electronics are finished.

---

## 10. Make it permanent (soldering)

Only do this once the breadboard version fully works. Now an adult should be nearby for the hot iron.

1. Solder the **8-pin socket** (not the LM358 itself) onto the perfboard first. Push the LM358 into the socket only after all the soldering is done and cooled.
2. Move the parts across from the breadboard one channel at a time, and keep the same wiring you already tested. Solder near-infrared LEDs quickly; too much heat can damage them, so touch the iron for a second or two, no longer.
3. After each joint, look closely for two things: a shiny, cone-shaped joint (good), and no accidental bridge of solder between two neighbouring pads (bad; remove it).
4. When it is all soldered, do the Section 4 sensor check and the Section 9 white-tile check again, to confirm nothing broke in the move.

---

## 11. The housing and optics

The measurement lives or dies on geometry, not on the electronics. The eight LEDs and the BPW34 must sit at the end of a short opaque tube that presses flat against the fruit and keeps room light out. Arrange the LEDs in a ring around the BPW34 so every LED lights the same patch of fruit the sensor sees.

Keep the LED-to-fruit and sensor-to-fruit distances the same for every reading. A hand-held gap that changes between fruit is the single largest source of error, so a 3D-printed housing that fixes these distances is worth the effort. Paint or line the inside of the tube matte black so stray reflections do not reach the sensor. Cut a small white tile (matte white plastic or PTFE) to hold against the opening when you set the white reference.

---

## 12. Calibration

Two calibrations matter, and they are different.

**White reference (every session).** Hold the white tile against the opening and press the button. This tells the meter what "all the light comes back" looks like, so it can turn raw sensor readings into reflectance. Redo it whenever the light around you changes, or every twenty fruit.

**Local calibration (once per cultivar).** The model was trained on Australian fruit, so on Alphonso or Kesar it reads with a small, steady bias. Measure about twenty local fruit against oven-dried dry matter (the procedure is in `FARM_DATA_COLLECTION.md`), fit a single slope and offset, and set `LOCAL_SLOPE` and `LOCAL_OFFSET` at the top of the firmware. This one step turns a biased reading into an accurate one, and the report (Section 5.6) shows it cuts the error by more than half.

---

## 13. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Sensor voltage (pin 1) never moves with light | BPW34 in backwards, or the reference is wrong | Swap the BPW34 legs; recheck that pin 7 reads about 0.2 V; confirm the 1 MΩ is between pins 1 and 2 |
| Sensor voltage jumps around or buzzes | The 10 pF cap is missing or the sensor leads are long | Fit the 10 pF cap across the 1 MΩ; keep the BPW34's two leads short; make sure the 0.1 µF sits close to the chip |
| Every band reads near zero | An LED is not lighting, or the amplifier lost power | Test each LED with the phone camera; check the LM358 has 3V3 on pin 8 and GND on pin 4 |
| Board will not start with everything connected | GPIO 12 (the 760 nm LED) held high at power-up | Power up first, or briefly unplug the wire to GPIO 12 while the board boots, then reconnect |
| Readings jump between fruit | Changing gap or stray light | Use the housing; keep pressure and distance the same; redo the white reference |
| Dry matter reads far too high or low | White reference not set, or local calibration wrong | Set the white reference; redo the local slope and offset |
| Screen stays blank | Wrong screen address or swapped wires | Confirm the OLED is the I2C type at address 0x3C and that SDA/SCL are on GPIO 21/22 |
| An infrared LED looks dead | You cannot see infrared by eye | Point a phone camera at it; a working LED glows faintly on the screen |

---

## 14. Safety

The whole device runs at 3.3 to 5 volts from a USB power bank. There is no mains and no shock hazard. Near-infrared LEDs are invisible but low-power; point them into the fruit housing and do not stare into the opening from close up. Take the usual care with a hot soldering iron, have an adult nearby for it, and let parts cool before touching them.
