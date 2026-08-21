# Architecture — MATA Hazard Command

## 1. System Topology

```
                         ┌─────────────────────────┐
   data/YYYY_WXX/*.json  │   ingest.py (CLI, one-   │
   *.csv  *.tif  ───────▶│   way, run manually or   │
   kelurahan.geojson     │   via cron per week)     │
                         └───────────┬──────────────┘
                                     │ writes rows + PNG overlays
                                     ▼
                         ┌─────────────────────────┐
                         │  Postgres 16 + PostGIS   │  (DATABASE.md schema
                         │  (docker compose)        │   + 2 new tables, §3)
                         └───────────┬──────────────┘
                                     │ read-only
                                     ▼
                         ┌─────────────────────────┐      generated/overlays/
                         │  FastAPI backend         │◀────  *.png (static-
                         │  (uvicorn, read-only API │       mounted, served
                         │  + PDF report endpoint)  │       to browser)
                         └───────────┬──────────────┘
                                     │ JSON / PNG / PDF over HTTP
                                     ▼
                         ┌─────────────────────────┐
                         │  React + react-leaflet   │───▶ Google Satellite
                         │  frontend (Vite)         │     XYZ tiles (browser
                         └─────────────────────────┘      fetches directly)
```

Two write paths only: `ingest.py` (files → DB, operator-run, not exposed via HTTP) and nothing else. The API is 100% read-only except the PDF endpoint, which generates a file but writes nothing back to DB.

## 2. Tech Stack

- **FastAPI** (Python) — matches `DATABASE.md`'s existing `shared/db.py` + GeoAlchemy2 convention; async-capable, auto OpenAPI docs for a small read-only API.
- **SQLAlchemy + GeoAlchemy2** — already the documented IO layer (`shared.db.write_rows`/`read_rows`, table reflection, no ORM models) — reused as-is, not replaced.
- **Postgres 16 + PostGIS 3.4** — already specified in `DATABASE.md`, `docker-compose.yml` exists in principle (needs creating fresh in this wiped repo).
- **rasterio** — reads the risk/burned-area GeoTIFFs (band values + geo bounds) at ingest time; boring, standard choice for GeoTIFF in Python.
- **Pillow** — colorizes each raster band into a PNG per the fixed color specs (simple per-pixel lookup, no need for a heavier raster-styling lib at this data size).
- **reportlab** — server-side PDF generation for the report endpoint; no headless browser needed.
- **React + react-leaflet + Vite** — user-chosen stack; Vite for a fast dev loop with no extra config.
- **Google Satellite unofficial XYZ tiles** — fetched directly by the browser (`https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}`), no backend proxy — keeps the backend simple; frontend swaps to Esri World Imagery with a one-line tile URL change if Google blocks the endpoint (flagged risk, PRD §Assumptions).

## 3. Data Models

All 14 tables from `DATABASE.md` §Schema are used as-is and unmodified (`kecamatan_boundary`, `grid_cell`, `acquisition_log`, `hotspot_detection`, `weekly_feature`, `fire_risk_prediction`, `model_run`, `known_fire_event`, `sar_burned_area_detection`, `landslide_grid_cell`, `landslide_static_feature`, `landslide_dynamic_feature`, `landslide_weekly_score`, `known_landslide_event`) — see that file for full column definitions. `migrations/0001_initial_schema.sql` creates all 14 plus the 2 new tables below, `IF NOT EXISTS` throughout, matching the existing idempotent-migration convention.

New tables (not in DATABASE.md, added for this dashboard):

### `ingest_log`
| column | type | notes |
|---|---|---|
| log_id | bigserial | PK |
| iso_week | text | not null |
| hazard | text | not null (`fire` / `landslide`) |
| file_type | text | not null, e.g. `fire_risk_json`, `landslide_risk_tif` |
| status | text | not null (`ok` / `mock_placeholder` / `missing` / `error`) |
| detail | text | error message or note, nullable |
| ingested_at | timestamptz | default now() |

Satisfies PRD F1 (idempotent, partial-week-tolerant ingest) and the Observability NFR — Budi can query "what's incomplete for week X."

### `raster_overlay`
| column | type | notes |
|---|---|---|
| overlay_id | bigserial | PK |
| iso_week | text | not null |
| layer_type | text | not null (`fire_grid` / `fire_kecamatan` / `burned_area` / `landslide_risk`) |
| png_path | text | not null, relative path under `generated/overlays/` |
| bounds | jsonb | not null, `[[south,west],[north,east]]` — Leaflet `ImageOverlay` bounds format |
| created_at | timestamptz | default now() |

One row per (week, layer_type). `ingest.py` overwrites (upsert on `iso_week, layer_type`) so re-running ingest for a week is idempotent, per PRD F1.

## 4. API Boundaries

