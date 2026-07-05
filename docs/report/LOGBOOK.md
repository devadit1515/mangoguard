# AamParakh — project logbook

A dated working log kept through the project. It feeds criterion 1.5 (time), 3.3 (reflection) and 4.4 (problems). Cumulative hours reach about 71, above the CREST Gold guideline of 70.

---

**12/04/2026 · 4 h · cumulative 4 h**
Planned: pick a project. Did: read the CREST Gold criteria and thought about a mango tool with real hardware. The idea that stuck was harvest timing. My family's Alphonso some years never ripens well, and I found this is decided by dry matter at harvest, a number growers cannot measure because the meter costs about ₹8.5 lakh. Decided to ask whether a cheap one is possible. Open question: is there any real data to work from?

**16/04/2026 · 4 h · cumulative 8 h**
Did: found the Anderson-Walsh public mango dataset on Mendeley, 11,691 near-infrared scans with oven-dry dry-matter values, open licence. This is the whole foundation: real fruit, a published error to reproduce, ten cultivars, four seasons. Wrote the aim as one question and pinned down five success conditions before touching the data, so I could not move the goalposts.

**20/04/2026 · 5 h · cumulative 13 h**
Planned: reproduce a published prediction. Did: loaded the data, worked out the calibration/tuning/test split from the dataset's own column, and fitted a partial least squares model on the full spectrum. Got an R² of 0.85 on the held-out season, close to the published error. The pipeline is sound. Spent a while understanding why partial least squares suits spectra (neighbouring wavelengths are almost the same, so a plain regression falls apart).

**24/04/2026 · 4 h · cumulative 17 h**
Did: wrote the metrics (RMSEP, R², RPD) from their definitions and checked them against scikit-learn so I actually understand them, not just call them. Small satisfaction: they matched exactly.

**29/04/2026 · 5 h · cumulative 22 h**
Planned: test a cheap sensor without owning one. Did: wrote the method that integrates a real spectrum through a band's response, so I can see what any sensor would read on the real fruit. Checked it on a flat spectrum (every band should return the constant, and it does).

**04/05/2026 · 4 h · cumulative 26 h**
Problem: my first cheap-sensor model scored an R² near 0.2. Nearly wrote off the whole cheap-meter idea. Something is wrong, or the idea does not work. Stuck.

**09/05/2026 · 5 h · cumulative 31 h**
Fixed it, and this was the turning point. Placed eighteen bands evenly across the informative window and got 0.84; the same number of bands at an off-the-shelf chip's fixed positions got 0.43. The number of bands was never the problem. Their placement is. The dry-matter signal sits in a narrow near-infrared region and a sensor that looks elsewhere is blind to it. This reshaped the project from "can a cheap sensor work" to "which wavelengths does it need".

**14/05/2026 · 4 h · cumulative 35 h**
Did: wrote the forward search that adds wavelengths one at a time, best first, choosing only on the tuning split. It picked 910, then 880, then 940 nm before anything else, exactly the sugar-and-water region. Five well-placed bands already reach 95% of the full spectrum. Good day.

**19/05/2026 · 4 h · cumulative 39 h**
Did: ran the two off-the-shelf chips through the same method. The AS7265x got 0.21, the AS7263 got −0.14. Both fail, and I can say why: the AS7265x wastes eleven of eighteen channels in the visible, and the AS7263 stops at 860 nm and misses the bands that matter. This is a clean negative result and it justifies building a custom sensor.

**24/05/2026 · 3 h · cumulative 42 h**
Problem: I tried a scatter-correction step to help the chips, and it made the eighteen-band model unstable, swinging wildly on tiny changes. Learned to prefer a simpler model I can trust over a fancier one I cannot. Dropped it, kept the plain pipeline.

**29/05/2026 · 5 h · cumulative 47 h**
Did: chose the eight buyable LED wavelengths (730 to 970 nm) from the search and confirmed the eight-band model reaches 0.84 on the unseen season. Settled the design.

**03/06/2026 · 5 h · cumulative 52 h**
Did: the cross-cultivar test, training without each cultivar and testing on it. R² between 0.63 and 0.78; weakest on Kensington Pride with about a 1% bias. Honest and useful: it shows the meter generalises but reads a new cultivar with a bias.

**09/06/2026 · 4 h · cumulative 56 h**
Did: showed that a short local calibration, one slope and offset from twenty fruit, removes most of that bias. This is the deployment recipe for taking the meter to Indian cultivars.

**15/06/2026 · 5 h · cumulative 61 h**
Planned: build the meter. Did: soldered the eight LED drivers and the OPT101, wired the OLED. Near-infrared LEDs look dark to the eye, which cost me an hour until I checked them with a phone camera and saw them glowing. Exported the eight model weights and put them in the firmware.

**20/06/2026 · 4 h · cumulative 65 h**
Did: checked the on-device arithmetic against the Python model; they agree to a rounding error. Wrote the white-reference and local-calibration steps into the firmware. Set up the orchard data-collection protocol for the field validation.

**26/06/2026 · 3 h · cumulative 68 h**
Did: wrote the figure script so every figure redraws from the metrics file, and drafted most of the report. Re-read the success conditions and checked each is answered with a number.

**04/07/2026 · 3 h · cumulative 71 h**
Did: self-critique as a harsh examiner. Checked every figure is referenced before it appears, every citation is in the reference list, and every number in the report matches the metrics file. Scrubbed the writing for tired phrasing. Ready to submit, with the Indian field validation named as the next step.
