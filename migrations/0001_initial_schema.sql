-- MATA Hazard Command — initial schema
-- 14 tables from DATABASE.md + 2 new tables from architecture.md §3.
-- Idempotent: safe to re-run.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Shared / boundary tables

CREATE TABLE IF NOT EXISTS kecamatan_boundary (
    kecamatan_id   text PRIMARY KEY,
    kecamatan_name text NOT NULL,
    geom           geometry(Polygon, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS grid_cell (
    grid_id       text PRIMARY KEY,
    kecamatan_id  text REFERENCES kecamatan_boundary(kecamatan_id),
    geom          geometry(Polygon, 4326) NOT NULL
);

-- Fire (karhutla) tables

CREATE TABLE IF NOT EXISTS acquisition_log (
    run_id           bigserial PRIMARY KEY,
    mode             text NOT NULL,
    date_range_start date NOT NULL,
    date_range_end   date NOT NULL,
    source_used      text,
    run_at           timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hotspot_detection (
    detection_id       bigserial PRIMARY KEY,
    source              text NOT NULL,
    detected_at         timestamptz NOT NULL,
    confidence          numeric,
    frp                 numeric,
    geom                geometry(Point, 4326) NOT NULL,
    grid_id             text REFERENCES grid_cell(grid_id),
    kecamatan_id        text REFERENCES kecamatan_boundary(kecamatan_id),
    acquisition_run_id  bigint REFERENCES acquisition_log(run_id)
);

CREATE TABLE IF NOT EXISTS weekly_feature (
    feature_id             bigserial PRIMARY KEY,
    spatial_unit_type       text NOT NULL,
    spatial_unit_id         text NOT NULL,
    iso_week                text NOT NULL,
    hotspot_count           int,
    hotspot_density         numeric,
    mean_confidence         numeric,
    max_confidence          numeric,
    mean_frp                numeric,
    max_frp                 numeric,
    trend_delta              numeric,
    land_cover_class         text,
    cumulative_rainfall_mm   numeric,
    days_since_rain          int,
    dry_spell_length         int,
    viirs_available          boolean
);

CREATE TABLE IF NOT EXISTS model_run (
    model_version       text PRIMARY KEY,
    model_type           text NOT NULL,
    trained_at            timestamptz DEFAULT now(),
    evaluation_metrics     jsonb
);

CREATE TABLE IF NOT EXISTS fire_risk_prediction (
    prediction_id              bigserial PRIMARY KEY,
    feature_id                  bigint REFERENCES weekly_feature(feature_id),
    model_version                text REFERENCES model_run(model_version),
    risk_tier                    text,
    predicted_next_week_count     numeric,
    predicted_at                  timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS known_fire_event (
    event_id           bigserial PRIMARY KEY,
    source               text,
    event_date_start      date,
    event_date_end         date,
    kecamatan_id            text REFERENCES kecamatan_boundary(kecamatan_id),
    area_hectares            numeric,
    geom                      geometry(Point, 4326)
);

CREATE TABLE IF NOT EXISTS sar_burned_area_detection (
    detection_id                bigserial PRIMARY KEY,
    iso_week                     text NOT NULL,
    method                        text NOT NULL,
    pre_start                     date,
    pre_end                       date,
    post_start                    date,
    post_end                      date,
    burned_area_hectares           numeric,
    classification_diagnostics      jsonb,
    geotiff_path                     text
);

-- Landslide tables

CREATE TABLE IF NOT EXISTS landslide_grid_cell (
    grid_id       text PRIMARY KEY,
    kecamatan_id  text REFERENCES kecamatan_boundary(kecamatan_id),
    geom          geometry(Polygon, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS landslide_static_feature (
    feature_id             bigserial PRIMARY KEY,
    grid_id                 text REFERENCES landslide_grid_cell(grid_id),
    slope_degrees             numeric,
    aspect_class               text,
    land_cover_class             text,
    soil_texture_class             text,
    drainage_distance_m              numeric
);

CREATE TABLE IF NOT EXISTS landslide_dynamic_feature (
    feature_id              bigserial PRIMARY KEY,
    grid_id                  text REFERENCES landslide_grid_cell(grid_id),
    iso_week                   text NOT NULL,
    cumulative_rainfall_mm       numeric,
    ndvi                           numeric
);

CREATE TABLE IF NOT EXISTS landslide_weekly_score (
    score_id             bigserial PRIMARY KEY,
    grid_id                text REFERENCES landslide_grid_cell(grid_id),
    iso_week                 text NOT NULL,
    score_255                  numeric,
    risk_category                text,
    factor_breakdown               jsonb
);

CREATE TABLE IF NOT EXISTS known_landslide_event (
    event_id           bigserial PRIMARY KEY,
    source               text,
    event_date_start      date,
    event_date_end         date,
    kecamatan_id            text REFERENCES kecamatan_boundary(kecamatan_id),
    area_hectares            numeric,
    geom                      geometry(Point, 4326)
);

-- New tables (architecture.md §3)

CREATE TABLE IF NOT EXISTS ingest_log (
    log_id         bigserial PRIMARY KEY,
    iso_week        text NOT NULL,
    hazard           text NOT NULL,
    file_type         text NOT NULL,
    status             text NOT NULL,
    detail               text,
    ingested_at            timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raster_overlay (
    overlay_id      bigserial PRIMARY KEY,
    iso_week         text NOT NULL,
    layer_type        text NOT NULL,
    png_path           text NOT NULL,
    bounds               jsonb NOT NULL,
    created_at             timestamptz DEFAULT now(),
    UNIQUE (iso_week, layer_type)
);
