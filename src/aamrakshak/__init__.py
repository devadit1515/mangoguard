"""AamRakshak — low-cost leaf-wetness early-warning for mango anthracnose.

A sub-Rs.2,000 open-source sensor node (ESP32 + leaf-wetness + microclimate)
that predicts anthracnose (*Colletotrichum gloeosporioides*) infection windows
well enough to cut needless calendar fungicide sprays. The package holds:

- ``riskengine``  the Akem (2006) humid-thermal-ratio infection model, the
  leaf-wetness sensor model, and the spray-decision rule;
- ``sim``         a physically-grounded, seeded generator of regional mango
  weather and *independent* outbreak labels (so the backtest is not circular);
- ``eval``        the evaluation pipeline (sensor-tier study, leaf-wetness
  sensor validation, spray-reduction analysis, calibration, ablation);
- ``io``          ingest of real node logs (JSON/CSV) into the same records.

Design and scope: see ``docs/DESIGN.md``. Every headline number in the report
is a real output of ``scripts/run_evaluation.py``.
"""

__version__ = "0.1.0"
