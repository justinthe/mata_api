# PRD — MATA Hazard Command

## Assumptions

Answered by user: data source = Postgres/PostGIS DB per `DATABASE.md`; basemap = Google Satellite (unofficial XYZ tiles); stack = FastAPI + React/Leaflet.

Left open, assumed here (flag if wrong):

- **DB doesn't exist yet.** Repo is a fresh wipe — no `migrations/`, no `shared/`. v1 therefore includes building `migrations/0001_initial_schema.sql` (per `DATABASE.md` schema) and a one-way ingest script that loads `data/YYYY_WXX/*.json|*.csv|*.tif` into Postgres. Dashboard API reads only from DB, never touches `data/` directly at request time.
- **Raster rendering: static PNG overlays, not dynamic tiling.** Sample TIFs are tiny (grid tif ~19KB, kecamatan tif ~1KB) — this is a coarse grid, not a high-res raster. Ingest converts each TIF to a colored PNG (per the color specs below) with its geo bounds, stored and served as a Leaflet `ImageOverlay`. No titiler/rio-tiler dynamic tile server needed for v1.
- **Alert / "needs attention" threshold:** Fire = `risk_tier == "HIGH"`. Landslide = `risk_category` in `{"Landslides Expected", "Active Landslides"}` (top 2 of the 5 DATABASE.md categories). "Combined alert" = a spatial unit HIGH on both hazards.
- **Week selector only lists ingested weeks.** Currently 3 non-contiguous sample weeks exist (2026-W30, W31, W34); some rasters in W34 are still `.mock` placeholders. UI must handle a week with partial/missing layers gracefully (grey out that layer, don't crash).
- **PDF export contents:** map snapshot (current view/layers) + per-kecamatan summary table (risk tier/category, counts) + list of HIGH/alert areas, for the selected week and hazard filter.
- **No authentication in v1** — single internal operator tool, not exposed publicly.
- **Google Satellite via unofficial XYZ endpoint** — free, no key, but undocumented/against Google's ToS; may break without notice. Flagged as a v1 risk, not a blocker.

## 1. Overview

MATA Hazard Command is an internal web dashboard that shows weekly fire and landslide risk across Majalengka Regency on a satellite map. It ingests weekly hazard model outputs (fire risk tiers, burned-area SAR detections, landslide risk scores) into a PostGIS database, then lets a BPBD-style operator pick a week, toggle hazard layers, inspect any grid/kecamatan cell's score, spot high-alert areas at a glance, and export a PDF summary for reporting.

## 2. Problem Statement

Fire and landslide risk model outputs currently land as raw JSON/CSV/GeoTIFF files per week, with no way to see them spatially or compare hazards side by side. An operator deciding where to send a field team, or a local government office preparing a weekly briefing, has no map, no at-a-glance alert view, and no exportable report — just files that need manual GIS work to interpret.

## 3. User Personas

**Andi — BPBD Field Coordinator**
Context: disaster management operator, checks the dashboard every week when new hazard data lands.
Goals: quickly see which kecamatan/grid cells are HIGH risk for fire or landslide (or both), decide where to send a field team.
Frustrations: raw CSV/TIF files require GIS tools to interpret; no single view combining both hazards.

**Sri — Kecamatan Government Analyst**
Context: prepares a weekly risk briefing for local government meetings.
Goals: pull a clean PDF summary for a given week without building it by hand.
Frustrations: currently assembles summaries manually from spreadsheets.

**Budi — System Operator**
Context: runs the weekly ingest after new `data/YYYY_WXX/` files land.
Goals: confidence the ingest succeeded, and a place to see what failed if a week's files are incomplete/mocked.
Frustrations: no visibility today into whether a given week's data is fully processed or partially placeholder.

## 4. Scope

### In Scope (v1)

- Postgres/PostGIS schema (`migrations/0001_initial_schema.sql`) + ingest script loading `data/YYYY_WXX/` files per DATABASE.md tables.
- Map view: Majalengka boundary delineation (kecamatan, from `kelurahan.geojson` dissolve), Google Satellite basemap.
- Hazard layer toggle: Fire / Landslide / Both.
- Week selector, populated from weeks present in DB.
- Per-layer opacity control: fire risk (grid + kecamatan), burned area, landslide risk.
- Raster overlays rendered with the specified color scheme:
  - Fire risk (grid & kecamatan tif): red=high, yellow=mid, green=low.
  - Burned area tif (band 1, 0.0–1.0): 0=red (burned), 0.5=yellow, 1=green.
  - Landslide risk tif (band 2, values 2/3/4): 2=red, 3=yellow, 4=green.
- Click-to-inspect: popup with score/tier/category and supporting metrics (hotspot/FRP for fire, factor breakdown for landslide) for the clicked grid/kecamatan.
- Alert summary panel: count of HIGH-alert areas (fire, landslide, combined) for the selected week, with zoom-to-area action.
- PDF export of current week + hazard-filter summary.
- Militaristic UI style: dark theme, high-contrast status colors, sharp/angular UI chrome, monospace data readouts.

### Out of Scope (v1)

- Authentication / user roles.
- Historical trend charts across weeks (single week at a time only).
- Real-time push alerts (email/SMS/webhook).
- Editing hazard data or re-running fire/landslide model pipelines from the dashboard (ingest is one-directional: files → DB).
- Any region beyond Majalengka.
- Mobile-native app (responsive web only).

## 5. Core Features

### F1 — Weekly data ingest

As Budi (System Operator), I want a script that loads a week's `data/YYYY_WXX/` files into Postgres, so the dashboard always reads from DB, never raw files.

- [ ] Reads all documented file types (fire_risk json, fire_sar_burned_area json/tif, fire_sar_result csv, fire_scores csv, fire_weekly_features csv, landslide_risk json/tif, landslide_scores/reclassified/static/dynamic csv) for a given `YYYY_WXX` folder.
- [ ] Writes rows into the matching DATABASE.md tables (`weekly_feature`, `fire_risk_prediction`, `sar_burned_area_detection`, `landslide_weekly_score`, `landslide_static_feature`, `landslide_dynamic_feature`, etc.), using `shared.db.write_rows`.
- [ ] Converts each risk/burned-area TIF to a colored PNG + bounds JSON per the color specs, stored for the API to serve.
- [ ] A week missing or `.mock`-only for a given layer ingests the layers it has and records the rest as absent, without failing the whole run.
- [ ] Re-running ingest for an already-ingested week is idempotent (no duplicate rows).

### F2 — Map with boundary + basemap

As Andi, I want a satellite map of Majalengka with kecamatan boundaries drawn, so I have spatial context for every hazard layer.

- [ ] Leaflet map centered/fit to Majalengka extent on load.
- [ ] Google Satellite basemap tiles.
- [ ] Kecamatan boundary polygons drawn from `kecamatan_boundary` (outline only, no fill, so imagery stays visible).

### F3 — Hazard layer selection + week selection

As Andi, I want to pick Fire and/or Landslide and a specific week, so I only see the data relevant to my current question.

- [ ] Toggle: Fire only / Landslide only / Both.
- [ ] Week dropdown lists only weeks present in DB, most recent first.
- [ ] Switching hazard or week updates all map overlays and the alert panel without a full page reload.

### F4 — Raster overlay rendering + opacity

As Andi, I want to see risk rasters color-coded on the map with adjustable opacity, so I can read risk at a glance without the basemap being obscured.

- [ ] Fire grid risk, fire kecamatan risk, burned area, landslide risk each render as their own toggleable `ImageOverlay` with correct color scheme.
- [ ] Each active layer has its own opacity slider (0–100%).
- [ ] A layer with no data for the selected week (missing/mock) shows as unavailable rather than a blank/broken overlay.

### F5 — Click-to-inspect

As Andi, I want to click any grid or kecamatan cell and see its numbers, so I can judge severity beyond just the color.

- [ ] Click on a fire layer shows: spatial unit id, risk tier, predicted next-week count, hotspot count/density, mean/max FRP (when available).
- [ ] Click on the landslide layer shows: grid id, `score_255`, `risk_category`, factor breakdown (slope/rainfall/ndvi/drainage/landuse/soil/aspect scores).
- [ ] Click on burned-area layer shows: burned area hectares for that detection, pixel-level burned fraction if within a pixel cell.
- [ ] Popup shown within 1 click, no extra navigation.

### F6 — Alert summary panel

As Andi, I want a running count of HIGH-risk areas, so I don't have to visually scan the whole map to know if anything needs attention.

- [ ] Panel shows count of HIGH fire areas, HIGH/Active landslide areas, and combined-alert areas, for the selected week.
- [ ] Each count is clickable and zooms/pans the map to fit those areas.
- [ ] Panel updates live when hazard/week selection changes.

### F7 — PDF export

As Sri, I want to export a PDF summary for the current week and hazard selection, so I can hand it to a meeting without manual assembly.

- [ ] Export button generates a PDF containing: map snapshot, per-kecamatan risk table, list of HIGH-alert areas, for the currently selected week + hazard filter.
- [ ] PDF generation completes without blocking the UI (async / spinner state).
- [ ] Downloaded file is named with the week and hazard filter (e.g. `mata-hazard-2026-W34-fire.pdf`).

## 6. User Flows

1. Operator opens dashboard → latest available week auto-selected → map loads with both hazards, boundary, satellite basemap.
2. Operator toggles hazard filter (Fire / Landslide / Both) → overlays and alert panel update.
3. Operator changes week via dropdown → overlays and alert panel refresh for that week; unavailable layers shown as such.
4. Operator adjusts opacity slider on a layer → overlay redraws at new opacity, no re-fetch.
5. Operator clicks a grid/kecamatan cell → popup shows score/tier/category and supporting metrics.
6. Operator opens alert panel, clicks a HIGH-count entry → map zooms/pans to those areas.
7. Operator clicks Export PDF → report generates and downloads for current week + hazard filter.
8. (Operator role) Budi runs ingest script for a new `data/YYYY_WXX/` folder → new week appears in the dashboard's week dropdown.

## 7. Success Metrics

- All 3 sample weeks (2026-W30, W31, W34) ingest and render without error, including weeks with `.mock` placeholder rasters.
- Map + default week overlays visible within 3s on a typical broadband connection.
- Switching week or hazard filter updates the map in under 1s (data already ingested, no re-processing).
- PDF export completes in under 10s and contains every HIGH-alert area shown in the panel at export time.
- Every documented color scheme (fire risk, burned area, landslide risk) renders exactly as specified — verifiable by sampling overlay pixel colors against known score values.

## 8. Non-Functional Requirements

- **Performance:** raster PNGs pre-generated at ingest time, not rendered per-request; map interactions (pan/zoom/opacity) stay client-side.
- **Security:** internal network use only for v1 (no auth); ingest script is the only write path to DB, dashboard API is read-only.
- **Accessibility:** red/yellow/green risk legend always paired with a text label (tier/category name), not color alone, for color-blind readability.
- **Observability:** ingest run outcome (per-week, per-file-type success/failure/mock) logged and visible to the operator, reusing the `acquisition_log`-style pattern from DATABASE.md.
- **Style:** dark background, high-contrast alert colors (red/yellow/green kept saturated against dark UI), angular/sharp panel chrome, monospace font for data readouts and coordinates — militaristic command-center look.
