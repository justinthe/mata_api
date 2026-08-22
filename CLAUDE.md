# MATA Hazard Command

Internal web dashboard showing weekly fire and landslide risk across Majalengka Regency on a satellite map, with click-to-inspect scoring, HIGH-alert summaries, and PDF report export.

## Project State
- Build commands: `./scripts/run-phase-01.sh` (starts the shared postgres if
  down, applies `migrations/0001_initial_schema.sql`, then
  `docker compose up -d --build`), `./scripts/run-phase-02.sh` (same
  container startup, plus a manual click-through checklist for the UI),
  `./scripts/run-phase-03.sh` (applies the migration, builds the `api`
  image, runs `ingest.py` against all 3 real sample weeks in sequence,
  prints a `psql` one-liner + the list of generated overlay PNGs for manual
  eyeballing), `./scripts/run-phase-04.sh` (same preamble, re-runs
  `ingest.py` for all 3 weeks to keep `ingest_log`/`raster_overlay` in sync
  with whatever's currently on disk, then prints the Swagger docs URL +
  example fire-API URLs to eyeball), or `./scripts/run-phase-05.sh` (same
  shared-postgres-start + migration + `docker compose up -d --build`
  preamble as phase-04, minus the ingest re-run — Phase 05 touched no
  `data/` files — then prints the Swagger docs URL + example landslide-API
  URLs), or `./scripts/run-phase-06.sh` (same preamble as phase-05, then
  prints the Swagger docs URL + example `/alerts` and `/cells` URLs), or
  `./scripts/run-phase-07.sh` (same shared-postgres-start + migration +
  `docker compose up -d --build` preamble, runs `ingest.py` for all 3 weeks
  only if `ingest_log` is empty — fast re-runs otherwise — then prints the
  frontend URL + a manual click-through checklist for real week/hazard
  switching, opacity, click-to-inspect, alerts, Empty Week, and Connection
  Error/Retry), or `./scripts/run-phase-08.sh` (same shared-postgres-start +
  migration + `docker compose up -d --build` preamble, no ingest re-run
  needed — Phase 08 touched no `data/` files — then prints the frontend URL
  + a manual click-through checklist for the Ingest Log screen across all 4
  weeks), or `./scripts/run-phase-09.sh` (same shared-postgres-start +
  migration + `docker compose up -d --build` preamble as phase-08, ingests
  the 3 sample weeks only if `ingest_log` is empty, then prints the frontend
  URL + a manual click-through checklist for generating and opening a real
  PDF report for both hazards), or `./scripts/run-phase-10.sh` (same
  shared-postgres-start + migration + `docker compose up -d --build`
  preamble as phase-09, ingests the 3 sample weeks only if `ingest_log` is
  empty, then prints the frontend URL + a manual click-through checklist for
  scroll-zoom, drag-pan, double-click-zoom, the zoom-control buttons, and
  kecamatan-click-to-zoom), or `./scripts/run-phase-13.sh` (same
  shared-postgres-start + migration + `docker compose up -d --build`
  preamble as phase-10, ingests the 3 sample weeks only if `ingest_log` is
  empty, then prints the frontend URL + a manual click-through checklist for
  the ≤480px phone layout: scroll order, header fit, Ingest Log table
  scroll, Empty/Error text padding, and unaffected 900px/desktop layouts).
  Frontend: http://localhost:5173.
  Backend health check: http://localhost:8001/health, fire API base:
  http://localhost:8001 — no `/api` prefix, e.g.
  http://localhost:8001/fire/summary?week=2026-W34 (host port 8001, not
  8000 — 8000 is taken by an unrelated local project). `ingest.py` itself
  runs as a one-off inside the `api` container:
  `docker compose run --rm api python ingest.py data/2026_wXX`. Landslide
  API base is the same host:port, e.g.
  http://localhost:8001/landslide/summary?week=2026-W31 — no separate port
  or prefix, same FastAPI app as fire.
