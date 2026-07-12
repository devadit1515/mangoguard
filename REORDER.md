# Parts to order (BPW34 + LM358 detector build)

This is the shopping list for the parts still needed to build the meter as described in
`HARDWARE_BUILD_GUIDE.md`, using the BPW34 photodiode + LM358 amplifier as the detector.
It lists only what is not already on hand.

## Detector

- BPW34 silicon PIN photodiode, 2 pieces
- LM358 dual op-amp, 8-pin DIP (the bare chip, not a "gain module"), 2 pieces
- 8-pin DIP IC socket, 2 pieces

## Resistors (metal film, one-quarter watt, through-hole)

- 1 Mega-ohm, labelled `1M`, 5 pieces
- 470 kilo-ohm, labelled `470K`, 5 pieces (spare gain value)
- 2.2 Mega-ohm, labelled `2M2`, 5 pieces (spare gain value)
- 100 kilo-ohm, labelled `100K`, 5 pieces
- 6.8 kilo-ohm, labelled `6K8`, 5 pieces

Smallest pack sold is usually 100 pieces per value, which is fine (cheap, lifetime spares).

## Capacitors (ceramic, through-hole)

- 10 picofarad, about 10 pieces
- 0.1 microfarad (marked `104` on the part), 2 pieces

## Near-infrared LEDs (5 mm, buy by peak wavelength)

- 730, 760, 810, 850, 880, 910, 940, 970 nm, 2 pieces each

## Prototyping

- Solderless breadboard, full-size (830-point), 1 piece
- Jumper wires, 40-pin 20 cm 2.54 mm Male-to-Male, 1 pack
- Jumper wires, 40-pin 20 cm 2.54 mm Male-to-Female, 1 pack

## Reading resistor labels

The letter is the multiplier, and its position marks the decimal point:

- `E` or `R` alone means ohms. `470E` or `470R` = 470 ohm (too small, wrong part).
- `K` means kilo (x1000). `470K` = 470,000 ohm. `6K8` = 6,800 ohm.
- `M` means mega (x1,000,000). `1M` = 1,000,000 ohm. `2M2` = 2,200,000 ohm.

## Buy-right notes

- Resistors and capacitors: through-hole (two wire legs), not surface-mount.
- Resistors: metal film, not carbon film (lower noise for the sensitive amplifier).
- Capacitors: ceramic, not electrolytic. Ceramic caps have no polarity.
- LM358: the bare 8-pin chip, around Rs. 7 to 20. If it says "module", it is the wrong thing.
- LEDs: confirm the peak wavelength on each datasheet. Generic "IR LED" ships only 850 or 940 nm.
- Jumper wires: 2.54 mm pitch, 20 cm length. Female-to-female is not needed for this build.

## Not catalog parts, but still required

These have to be made or printed, not ordered, and the meter cannot be calibrated or used
without them:

- Opaque tube or 3D-printed housing, matte black on the inside.
- White reference tile (a scrap of matte-white plastic or PTFE).
- A soldering iron, for the permanent version (the breadboard stage needs none).

## Already on hand (do not re-buy)

ESP32 DevKit V1, SSD1306 OLED, 8 NPN transistors (KN2222A), 8 resistors of 220 ohm,
8 resistors of 1 kilo-ohm, push button, perfboard, hook-up wire, header pins, solder,
heat-shrink tubing, USB cable, multimeter.
