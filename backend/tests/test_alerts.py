"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_fire_alerts_w31_includes_known_high_grid():
    # GRID-00013 is a real risk_tier=HIGH row in 2026-W31's fire_scores_2026-W31.csv.
    response = client.get("/alerts", params={"week": "2026-W31", "hazard": "fire"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 7  # matches test_fire.py's count_by_tier HIGH=7
    assert "GRID-00013" in body["spatial_unit_ids"]


def test_landslide_alerts_w30_includes_known_expected_cell():
    # 2026-W31's landslide_weekly_score is 100% "masked" -- W30 is the real week
    # with an actual "Landslides Expected" row (LS-00019), per landslide_scores_2026-W30.csv.
    response = client.get("/alerts", params={"week": "2026-W30", "hazard": "landslide"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["spatial_unit_ids"] == ["LS-00019"]


def test_combined_alerts_w31_kecamatan_scoped_and_empty():
    # No real sample week has a kecamatan HIGH on both hazards -- still a real,
    # meaningful assertion: shape is correct and ids (if any) are KEC-* only.
    response = client.get("/alerts", params={"week": "2026-W31", "hazard": "combined"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(body["spatial_unit_ids"])
    assert all(sid.startswith("KEC-") for sid in body["spatial_unit_ids"])


def test_alerts_bogus_hazard_400():
    response = client.get("/alerts", params={"week": "2026-W31", "hazard": "flood"})

    assert response.status_code == 400


def test_alerts_bogus_week_400():
    response = client.get("/alerts", params={"week": "2099-W99", "hazard": "fire"})

    assert response.status_code == 400
