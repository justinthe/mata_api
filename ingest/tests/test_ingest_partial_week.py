"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
from ingest.orchestrate import ingest_week
from shared.db import read_rows


def test_ingest_w30_partial_week_does_not_raise():
    # w30 has no fire grid tif, no fire_scores/fire_weekly_features CSVs.
    summary = ingest_week("data/2026_w30")

    logs = read_rows("ingest_log", {"iso_week": "2026-W30"})
    by_type = {r["file_type"]: r["status"] for r in logs}
    assert by_type["fire_weekly_features_csv"] == "missing"
    assert by_type["fire_scores_csv"] == "missing"
    assert summary["weekly_feature"] == 0


def test_ingest_w34_partial_week_does_not_raise():
    # w34: landslide tif is .mock, no landslide CSVs at all.
    summary = ingest_week("data/2026_w34")

    logs = read_rows("ingest_log", {"iso_week": "2026-W34"})
    by_type = {r["file_type"]: r["status"] for r in logs}
    assert by_type["landslide_risk_tif"] == "mock_placeholder"
    assert by_type["landslide_scores_csv"] == "missing"
    assert summary["landslide_weekly_score"] == 0
    # fire side is fully present for w34 -- should actually ingest.
    assert summary["weekly_feature"] > 0
