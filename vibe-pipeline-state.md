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

## Post-pipeline addition — 2026-08-22
User asked for a mobile-responsive redesign ("fits on a mobile phone
screen ... user can see everything all important information"). Chose
**full revise** route (not the Phase-10-style S5-only fast-track) since
this is a visual change — mockup needed to show the target phone layout
before a build phase is written.
- S3 `mockup.html` — revised: added `@media (max-width:480px)` block.
  Dashboard reorders to map → alert summary/buttons → filters (CSS
  `order`, flex column) so the map + all 3 alert counts are visible
  before scrolling past filter chrome. Ingest Log table wrapped in a
  `.table-scroll` div (`overflow-x:auto`, table `min-width:480px`) so
  columns scroll instead of crushing. Export modal width clamped to
  `calc(100vw - 32px)`. Approved 2026-08-22.
- `images/` (desktop, 1440px) re-rendered via the bundled
  `screenshot-mockup.mjs` — byte-identical to before (media query is
  phone-only, doesn't touch the 1440px capture).
- `images/mobile/` (new, 390×844) added via a one-off local script
  (`screenshot-mockup-mobile.mjs`, not part of the bundled skill,
  deleted after use — re-create by copying `screenshot-mockup.mjs` and
  swapping the viewport + output path if phone shots are needed again).
  Confirms the reorder and table-scroll actually render correctly.
  Root `package.json`/`package-lock.json`/`node_modules` that `npm i
  playwright` created as a side effect were deleted after — this repo
  has no root Node project, only `frontend/`.
- S4 `storyboard.md` — revised: added a "Mobile (≤480px)" subsection
  per screen embedding the matching `images/mobile/*.png` and one-line
  reflow description; noted in the Journey Summary that the phone
  journey is identical, layout-only.
- S5: added `vibe-prompts/phase-13-mobile-responsive.md` +
  `00-README.md` phase table row — same "extend, don't touch built
  phases" pattern as Phase 10, not a full vibe-prompts regeneration.
  Ports the mockup's phone breakpoint into `frontend/src/theme.css` +
  `IngestLogScreen.tsx`'s table wrapper. Not yet executed — run via
  `Read vibe-prompts/phase-13-mobile-responsive.md and execute it` in a
  fresh Claude Code session once ready to build.
