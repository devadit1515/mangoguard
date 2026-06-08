---
title: MangoGuard
emoji: 🥭
colorFrom: yellow
colorTo: red
sdk: streamlit
sdk_version: "1.34.0"
app_file: streamlit_app.py
pinned: false
license: mit
short_description: AI orchard-management & MRL-aware spray-audit system for Indian Alphonso mango growers.
---

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