- Test commands: `docker compose run --rm api pytest` (backend + ingest,
  against the real shared DB — includes idempotent-re-ingest and
  partial-week-tolerance tests that actually run `ingest.py`, plus Phase
  04's route tests in `backend/tests/test_weeks_boundaries.py` and
  `test_fire.py`, Phase 05's `test_landslide.py`, Phase 06's
  `test_alerts.py`/`test_cells.py`, Phase 08's `test_ingest_status.py`, and
  Phase 09's `test_reports.py`);
  frontend
  `cd frontend && npm test` (Vitest + RTL) and `npm run typecheck`
  (tsc --noEmit). Backend code is baked into the `api` image at build time
  (no live volume mount for `backend/`) — after editing backend code, run
  `docker compose build api` before `docker compose run --rm api pytest`
  or the container will run stale code. Frontend tests stub `fetch` (no
  `msw`/mock-server dependency) via `frontend/src/api/mockFetch.ts`'s
  `installMockFetch("ok"|"down")`, auto-installed in "ok" mode before every
  test by `vitest.setup.ts`; call it again inside a test to override (a
  different mode, or to hold a reference and assert on calls). That same
  setup file also shims `SVGElement.prototype.createSVGRect` — jsdom has no
  SVG geometry engine, and without this shim Leaflet's `Browser.svg`
  feature-detect fails and any vector layer (`react-leaflet`'s `<GeoJSON>`,
  used for the kecamatan boundary layer since Phase 07) crashes on
  mount/unmount.
- Postgres/PostGIS is NOT a service in this repo's `docker-compose.yml` — it
  is the existing shared `mata_api_algo-postgres-1` container. See memory /
  `docker-compose.yml`'s top comment before adding a `postgres` service.
- Current phase: Phase 05 complete (`backend/app/routers/landslide.py` — 3
  read-only routes: `/landslide/summary`, `/landslide/grid`,
  `/landslide/overlay` — reading only `landslide_weekly_score`,
  `landslide_static_feature`, `landslide_dynamic_feature`, `raster_overlay`,
  `ingest_log`, same pattern as Phase 04's fire routes).
- Current phase: Phase 06 complete (`backend/app/routers/alerts.py` — 1
  route: `GET /alerts?week=&hazard=`; `backend/app/routers/cells.py` — 1
  route: `GET /cells/{hazard}/{spatial_id}?week=`. Both reuse Phase 04/05's
  `fire.py`/`landslide.py` functions — no new SQL, no changes to those two
  files). Ready for Phase 07.
- Current phase: Phase 07 complete (Command Map screen wired to the real
  API — `frontend/src/api/client.ts` replaces every `mocks/*.ts` data call
  for Command Map; `mocks/cells.ts`/`overlays.ts` deleted as dead code,
  `mocks/weeks.ts`/`ingest.ts`/`api.ts` untouched, still used by Phase
  08/09's screens — `mocks/api.ts` deleted in Phase 09, see below). Ready for
  Phase 08.
- Current phase: Phase 08 complete (`backend/app/routers/ingest_status.py`
  — 1 route: `GET /ingest-status?week=`, returns `{file_type, status,
  detail}` rows straight from `ingest_log`, `weeks.py`-style minimalism —
  no week validation, no Pydantic model, unknown week just yields `[]` at
  200. Screen 2 (`IngestLogScreen.tsx`) now fetches this instead of reading
  `mocks/ingest.ts`'s fake `INGEST_STATUS`). Ready for Phase 09.
- Current phase: Phase 09 complete (`backend/app/routers/reports.py` — 1
  route: `POST /reports/pdf`, body `{week, hazard: "fire"|"landslide",
  map_image_base64}`. Calls `fire.fire_summary()`/`landslide.landslide_summary()`
  for the per-kecamatan table and `alerts.alerts()` for the HIGH-alert list —
  no new alert/summary logic, same cross-import pattern `alerts.py`/`cells.py`
  already use. Composes the PDF via `reportlab.platypus` (`SimpleDocTemplate`
  + `Image`/`Table`/`Paragraph`). `reportlab` was named by architecture.md §2
  but never actually added to `backend/requirements.txt` until now; `pypdf`
  was added alongside it, test-only, to read the generated PDF's text back
  for `test_reports.py`'s content-match assertions. Frontend:
  `ExportModal.tsx` now captures a real map snapshot and does a real
  POST+download, replacing the Phase 02 `setTimeout` mock; `mocks/api.ts`
  (its only content was the mocked `postReportsPdf`) is deleted.
- Current phase: Phase 10 complete (`frontend/src/components/MapView.tsx` —
  `MapContainer`'s `dragging`/`scrollWheelZoom`/`doubleClickZoom`/`boxZoom`/
  `touchZoom`/`keyboard` flipped from hardcoded `false` to `true`; an
  explicit `<ZoomControl position="topright"/>` replaces the disabled
  `zoomControl` prop; `onEachKec`'s click handler now also calls
  `mapRef.current.fitBounds(layer.getBounds(), {padding:[40,40]})` after
  `openPopup(...)`, using the same Phase 09 `mapRef` — no new state, no new
  library, no backend change). Frontend-only phase, no ingest impact. Ready
  for Phase 11 (if any).
  Notable Phase 10 decisions/gotchas:
  - **All four map corners were already occupied** by `.map-title`/
    `.compass`/`.map-hud`/`.map-legend` (each `position:absolute` with
    `z-index:20`), while Leaflet's own controls render inside
    `.leaflet-container`, which has `z-index:0` and — per the Phase 03-era
    `ImageOverlay`-pane lesson in `tasks/lessons.md` — establishes its own
    stacking context, so its children lose to any geometrically-overlapping
    sibling div regardless of Leaflet's internal control z-index. Placed
    `<ZoomControl position="topright"/>` and added one CSS rule
    (`frontend/src/theme.css`: `.map-wrap .leaflet-top.leaflet-right
    .leaflet-control-zoom { margin-top: 54px; }`) to push it below the
    34px-tall `.compass` box instead of relying on z-index.
  - `activeBounds`/`bounds`/`boundsOptions` (the initial-view-fit logic from
    Phase 07) is untouched — `fitBounds` on kecamatan click is real user
    interaction layered on top, same distinction the phase prompt drew.
  - **No `react-leaflet`/`leaflet` mocking exists anywhere in this repo** —
    every MapView-touching test renders the real `<App/>` with real Leaflet
    in jsdom. The two new interaction tests in
    `frontend/src/screens/CommandMapScreen.test.tsx` follow that same
    pattern rather than introducing mocks: `vi.spyOn(L.Map.prototype,
    "initialize")` (Leaflet's real per-instance constructor hook, confirmed
    at `leaflet/dist/leaflet-src.js:3145,3239` — not in `@types/leaflet`'s
    public surface, hence a local cast) captures the exact options object
    react-leaflet hands to Leaflet, verifying the interaction props for
    real; `vi.spyOn(L.Map.prototype, "fitBounds")` + a real `user.click()`
    on a rendered `.leaflet-overlay-pane path` verifies the click-to-zoom
    behavior plus that the existing inspect popup (`"Spatial Unit"` text)
    still opens on the same click — both run their real, un-mocked
    implementations, no stubbing was needed even under jsdom's zero-size
    container.
  Notable Phase 09 decisions/gotchas:
  - **No Leaflet map ref existed anywhere in the frontend before this
    phase** — added `mapRef` (`RefObject<LeafletMap | null>`) to
    `DashboardContextValue`, created in `CommandMapScreen.tsx`, attached to
    `MapView.tsx`'s `<MapContainer ref={mapRef}>`. react-leaflet v4 types
    that prop as non-nullable (`RefObject<Map>`) even though it's genuinely
    `null` before mount — a cast at the JSX call site works around this
    known upstream typing gap; not a runtime concern.
  - **Map snapshot capture uses `html2canvas`, not `leaflet-image`** —
    architecture.md §8 named `leaflet-image`, but it's unmaintained and
    fragile against modern Leaflet; the phase prompt itself allows "or an
    equivalent canvas capture," so this is an in-bounds substitution. New
    `dependencies` entry, nothing already installed covered this.
  - **Known ceiling, not a bug**: the base satellite tile layer
    (`mt{s}.google.com`) has no CORS headers, so `html2canvas` will likely
    render that layer blank/grey in the captured snapshot (canvas taint)
    while the same-origin overlay PNGs (`/generated/...`) and the vector
    kecamatan boundary layer — the actual hazard data — still capture
    correctly. `run-phase-09.sh`'s manual checklist calls this out
    explicitly. Upgrade path if it matters: proxy tiles through the `api`
    container to make them same-origin.
  - `ExportModal.test.tsx`'s old assertion on the transient "COMPILING
    REPORT..." spinner text was dropped — the mocked capture+POST both
    resolve within a single `act()` flush (no macrotask boundary like the
    old `setTimeout` mock had), so the intermediate state isn't reliably
    observable; the test asserts the reachable end state (`READY:` +
    filename, `URL.createObjectURL` called) instead.
  - `ExportModal.test.tsx` assigns `URL.createObjectURL`/`revokeObjectURL`
    directly (jsdom has neither) rather than replacing the global `URL`
    object — an earlier attempt at `vi.stubGlobal("URL", {...})` broke `new
    URL(...)`, used internally by `mockFetch.ts`'s `route()`, causing every
    GET in the test to fail as a false "connection error." Same "don't
    replace a whole global to shim one missing method" lesson as
    `vitest.setup.ts`'s narrower `SVGElement.prototype.createSVGRect` shim.
  Notable Phase 08 decisions/gotchas:
  - The old mock fixture (`mocks/ingest.ts`'s `INGEST_FILES`) was stale
    against reality on two counts: it used glob-style `file_type` names
    (`"fire_risk_*.json"`) instead of `ingest/orchestrate.py`'s real
    `FILE_TYPES` keys (`"fire_risk_json"`), and its item order didn't match
    `FILE_TYPES`' order for items 4-8. It also hardcoded W34's kecamatan tif
    as `"mock"` status, which was already wrong before this phase — Phase
    04's note documents that file's `.mock` sidecar was deleted, so it's
    real/`ok` in the live DB; only `landslide_risk_tif` is genuinely
    `mock_placeholder` for W34. Replaced with `FILE_TYPE_INFO` (still in
    `mocks/ingest.ts`, no longer literal mock *data* — just the static
    file_type→description lookup the DB has no column for), keyed and
    ordered to match `orchestrate.py`'s `FILE_TYPES` exactly.
  - `IngestLogScreen` joins the live API rows to `FILE_TYPE_INFO` by
    `file_type` and renders only rows the API actually returned (no
    client-side backfill of synthetic "missing" rows for an unseeded week)
    — for `2026-W99` this means an empty table, not 14 fabricated MISSING
    rows like the old mock produced.
  Notable Phase 07 decisions/gotchas:
  - **No backend route exposes lat/lon for individual grid cells.**
    `/fire/grid` (~1450 GRID-type rows/week) and `/landslide/grid` (50
    rows) return only `grid_id` + tier/score — `landslide_grid_cell.geom`
    exists in the DB but no route projects it, and fire's 1km `grid_cell`
    table has 0 rows (Phase 06 note). The only real geometry available is
    kecamatan polygons via `/boundaries`. Since backend routes are frozen
    this phase, **explicit user decision**: kecamatan polygons
    (`MapView.tsx`'s `<GeoJSON>` layer) are the only real, geo-accurate,
    clickable map layer; grid-tier click-to-inspect (fire's ~1450 cells,
    landslide's 50) moved to a new non-map scrollable list,
    `components/GridCellList.tsx`, in the left sidebar. The old fixed
    14×9 abstract div-grid (`mocks/cells.ts::genCells`, never geo-accurate
    either) is gone entirely, not ported forward.
  - Same gap means PRD F5's burned-area per-detection hectares/pixel-
    fraction click detail has no backing route and isn't implemented —
    `burned` stays a raster-only overlay layer with no click target, same
    "route doesn't exist" honesty as the grid-geometry gap above.
  - Alert flashing (`AlertPanel`'s `flashAlerts`) splits by hazard because
    `/alerts`' returned ids aren't uniformly map-plottable: `hazard=fire`
    mixes GRID+KECAMATAN ids server-side (`alerts.py::_fire_high_ids`,
    `kecamatan_only=False`) so only the kecamatan-tier subset actually
    highlights on the map (the alert card's **count** is still the real
    unfiltered total); `hazard=combined` is kecamatan-only server-side
    already (Phase 06) so all ids flash on the map; `hazard=landslide`
    returns raw `grid_id`s only, never kecamatan, so it flashes matching
    rows in `GridCellList` instead (`.gcl-row.flash`), not the map.
  - `/cells/landslide/{id}` only accepts a `grid_id` (404s on a kecamatan
    id — `cells.py::_landslide_cell` queries `landslide_weekly_score` by
    `grid_id`). `InspectPopup`'s kecamatan-tier landslide popup therefore
    reads the matching row straight out of the already-fetched
    `/landslide/summary`'s `by_kecamatan` instead of calling `/cells` —
    coarser (`mean_score_255`/`highest_category` only, no factor
    breakdown) but real, and avoids a 404.
  - Conversely `/cells/fire/{id}` does **not** filter by spatial type
    (`cells.py::_fire_cell` matches on `spatial_unit_id` regardless of
    GRID vs KECAMATAN) — `InspectPopup`'s `kind:"fire"` branch is a single
    code path for both the map's kecamatan clicks and the list's grid
    clicks.
  - `landslide_weekly_score.risk_category` isn't a fixed enum (Phase 05
    note) so kecamatan polygon/list coloring can't match category strings
    — `types.ts::landslideTierClass` buckets by `score_255` thresholds
    (≥180 high, ≥60 med) instead, a ponytail-flagged heuristic with no
    real DB-derived threshold source; revisit if a real severity cutoff
    surfaces.
  - jsdom has no SVG geometry engine — `react-leaflet`'s `<GeoJSON>` layer
    (new this phase) crashed every test that mounted `MapView` until
    `vitest.setup.ts` shimmed `SVGElement.prototype.createSVGRect` (see
    Test commands note above). Leaflet feature-detects SVG support via
    exactly that method; without it `Browser.svg` is `false` and
    `map._createRenderer()` returns `null`, crashing on add/remove.
  - Frontend tests stub `fetch` directly (`api/mockFetch.ts`,
    `installMockFetch`) rather than adding `msw` — no new dependency,
    matches ponytail's stdlib/native-first rung.
  Notable Phase 06 decisions/gotchas:
  - `hazard` on `/alerts` is a required filter (`fire|landslide|combined`)
    — one hazard's `{iso_week, hazard, count, spatial_unit_ids}` per call,
    not all three bundled in one response. The frontend (Phase 07) calls it
    3× to fill the Alert Summary panel's 3 cards.
  - "Combined" alert is **kecamatan-only**, not a live PostGIS spatial join
    — `grid_cell` (fire's 1km grid geometry table) has **0 rows** in the
    live DB, confirmed live; no phase populates it, so there's nothing on
    the fire side to `ST_Intersects` against. Combined = fire's
    `KECAMATAN`-tier `risk_tier=="HIGH"` ids ∩ landslide alert-category
    grid cells rolled up to kecamatan via `landslide._grid_kecamatan_map()`.
    Explicit user decision after finding the empty table.
  - `/cells/fire/{id}`'s 4 extra PRD F5 fields (`hotspot_count`,
    `hotspot_density`, `mean_frp`, `max_frp`) come straight out of
    `fire._predictions_for_week()`'s already-fetched `feature_by_id` dict
    (real columns on `weekly_feature`, just never projected by any Phase 04
    route) — no new query, and `fire.py` itself stays untouched per the
    scope boundary.
  - The phase build prompt's own text (and a stale CLAUDE.md/DATABASE.md
    claim) said `/cells/landslide/LS-00250?week=2026-W31` should return
    `score_255` 83.0 — **wrong against the live DB**: 2026-W31's
    `landslide_weekly_score` is 100% `risk_category=masked`/`score_255=0.0`,
    and `LS-00250` isn't even a `grid_id` in that week's rows. The real
    `highest_risk_cell` live is `LS-00019`/week `2026-W30`/`score_255=92.0`
    (`risk_category="Landslides Expected"`) — tests and
    `scripts/run-phase-06.sh`'s example URL both use this instead. Same
    "docs sketch isn't ground truth" pattern as Phase 01's port/postgres
    surprise (`tasks/lessons.md`) — real data over a stale doc claim,
    confirmed live before trusting it.
  - No real sample week has a kecamatan `HIGH` on both hazards at once —
    `test_combined_alerts_w31_kecamatan_scoped_and_empty` asserts the
    response shape and `KEC-*`-only ids rather than a nonzero count, since
    none exists in the real data.
  Notable Phase 05 decisions/gotchas:
  - `landslide_grid_cell`'s 50 real cells are **not** uniformly sized
    (`ST_Area(geom::geography)/10000` ranges ~0.09–1.0 ha) — `/landslide/
    summary`'s `area_by_category_ha` sums real per-cell geodesic area via
    one raw `ST_Area(geom::geography)` SQL query
    (`landslide.py::_area_ha_by_grid`), not `count * constant`.
  - `risk_category` is not a fixed small enum like fire's LOW/MEDIUM/HIGH
    tiers — DATABASE.md documents "5 categories + masked", and real weekly
    score rows can be 100% `masked` (W31) or split across just 2 of the 5
    named categories (W30) — `count_by_category` is a live `Counter` over
    whatever's actually in `landslide_weekly_score` for the week, not a
    hardcoded tuple.
  - `/landslide/summary`'s `by_kecamatan.highest_category` is the
    `risk_category` of that kecamatan's max-`score_255` row (same
    max-by-score logic as `highest_risk_cell`), not a hardcoded severity-name
    ordering — avoids needing to guess/hardcode the 5 categories' exact
    string spelling and ordinal rank.
  - `/landslide/overlay` takes no `{layer}` path segment (unlike
    `/fire/overlay/{layer}`) — `raster_overlay.layer_type = 'landslide_risk'`
    is the only landslide overlay layer, no per-kecamatan variant.
  - `/landslide/overlay` always returns HTTP 200 with a `status` field —
    same always-200 contract as `/fire/overlay/{layer}` (see Phase 04 note
    below). The original phase-05 build prompt's text said "404-with-status
    if `mock_placeholder` or `missing`"; this was deliberately overridden in
    favor of matching the already-shipped fire contract, confirmed with the
    user before implementing. W34's `landslide_risk_tif` is a **real**
    `mock_placeholder` (`ingest_log` status), not a synthetic test row like
    fire's Phase 04 test needed.
  - `landslide_static_feature` has no `iso_week` column (slope/aspect/etc.
    are static per grid cell, ingested once); `landslide_dynamic_feature`
    does (rainfall/ndvi are per-week). `/landslide/grid` joins both by
    `grid_id` (+ `iso_week` for dynamic) in Python, same dict-lookup style
    as `fire.py`'s `_predictions_for_week`.
  Notable Phase 04 decisions/gotchas:
  - Two `.mock` sidecar files (`fire_risk_2026-W34_kecamatan.tif.mock`,
    `fire_sar_burned_area_2026-W34.tif.mock`) were removed this phase —
    real `.tif` files already superseded them and `classify_files()` always
    prefers a real file over its `.mock` sidecar, so those two were already
    dead weight. Consequence: **no fire-scope layer/week combination is
    naturally `mock_placeholder` in the real sample data any more** (only
    `landslide_risk_tif` for W34 still is, out of this phase's scope) —
    `test_fire.py::test_overlay_surfaces_mock_placeholder_status` covers
    that status via a synthetic `ingest_log` row instead of real W34 data.
  - `/fire/overlay/{layer}` always returns HTTP 200 with a `status` field
    (`ok`/`mock_placeholder`/`missing`/`error`), never a bare 404 — an
    uningested layer for a given week is an expected UI state (PRD F4:
    "shows as unavailable"), not an error condition. Explicit user decision.
  - `count_by_tier`/`highest_predicted` in `/fire/summary` are computed
    over **all** `fire_risk_prediction` rows for the week (GRID+KECAMATAN
    combined), not GRID-only — confirmed against the real sample
    `fire_risk_2026-W31.json`, whose own `count_by_tier` is the literal
    tally across all 1475 `fire_scores_2026-W31.csv` rows of both types.
  - `run-phase-04.sh` re-runs `ingest.py` for all 3 weeks before printing
    URLs (same as `run-phase-03.sh`) so `ingest_log`/`raster_overlay` stay
    in sync with the `.mock` deletion above — skipping this step would
    leave stale `mock_placeholder` rows in the DB even though the files on
    disk no longer justify them.
  Notable Phase 03 decisions/gotchas (see code comments at each site):
  - No hazard table except `raster_overlay(iso_week, layer_type)` has a
    real UNIQUE constraint on its natural key — idempotency is app-level
    delete-then-insert everywhere else (`shared/db.py::delete_rows`).
    `kecamatan_boundary`'s own PK *is* its natural key, so it gets a real
    upsert (`shared/db.py::upsert_rows`) instead — delete-then-insert there
    would violate `landslide_grid_cell`'s FK to it mid-run.
  - The shared DB's `landslide_grid_cell` only has 50 of the 500 real grid
    cells (bootstrapped by the sibling `mata_api_algo` project, out of this
    repo's scope, no geometry source here to fill the rest) — landslide rows
    referencing a missing `grid_id` are skipped and counted in
    `ingest_log.detail`, not treated as a failure.
  - Real Majalengka has only 26 kecamatan, but the sample hazard data
    references 45 ids — `shared/boundary.py::MAJALENGKA_KECAMATAN` hardcodes
    the authoritative 45-id/name roster (from `fire_risk_*.json`'s
    `by_kecamatan`); 19 of the 45 boundary polygons legitimately sit outside
    real Majalengka on the map (borrowed from neighboring regencies by the
    synthetic data generator).
  - `ingest.py` (top-level CLI script) and the `ingest/` package can't both
    be `import`ed as `ingest` — Python resolves the collision to the
    package. All real logic lives in `ingest/orchestrate.py`; `ingest.py`
    is a 3-line shim (`python ingest.py ...` still works fine, since a
    script's own execution doesn't go through that import path).
  - Source polygons in `kelurahan.geojson` are 3D (`POLYGON Z`) but
    `kecamatan_boundary.geom` is 2D — flattened via `shapely.force_2d`.
  - `rasterio`'s wheel needs `libexpat1`, not present in the `python:3.12-slim`
    base image — installed via `apt-get` in `backend/Dockerfile`.
- Current phase: Phase 13 complete (`frontend/src/theme.css` — new
  `@media (max-width:480px)` block ported verbatim from `mockup.html`'s
  already-approved phone breakpoint: `#dashboard .layout` switches to a
  flex column ordering `.map-wrap`(1, 42vh) → `aside.right`(2) →
  `aside:not(.right)`(3) so the map + all 3 alert cards are visible before
  any scrolling past filters; header/nav/HUD/legend/compass text shrinks;
  `.popup-card` and `.modal` width-clamp to the viewport; `.empty-body`/
  `.error-body` get side padding + a text max-width. `IngestLogScreen.tsx`'s
  `<table>` is now wrapped in `<div className="table-scroll">` so it
  scrolls horizontally at `min-width:480px` instead of crushing columns —
  same `.table-scroll`/`table{min-width:480px}` split the mockup uses.
  Frontend-only phase, no ingest/backend impact — the existing 900px tablet
  block is untouched.
  Notable Phase 13 decisions/gotchas:
  - The mockup's phone-block rules for the empty/error screens are scoped
    `#empty-week .empty-body{...}`/`#error-state .error-body{...}` (its
    screens live inside those id'd `<section>`s); the real app's
    `EmptyWeekScreen.tsx`/`ErrorScreen.tsx` render `.empty-body`/
    `.error-body` as the section's direct child with no such nesting need,
    and `theme.css` already declares those two classes bare, unprefixed
    (lines ~161-174, pre-dating this phase). Ported the mockup's *values*
    with the *existing* bare selectors, not the mockup's id-prefixed ones —
    same "port values, fix selectors to match reality" pattern as prior
    phases' notes below.
  - Vite 5.4/Vitest 2.1 in this repo does not honor a `?raw` query on `.css`
    imports (the CSS plugin claims the request by extension before any
    asset/raw-query handling runs, so `import css from "./theme.css?raw"`
    silently resolves to an empty string) — `theme.css.test.ts` reads the
    stylesheet via `node:fs` instead. `@types/node` isn't installed in this
    frontend, so `frontend/src/node-shim.d.ts` declares just the two
    ambient types (`readFileSync`, `__dirname`) that test needs, rather
    than adding the dependency for one file.
- Phase prompts: see vibe-prompts/00-README.md for run order.

## Key Context Files
- PRD.md · architecture.md · storyboard.md + images/
- DATABASE.md (target Postgres/PostGIS schema — extended by architecture.md §3)

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detaild specs upfront to reduce ambiguity
- Always use `graphify` at the start of planning to map out existing architecture and proposed changes.

### 2. Subagent strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problem, throw more compute at it via subagents
- One task per subagent for focus execution
- Provide subagents with `graphify` outputs to ensure they have an immediate visual understanding of the codebase segment they are working on.

### 3. Self-Improvement Loop
- After ANY correction from the user: update 'tasks/lessons.md' with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at the session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Use `graphify` to verify the "After" state matches the intended architectural design.
- Diff behavior between main and your changes when relevant
- Ask yoursef: "Would a staff engineer approve this?"
- Run test, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- Visualize the solution with `graphify`—if the resulting graph looks like "spaghetti," the solution is not elegant.
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Run `graphify` on the affected module to find hidden dependencies causing the bug.
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Run `graphify` and Write plan to 'tasks/todo.md' with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to 'tasks/todo.md'
6. **Capture Lessons**: Update 'tasks/lessons.md' after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **Visual Grounding**: Always use `graphify` to maintain a mental map of the project.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
