"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
from fastapi.testclient import TestClient

from app.main import app
from shared.db import delete_rows, write_rows

client = TestClient(app)


def test_summary_w31_matches_known_shape():
    response = client.get("/fire/summary", params={"week": "2026-W31"})

    assert response.status_code == 200
    body = response.json()
    assert body["count_by_tier"] == {"LOW": 1468, "MEDIUM": 0, "HIGH": 7}
    assert body["highest_predicted"] == {"spatial_unit_id": "KEC-10", "predicted_next_week_count": 4.0}
    assert len(body["by_kecamatan"]) == 45


def test_summary_w30_partial_week_is_empty_not_error():
    # w30 has no fire_weekly_features_csv/fire_scores_csv on disk.
    response = client.get("/fire/summary", params={"week": "2026-W30"})

    assert response.status_code == 200
    body = response.json()
    assert body["count_by_tier"] == {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    assert body["highest_predicted"] is None
    assert body["by_kecamatan"] == []


def test_summary_bogus_week_400():
    response = client.get("/fire/summary", params={"week": "2099-W99"})

    assert response.status_code == 400


def test_grid_w31_returns_1430_rows():
    response = client.get("/fire/grid", params={"week": "2026-W31"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1430
    assert all(row["grid_id"].startswith("GRID-") for row in body)


def test_overlay_ok_w31_grid():
    response = client.get("/fire/overlay/grid", params={"week": "2026-W31"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["png_url"] == "/generated/overlays/2026-W31_fire_grid.png"
    assert len(body["bounds"]) == 2 and len(body["bounds"][0]) == 2


def test_overlay_missing_w30_grid():
    # w30 genuinely has no fire_risk_2026-W30_grid.tif and never had a .mock sidecar either.
    response = client.get("/fire/overlay/grid", params={"week": "2026-W30"})

    assert response.status_code == 200
    assert response.json()["status"] == "missing"


def test_overlay_bogus_layer_400():
    response = client.get("/fire/overlay/xyz", params={"week": "2026-W31"})

    assert response.status_code == 400


def test_overlay_bogus_week_400():
    response = client.get("/fire/overlay/grid", params={"week": "2099-W99"})

    assert response.status_code == 400


def test_overlay_surfaces_mock_placeholder_status():
    write_rows("ingest_log", [{
        "iso_week": "2099-W99",
        "hazard": "fire",
        "file_type": "fire_risk_grid_tif",
        "status": "mock_placeholder",
        "detail": "synthetic test row",
    }])
    try:
        response = client.get("/fire/overlay/grid", params={"week": "2099-W99"})
        assert response.status_code == 200
        assert response.json()["status"] == "mock_placeholder"
    finally:
        delete_rows("ingest_log", {"iso_week": "2099-W99"})
