"""Market-conditioned MRL-aware spray recommender.

This subpackage takes the PPI from ``mangoguard.risk`` and produces a
single, actionable spray recommendation per (block, day, target market)
tuple. The recommendation filters by:

- **PHI** (pre-harvest interval) -- pesticides whose residue half-life
  pushes harvest past the destination's MRL window are excluded.
- **MRL** (maximum residue limit) -- the destination market's MRL
  tables (EU, Japan, FSSAI) gate which active ingredients are even
  allowed.
- **RASFF historical rejection probability** -- ingredients with a
  history of EU/Japan/US import refusals get demoted or excluded for
  export segments.
- **CIB&RC registration** -- only India-registered active ingredients
  for mango are considered.

Tasks 6-12 progressively build these subsystems. Module map:

- :mod:`markets` -- MarketSegment enum + segment-to-MRL-table mapping
- :mod:`mrl_loader` -- YAML MRL tables loader (Task 6)
- :mod:`cibrc` -- CIB&RC registered-pesticide registry (Task 7)
- :mod:`rasff` -- RASFF historical-rejection analyzer (Task 8)
- :mod:`ranker` -- pesticide ranker by efficacy / half-life / cost (Task 11)
- :mod:`recommend` -- top-level orchestrator (Task 12)
"""
