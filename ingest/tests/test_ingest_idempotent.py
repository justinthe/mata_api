"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
from ingest.orchestrate import ingest_week
from shared.db import read_rows


def test_reingest_same_week_does_not_duplicate_rows():
    first = ingest_week("data/2026_w31")
    second = ingest_week("data/2026_w31")

    assert first == second  # same per-table counts both runs -> no accumulation

    # fire_risk_prediction has no iso_week column (only a feature_id FK) --
    # its count stability is already covered by the first == second check.
    for table in ("weekly_feature", "sar_burned_area_detection",
                  "landslide_weekly_score", "landslide_dynamic_feature"):
        rows = read_rows(table, {"iso_week": "2026-W31"})
        assert len(rows) == first[table]

    overlays = read_rows("raster_overlay", {"iso_week": "2026-W31"})
    assert len(overlays) == first["raster_overlay"]

    logs = read_rows("ingest_log", {"iso_week": "2026-W31"})
    assert len(logs) == 14  # one row per FILE_TYPES entry, not doubled