All routes read-only against Postgres unless noted. No auth in v1 (PRD §8). Base path `/api`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | DB connectivity check |
| GET | `/weeks` | List ingested `iso_week`s, most recent first |
| GET | `/boundaries` | Kecamatan boundary polygons (GeoJSON, from `kecamatan_boundary`) |
| GET | `/fire/summary?week=` | Count-by-tier, highest-predicted, by-kecamatan (mirrors `fire_risk_*.json` shape) |
| GET | `/fire/grid?week=` | Per-grid tier/score list, for click-to-inspect (F5) |
| GET | `/fire/overlay/{layer}?week=` | `layer` = `grid`\|`kecamatan`\|`burned_area`; returns `{png_url, bounds}` from `raster_overlay` |
| GET | `/landslide/summary?week=` | Count-by-category, area-by-category, highest-risk cell, by-kecamatan |
| GET | `/landslide/grid?week=` | Per-grid score/category/factor-breakdown, for click-to-inspect |
| GET | `/landslide/overlay?week=` | `{png_url, bounds}` for the landslide risk raster |
| GET | `/alerts?week=&hazard=` | HIGH-alert areas per PRD's threshold definition (fire/landslide/combined) — feeds F6 |
| GET | `/cells/{hazard}/{spatial_id}?week=` | Full detail for one clicked grid/kecamatan (F5) |
| GET | `/ingest-status?week=` | Per-file `ingest_log` rows for a week (Budi's observability view) |
| POST | `/reports/pdf` | Body `{week, hazard, map_image_base64}` (client-captured map snapshot) → returns PDF binary. Generates only, writes nothing to DB. |

`generated/overlays/*.png` served as static files by FastAPI (`StaticFiles` mount); `/fire/overlay` and `/landslide/overlay` return the URL, not the bytes, so the browser caches PNGs normally.

## 5. Containerization & Environments

```yaml
# docker-compose.yml (sketch)
services:
  postgres:
    image: postgis/postgis:16-3.4
    environment: [POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]  # from .env
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: pg_isready -U $POSTGRES_USER -d $POSTGRES_DB, 5s interval, 5 retries

  api:
    build: ./backend
    env_file: .env
    depends_on: [postgres]
    ports: ["8000:8000"]
    volumes: ["./generated:/app/generated"]   # overlay PNGs, shared with ingest

  web:
    build: ./frontend
    depends_on: [api]
    ports: ["5173:5173"]                       # vite dev server

volumes:
  pgdata:
```

`ingest.py` runs as a one-off (`docker compose run --rm api python ingest.py data/2026_w34`), not a long-running service — matches PRD's "operator runs it manually" flow (F1/User Flow 8). Same `.env` (`DATABASE_URL`, `POSTGRES_*`) already documented in `DATABASE.md` covers both `api` and `ingest.py`.

## 6. Observability Plan

- Structured JSON logs (Python `logging` + `python-json-logger` or stdlib `logging.Formatter` emitting JSON) for both `api` and `ingest.py`: timestamp, level, request/run id, message.
- `ingest_log` table (§3) is the durable, queryable record of ingest outcomes per file/week — surfaced via `GET /ingest-status`.
- `GET /health` checks DB connectivity (`SELECT 1`) — used by docker-compose healthcheck and manual operator checks. No upstream third-party dependency to probe (Google tiles are fetched client-side, not proxied).
- No error-tracking service (Sentry etc.) in v1 — internal single-operator tool; add if this moves beyond dev/internal use.

## 7. Security Posture

- No authentication in v1 (PRD §8, explicit assumption) — mitigated by internal-network-only deployment; call out clearly in README that this must not be exposed to the public internet as-is.
- Server-side re-validation on every endpoint: `week` query params validated against actual `ingest_log`/DB values (not trusted from client), `hazard`/`layer` params validated against a fixed enum, 400 on anything else.
- No rate limiting in v1 — no public routes, no cost-sensitive third-party calls from the backend (Google tiles are fetched by the browser directly, never proxied through the API, so there's no API-side tile cost to protect).
- CORS locked to the frontend's dev/prod origin(s) only.
- Secrets (`DATABASE_URL`, `POSTGRES_*`) stay server-side in `.env`, never sent to the frontend. Errors returned to the client are generic (`{"detail": "..."}`); full tracebacks only in server logs.

## 8. Dependency Graph

```
ingest.py
  ├── shared/db.py (write_rows)              [reused from DATABASE.md convention]
  ├── shared/boundary.py (dissolve kelurahan → kecamatan)  [reused]
  ├── ingest/parsers/fire.py                  (fire_risk json, fire_scores/fire_weekly_features csv)
  ├── ingest/parsers/landslide.py             (landslide_risk json, landslide_*.csv)
  ├── ingest/parsers/sar.py                   (fire_sar_result csv, fire_sar_burned_area json)
  └── ingest/rasterize.py                     (rasterio + Pillow → PNG, writes raster_overlay rows)

backend/api
  ├── shared/db.py (read_rows)                [reused]
  ├── routers/weeks.py, boundaries.py
  ├── routers/fire.py, landslide.py, alerts.py, cells.py
  ├── routers/ingest_status.py
  └── routers/reports.py                      (reportlab, reads DB + generated/overlays)

frontend/web
  ├── api/client.ts                            (fetch wrappers for all /api routes)
  ├── components/MapView.tsx                   (react-leaflet, ImageOverlay per layer)
  ├── components/LayerControls.tsx              (hazard toggle, week select, opacity sliders)
  ├── components/AlertPanel.tsx                 (F6, calls /alerts)
  ├── components/InspectPopup.tsx                (F5, calls /cells)
  └── components/ExportButton.tsx                (captures map via leaflet-image, POSTs /reports/pdf)
```

`shared/db.py` and `shared/boundary.py` are the only modules shared between `ingest.py` and the API — everything else is one-directional (ingest writes, API reads, frontend calls API only).
