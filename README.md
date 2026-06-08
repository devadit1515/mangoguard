# MangoGuard

AI orchard-management & MRL-aware spray-audit system for mid-sized Indian Alphonso mango growers.
CREST Gold Award project, 12-week solo build, summer 2026.

## Where to read first
1. `CLAUDE.md` — project memory
2. `docs/superpowers/specs/2026-05-30-mangoguard-design.md` — canonical design spec
3. `docs/superpowers/plans/` — implementation plans

## Install (dev)

```bash
pip install -e ".[dev,ml,geo,dashboard,scrape,llm]"
pre-commit install
```

## Run tests

```bash
pytest
```

## Status
v0.0.1 — foundation only. See `docs/superpowers/plans/` for what's next.
