# AamGanak

Estimating how many mangoes a tree carries from a short walk around it with a camera,
including the fruit no viewpoint ever sees.

An independent research project by Devadit Jain, submitted for a CREST Gold Award and
then to Regeneron ISEF.

The work lives in **[`aamganak/`](aamganak/)**. Start with
[`aamganak/PROJECT_DEFINITION.md`](aamganak/PROJECT_DEFINITION.md) for the aim, the
objectives and the success conditions that were fixed before any code was written, and
[`aamganak/FIX_LOG.md`](aamganak/FIX_LOG.md) for what went wrong along the way.

## The question

Fruit detectors already find the visible mangoes in an image almost perfectly: the
published MangoYOLO benchmark reaches an F1 of 0.968. A tree hides most of its own crop
behind leaves, limbs and other fruit, so the visible count is not the crop. Counting
mango from a vehicle imaging both sides of a row recovers about 40% of what the trees
actually carried, and the standard repair is to multiply by a correction factor fitted per
orchard, a factor that ranges from 1.05 to 2.43 across orchards. The authors of that work
say plainly that the final estimate is sensitive to it.

This project asks whether the hidden fruit can be estimated from the data itself instead.
Every camera position is treated as a survey occasion, the pattern of which viewpoints saw
which fruit gives the detector's hit rate, and the three-dimensional reconstruction
measures the canopy volume that no camera ever saw into.

## State

Simulation stage. Real-orchard validation waits for the Alphonso season in early 2027,
because the ground truth for a tree is obtained by picking it and counting.

`extra_stuff/aamparakh_archive/` holds the previous project, an eight-wavelength
near-infrared meter for mango dry matter, which is finished and also in git history.
