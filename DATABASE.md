# Database

## Connection

- Engine: Postgres 16 + PostGIS 3.4, container image `postgis/postgis:16-3.4`
  (`docker-compose.yml`), port `5432` mapped to host, volume `pgdata`.
- Start: `docker compose up -d`.
- Container env (from `.env`, read by compose): `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_DB`.
- App connection: `DATABASE_URL` env var, read by `shared/db.py::get_connection()`
  via `python-dotenv` + `sqlalchemy.create_engine()`. Format:
  `postgresql://<user>:<password>@localhost:5432/<db>`. Unset -> `RuntimeError`.
- `.env.example` template:
  ```
  DATABASE_URL=postgresql://user:password@localhost:5432/mata_hazard
  POSTGRES_USER=user
  POSTGRES_PASSWORD=password
  POSTGRES_DB=mata_hazard
  ```
  Real `.env` exists locally (git-ignored), values not reproduced here.
- Healthcheck: `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`, 5s interval,
  5 retries.
- Migration apply: `docker compose exec -T postgres psql -U <user> -d <db> <
  migrations/0001_initial_schema.sql` (idempotent, re-run safe).
- Preflight check (live GEE + live DB): `set -a; source .env; set +a;
  .venv/bin/python -c "from shared import health; print(health.run_preflight())"`.
- IO layer: `shared.db.write_rows(table, rows)` / `read_rows(table, filters)`
  — generic SQLAlchemy reflection via `Table(..., autoload_with=engine)`, no
  ORM models, geometry columns handled transparently via GeoAlchemy2 import.

## Schema

Postgres 16 + PostGIS 3.4 (`postgis/postgis:16-3.4`, `docker compose up -d`).
Schema: `migrations/0001_initial_schema.sql` (idempotent, `IF NOT EXISTS`
throughout). 14 tables, full ERD from `MULTI_HAZARD_TRD.md` §5. Connection
via `DATABASE_URL` env var (`shared/db.py::get_connection()`, SQLAlchemy +
GeoAlchemy2). IO helpers: `shared.db.write_rows(table, rows)` /
`read_rows(table, filters)` — generic, autoload table via reflection, no ORM
models.

## Shared / boundary tables

### `kecamatan_boundary`
| column | type | notes |
|---|---|---|
| kecamatan_id | text | PK |
| kecamatan_name | text | not null |
| geom | geometry(Polygon, 4326) | not null |

45 official Majalengka kecamatan (dissolved from `data/kelurahan.geojson` via
`shared/boundary.py`).

### `grid_cell` (fire's 1km grid)
| column | type | notes |
|---|---|---|
| grid_id | text | PK |
| kecamatan_id | text | FK -> kecamatan_boundary |
| geom | geometry(Polygon, 4326) | not null |

~1,430 cells, UTM 48S 1km grid clipped to boundary.

## Fire (karhutla) tables

### `acquisition_log`
| column | type | notes |
|---|---|---|
| run_id | bigserial | PK |
| mode | text | not null |
| date_range_start | date | not null |
| date_range_end | date | not null |
| source_used | text | |
| run_at | timestamptz | default now() |

### `hotspot_detection`
| column | type | notes |
|---|---|---|
| detection_id | bigserial | PK |
| source | text | not null (MODIS/VIIRS) |
| detected_at | timestamptz | not null |
| confidence | numeric | |
| frp | numeric | |
| geom | geometry(Point, 4326) | not null |
| grid_id | text | FK -> grid_cell |
| kecamatan_id | text | FK -> kecamatan_boundary |
| acquisition_run_id | bigint | FK -> acquisition_log |

### `weekly_feature`
| column | type | notes |
|---|---|---|
| feature_id | bigserial | PK |
| spatial_unit_type | text | not null (GRID/KECAMATAN) |
| spatial_unit_id | text | not null |
| iso_week | text | not null |
| hotspot_count | int | |
| hotspot_density | numeric | |
| mean_confidence | numeric | |
| max_confidence | numeric | |
| mean_frp | numeric | |
| max_frp | numeric | |
| trend_delta | numeric | trailing 3-week mean delta |
| land_cover_class | text | ESA WorldCover majority |
| cumulative_rainfall_mm | numeric | CHIRPS |
| days_since_rain | int | |
| dry_spell_length | int | |
| viirs_available | boolean | |

