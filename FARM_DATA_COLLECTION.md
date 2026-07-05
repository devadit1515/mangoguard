# Collecting the real orchard data

This is the one part of the project that has to happen with real fruit, and only you can do it. It replaces the placeholder pilot in Section 5.6 of the report with genuine Alphonso and Kesar measurements. The whole collection takes one long afternoon of readings plus a day or two of oven-drying in the background. Follow the steps in order.

When you are done you will have a file, `data/farm/aamparakh_farm_readings.csv`, that the analysis picks up automatically: re-run `python scripts/run_evaluation.py` and the farm numbers in the report become your measured ones.

---

## What you need

- The built AamParakh meter (see `HARDWARE_BUILD_GUIDE.md`), flashed and working, with a white reference tile.
- A laptop to log the serial output from the meter.
- **40 to 120 mango fruit spanning a range of ripeness.** This is the single most important requirement. If every fruit is the same ripeness there is nothing for the model to learn. Get some hard green ones straight off the tree, some half-ripe, and some soft-ripe from the market. Aim for Alphonso and Kesar if you can; either alone is fine.
- A kitchen scale reading to 0.01 g if possible, 0.1 g at worst.
- An oven or a food dehydrator that holds about 65 to 70 °C.
- A knife and a cutting board, and an adult present for the oven work.

---

## Step 1 — Take a meter reading for each fruit

1. Number every fruit with a marker: `A01`, `A02`, ... for Alphonso, `K01`, ... for Kesar.
2. Power the meter and press the button once against the white tile to set the white reference. Do this again every twenty fruit or if the light changes.
3. For each fruit, hold the sensor window flat against the cheek of the fruit and take a reading. Take it at two or three spots around the fruit and keep them; do not average by hand.
4. The meter prints a line over serial for every reading, in this exact order:

   ```
   fruit_id,cultivar,DM,b730,b760,b810,b850,b880,b910,b940,b970
   ```

   The meter leaves `fruit_id` and `cultivar` blank and fills in its own DM estimate and the eight band values. Copy each line into your spreadsheet and type in the fruit number and cultivar yourself.

Keep the geometry the same every time: same pressure, sensor flat on the skin, fruit shading the window from room light. Inconsistent geometry is the main thing that adds noise.

---

## Step 2 — Measure the true dry matter of each fruit

This is the reference value the meter is judged against. It is the standard oven-dry method.

1. Cut a thin slice, about 5 mm, straight through the cheek you measured, skin to stone, so the sample represents the whole flesh.
2. Weigh the fresh slice immediately and record it as `fresh_g`. Weigh a small tray first and subtract it, or tare the scale.
3. Dry the slices at 65 to 70 °C until the weight stops changing. In an oven this is usually 24 to 48 hours; in a dehydrator, similar. Weigh once, dry for a few more hours, weigh again; when two weighings match, it is done. Label each slice so it stays matched to its fruit.
4. Record the final dry weight as `dry_g`.
5. The true dry matter is:

   ```
   DM (%) = 100 * dry_g / fresh_g
   ```

Use this measured `DM` in the CSV, not the meter's estimate. The meter's estimate is what you are testing; the oven value is the truth.

---

## Step 3 — Build the CSV

Make one row per fruit reading, with these columns in this order:

```
fruit_id,cultivar,DM,b730,b760,b810,b850,b880,b910,b940,b970,provenance
```

- `fruit_id`: your label, e.g. `A01`.
- `cultivar`: `Alphonso` or `Kesar`.
- `DM`: the oven-dry percentage from Step 2.
- `b730` ... `b970`: the eight band values the meter printed for that reading.
- `provenance`: the word `REAL_FARM` on every row.

Save it as `data/farm/aamparakh_farm_readings.csv`. A worked example row:

```
A01,Alphonso,17.8,0.214,0.198,0.256,0.241,0.199,0.233,0.221,0.207,REAL_FARM
```

---

## Step 4 — Run the analysis

From the project root:

```
python scripts/run_evaluation.py
python scripts/make_figures.py
```

The script sees that the farm file is now real (no `SYNTHETIC_PLACEHOLDER` rows), uses your fruit for the on-orchard validation, and rewrites the farm numbers and Figure 9. Then update the two farm sentences in Section 5.6 of the report and the provenance note in Appendix F to say the readings are your own, and delete the placeholder caveat.

---

## How many fruit, and how to split them

The script uses the first twenty of your fruit as the local calibration anchor and the rest as the validation set, so aim for **at least 40 fruit**, and more is better. What matters most is the spread of dry matter: try to cover roughly 12% to 22% DM, with fruit at both ends, not a cluster in the middle. A good collection is 60 to 100 fruit across a wide ripeness range.

## Safety

- An adult should be present for the oven work; slices at 70 °C and hot trays can burn.
- Cut away from your hand on a stable board.
- The meter is low-voltage from a USB power bank; there is no mains and no shock risk.
