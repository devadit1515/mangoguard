# MangoGuard Implementation Plans — Index

> All plans implement the canonical spec `docs/superpowers/specs/2026-05-30-mangoguard-design.md`. Execute in order, except where parallelism is explicitly marked.

| # | Plan | Implements spec § | Prerequisites | Tag at completion | Parallelizable with |
|---|------|------------------|---------------|---------------------|---------------------|
| 1 | [Foundation — repo scaffolding + schema + Connector ABC](2026-05-30-01-foundation.md) | O1 foundation | none | `v0.1.0` | — |
| 2 | [Free public baseline connectors (AGMARKNET, IMD, DBSKKV, CROPSAP, Sentinel-2)](2026-05-30-02-free-public-connectors.md) | O1 (free baselines) | Plan 1 | `v0.2.0` | Plan 3 |
| 3 | [Commercial connectors (Pessl, Fyllo, Fasal, Plantix, CSV fallback)](2026-05-30-03-commercial-connectors.md) | O1 (commercial) | Plan 1 | `v0.3.0` | Plan 2 |
| 4 | [**FOCAL** — Disease-risk engine + market-conditioned MRL recommender + evaluation harness](2026-05-30-04-risk-engine-recommender.md) | O2, O3 | Plans 1, 2 | `v0.4.0` | Plan 5 |
| 5 | [Supporting modules — disease detector + orchard-health + yield/price + chatbot](2026-05-30-05-supporting-modules.md) | O4, O5 | Plans 1, 2 | `v0.5.0` | Plan 4 |
| 6 | [Streamlit integration + field-validation logbook + report scaffolding](2026-05-30-06-dashboard-fieldwork-report.md) | O5 (UI), O6 | Plans 1-5 | `v1.0.0-rc1` | — |

## Recommended execution order

**Serial (single subagent):**
```
Plan 1 -> Plan 2 -> Plan 3 -> Plan 4 -> Plan 5 -> Plan 6
```

**Parallel (multiple subagents, faster wall-clock):**
```
Plan 1
├── Plan 2 ─┐
└── Plan 3 ─┤
            ├── Plan 4 ─┐
            └── Plan 5 ─┤
                        └── Plan 6
```

Plan 2 and Plan 3 share no code beyond the `Connector` base — one subagent on each.
Plan 4 and Plan 5 touch different module trees — one subagent on each.
Plan 6 must run last (integrates artifacts from all prior plans).

## How to execute a plan

Each plan is consumed by the `superpowers:subagent-driven-development` skill (recommended) or `superpowers:executing-plans` skill (inline batch execution).

Both skills:
1. Read the plan top to bottom.
2. Identify tasks marked `- [ ]`.
3. Run each step's commands (write tests, implement code, verify, commit) in order.
4. Update the checkbox to `- [x]` after each successful step.

## Total task counts

| Plan | Tasks | Steps per task (avg) | Approx total steps |
|------|-------|----------------------|---------------------|
| 1 | 6 | 7 | 42 |
| 2 | 9 | 5 | 45 |
| 3 | 9 | 5 | 45 |
| 4 | 18 | 4 | 72 |
| 5 | 17 | 4 | 68 |
| 6 | 14 | 4 | 56 |
| **Total** | **73 tasks** | — | **~328 steps** |

This is the ~70-hour CREST Gold project broken into 320 specific, atomic, testable steps.

## Acceptance criteria for "all plans complete"

- [ ] Tag `v1.0.0-rc1` exists in the repo.
- [ ] `pytest -v` shows 100% pass rate across all plans.
- [ ] All 6 Streamlit pages load without exceptions.
- [ ] All 15 CREST criteria have artifact evidence per the §6 evidence map in the spec.
- [ ] At least one farmer visit, one FPO demo, and one exporter interview logged.

Weeks 11-12 are pure report writing using `docs/crest_report/` templates.
