# Vibe Coding Prompts — MATA Hazard Command

## One-time setup (Claude Code)
Install the ponytail plugin (two separate prompts):
    /plugin marketplace add DietrichGebert/ponytail
    /plugin install ponytail@ponytail
Ponytail level for this project: **ultra** (set with `/ponytail ultra`;
this stays active across sessions and is injected into subagents
automatically).

## Running a phase
Fresh Claude Code session (or `/clear`), then:
    Read vibe-prompts/phase-NN-<name>.md and execute it.
(Outside Claude Code, load the same file via Caveman.)

Run the phases IN ORDER, one per fresh session.
Before each phase: read CLAUDE.md for current build/test commands and state.
Only advance when the previous phase's automated tests pass, its manual
testing steps have been verified, and `/ponytail-review` came back clean.

| # | File | Scope | Verify by |
|---|------|-------|-----------|
| 01 | phase-01-container-init.md | docker-compose (Postgres/PostGIS, api, web), `.env`, `migrations/0001_initial_schema.sql` (14 DATABASE.md tables + `ingest_log` + `raster_overlay`), `shared/db.py`, `shared/boundary.py` stub, FastAPI skeleton with `/health`, Vite/React skeleton hitting it | `docker compose up -d`, all 3 containers healthy, `GET /health` returns `{"db":"ok"}`, blank React shell loads and shows the health status |
| 02 | phase-02-ui-shell-mocks.md | Full UI/UX layer per storyboard.md's 4 screens, react-leaflet + Google Satellite tiles, wired to local mock fixtures (no backend calls yet) | Every screen from storyboard.md is reachable and visually matches its `images/screen-NN-*.png`; all interactions (toggle, sliders, popup, export modal, alert click) work against mock data |
| 03 | phase-03-ingest-pipeline.md | `ingest.py` + `ingest/parsers/{fire,landslide,sar}.py` + `ingest/rasterize.py` — loads `data/2026_w30`, `_w31`, `_w34` into Postgres, writes colored PNG overlays, idempotent, records `ingest_log` rows | `python ingest.py data/2026_w34` (and w31, w30) populate DB tables + `generated/overlays/*.png`; re-running is a no-op (no duplicate rows); `ingest_log` shows correct OK/MOCK/MISSING per real file gaps |
| 04 | phase-04-fire-api.md | `GET /weeks`, `GET /boundaries`, `GET /fire/summary`, `GET /fire/grid`, `GET /fire/overlay/{layer}` | Each endpoint returns correct data for 2026-W34/W31/W30 against the ingested DB from phase 03; automated API tests pass |
| 05 | phase-05-landslide-api.md | `GET /landslide/summary`, `GET /landslide/grid`, `GET /landslide/overlay` | Same as phase 04 for the landslide tables; automated API tests pass |
| 06 | phase-06-alerts-cells-api.md | `GET /alerts`, `GET /cells/{hazard}/{spatial_id}` — HIGH-alert threshold logic (PRD Assumptions) and click-to-inspect detail | Alert counts match manually-verified counts from the ingested data; cell detail matches DB rows exactly |
| 07 | phase-07-map-live-integration.md | Command Map screen (Screen 1) switched from mock fixtures to real API calls; Empty Week (Screen 3) and Connection Error (Screen 4) wired to real `/weeks` results and real fetch failures | Selecting each real week shows correct overlays/counts; selecting a week with no data shows Screen 3; killing the API shows Screen 4 and Retry recovers |
| 08 | phase-08-ingest-log-live.md | `GET /ingest-status`, Ingest Log screen (Screen 2) wired to it | Screen 2 shows live per-file status matching `ingest_log` table contents for each week |
| 09 | phase-09-pdf-export.md | `POST /reports/pdf` (reportlab) + frontend export modal capturing a real map snapshot and downloading the returned PDF | Clicking Export produces a downloadable PDF containing the map image, per-kecamatan table, and HIGH-alert list for the current week/hazard |
| 10 | phase-10-map-navigation.md | Real Leaflet map interaction on Command Map: scroll/control zoom, drag-to-pan, double-click-zoom, kecamatan-click zooms/pans to that polygon's bounds (in addition to the existing inspect popup) | Scroll-zoom, drag-pan, double-click-zoom, and zoom-control buttons all work; clicking a kecamatan fits the map to it and still opens the popup |
| 11 | phase-11-observability.md | Structured JSON logging across `api` and `ingest.py`, `/health` DB probe (already scaffolded in phase 01, verified end-to-end here) | Log lines are valid JSON with timestamp/run-id; `/health` correctly reports DOWN when Postgres is stopped |
| 12 | phase-12-security-audit.md | Full post-build security audit — zero-trust checks, the 3 mandated audit prompts, no-auth-in-v1 posture confirmed as intentional and documented | All three audit prompts run and findings resolved or explicitly accepted with rationale in CLAUDE.md |

Every phase also ships `scripts/run-phase-NN.sh` — a one-command launcher
that stands the stack up (and loads sample data where relevant) and
prints exactly what URL to open and what to click or look at. These are
for you to eyeball the result yourself; they don't assert pass/fail —
that's what the "Verify by" column above and each phase file's Validation
Verification section are for.

Context files every session needs available: PRD.md, architecture.md,
storyboard.md, CLAUDE.md.
