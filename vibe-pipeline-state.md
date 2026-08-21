# Vibe Pipeline State

## Intake

- Idea: dashboard, weekly fire + landslide risk, Majalengka. Map-based, Leaflet, Google Satellite basemap, militaristic style.
- Track: **UI** (map dashboard).
- S1 doc type: **PRD.md**.
- Data on disk: `data/YYYY_WXX/` (2026_w30, w31, w34 — non-contiguous, some W34 rasters still `.mock` placeholders) + `data/kelurahan.geojson`. `DATABASE.md` documents target Postgres/PostGIS schema (14 tables) — repo is post-wipe, no `migrations/` or `shared/` code exists yet.

## Clarifying answers (asked before S1 draft)

- Data source: **Postgres/PostGIS DB per DATABASE.md** (not direct file read). v1 must build `migrations/0001_initial_schema.sql` + an ingest script (files → DB) since neither exists yet.
- Basemap: **Google Satellite, unofficial XYZ tiles** (no key; ToS risk flagged in PRD).
- Stack: **FastAPI (backend) + React/Leaflet (frontend)**.

## Stage status

- S1 `PRD.md` — approved 2026-08-20.
- S2 architecture.md — approved 2026-08-20.
- S3 mockup.html + images/ — approved 2026-08-20 (revised: dropped Both hazard tab, dropped MOCK/LIVE layer tags).
- S4 storyboard.md — approved 2026-08-20.
- S5 vibe-prompts/ — approved 2026-08-20 (revised: run-phase-NN.sh manual click-through launchers instead of automated assertion scripts). Ponytail level: **ultra**.

## Pipeline complete
CLAUDE.md + tasks/todo.md + tasks/lessons.md created 2026-08-20. Ready for Phase 1.

## Post-pipeline addition — 2026-08-21
User asked to skip straight to S5 for a new feature (map is currently
fully static: `dragging=false`/`scrollWheelZoom=false`/etc. in
`MapView.tsx`, against PRD.md's own pan/zoom performance note):
1. zoom in/out, 2. pan, 3. click-to-zoom.
Clarified with user: "click-to-zoom" target = kecamatan polygon (the
map's only real geo-accurate clickable layer — GridCellList rows have no
coordinates in any backend route). Pure frontend, no backend/migration
change.
Added `vibe-prompts/phase-10-map-navigation.md` + `scripts/run-phase-10.sh`,
renumbered the always-last observability/security-audit phases:
`phase-10-observability.md` → `phase-11-observability.md`,
`phase-11-security-audit.md` → `phase-12-security-audit.md` (their
`scripts/run-phase-NN.sh` names updated to match; neither had been
executed yet, so the rename was safe). `00-README.md`'s phase table
updated to match.