### `fire_risk_prediction`
| column | type | notes |
|---|---|---|
| prediction_id | bigserial | PK |
| feature_id | bigint | FK -> weekly_feature |
| model_version | text | |
| risk_tier | text | |
| predicted_next_week_count | numeric | |
| predicted_at | timestamptz | default now() |

### `model_run`
| column | type | notes |
|---|---|---|
| model_version | text | PK, timestamp-suffixed per run |
| model_type | text | not null (e.g. `tier:rule/count:persistence`) |
| trained_at | timestamptz | default now() |
| evaluation_metrics | jsonb | raw dict, no `json.dumps` |

### `known_fire_event`
| column | type | notes |
|---|---|---|
| event_id | bigserial | PK |
| source | text | |
| event_date_start | date | |
| event_date_end | date | |
| kecamatan_id | text | FK -> kecamatan_boundary |
| area_hectares | numeric | |
| geom | geometry(Point, 4326) | |

### `sar_burned_area_detection`
| column | type | notes |
|---|---|---|
| detection_id | bigserial | PK |
| iso_week | text | not null |
| method | text | not null |
| pre_start / pre_end | date | S1 pre-composite window |
| post_start / post_end | date | S1 post-composite window |
| burned_area_hectares | numeric | |
| classification_diagnostics | jsonb | K-means cluster diagnostics |
| geotiff_path | text | |

## Landslide tables

### `landslide_grid_cell`
| column | type | notes |
|---|---|---|
| grid_id | text | PK |
| kecamatan_id | text | FK -> kecamatan_boundary |
| geom | geometry(Polygon, 4326) | not null |

~134,700 cells, 100m UTM 48S grid (vectorized, `landslide/acquisition.py::_build_grid()`).

### `landslide_static_feature`
| column | type | notes |
|---|---|---|
| feature_id | bigserial | PK |
| grid_id | text | FK -> landslide_grid_cell |
| slope_degrees | numeric | SRTM |
| aspect_class | text | 8-way compass + "Flat" |
| land_cover_class | text | ESA WorldCover |
| soil_texture_class | text | OpenLandMap, 12-class |
| drainage_distance_m | numeric | HydroSHEDS flow-accum distance transform |

### `landslide_dynamic_feature`
| column | type | notes |
|---|---|---|
| feature_id | bigserial | PK |
| grid_id | text | FK -> landslide_grid_cell |
| iso_week | text | not null |
| cumulative_rainfall_mm | numeric | CHIRPS trailing 7d |
| ndvi | numeric | Sentinel-2 SR, cloud-masked |

### `landslide_weekly_score`
| column | type | notes |
|---|---|---|
| score_id | bigserial | PK |
| grid_id | text | FK -> landslide_grid_cell |
| iso_week | text | not null |
| score_255 | numeric | 0 if masked |
| risk_category | text | 5 categories + "masked" |
| factor_breakdown | jsonb | per-factor score dict, NaN->None |

### `known_landslide_event`
| column | type | notes |
|---|---|---|
| event_id | bigserial | PK |
| source | text | |
| event_date_start | date | |
| event_date_end | date | |
| kecamatan_id | text | FK -> kecamatan_boundary |
| area_hectares | numeric | |
| geom | geometry(Point, 4326) | |

## Known gaps (see CLAUDE.md phase notes)

- No phase writes `landslide_grid_cell`/`kecamatan_boundary` rows in
  production — `run_landslide_processing.py --persist` bootstraps them
  itself (demo-only, `ON CONFLICT DO NOTHING`).
- `kecamatan_boundary.geom` typed `Polygon` but a dissolved border-fragment
  kecamatan can legitimately be `MultiPolygon` — worked around by keeping
  only the largest sub-polygon in the bootstrap, not fixed in the schema.
- `landslide_static_feature`/`_dynamic_feature`/`_weekly_score` carry no
  `acquisition_run_id`/`model_version` columns — only the fire chain writes
  `acquisition_log`/`model_run` (landslide's `reclassify()` is rule-based,
  never a trained model).
