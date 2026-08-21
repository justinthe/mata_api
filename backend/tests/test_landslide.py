"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_summary_w30_matches_known_shape():
    response = client.get("/landslide/summary", params={"week": "2026-W30"})

    assert response.status_code == 200
    body = response.json()
    assert body["count_by_category"] == {"Landslides Expected": 1, "Modest Hazard": 19}
    assert body["highest_risk_cell"] == {"grid_id": "LS-00019", "kecamatan_id": "KEC-11", "score_255": 92.0}
    assert set(body["area_by_category_ha"]) == {"Landslides Expected", "Modest Hazard"}
    kec = next(k for k in body["by_kecamatan"] if k["kecamatan_id"] == "KEC-11")
    assert kec["highest_category"] == "Landslides Expected"


def test_summary_w31_all_masked():
    response = client.get("/landslide/summary", params={"week": "2026-W31"})

    assert response.status_code == 200
    body = response.json()
    assert body["count_by_category"] == {"masked": 50}
    assert body["highest_risk_cell"] is not None
    assert body["highest_risk_cell"]["score_255"] == 0.0


def test_summary_w34_empty_not_error():
    # w34 has no landslide_scores_csv on disk -- landslide_weekly_score has 0 rows.
    response = client.get("/landslide/summary", params={"week": "2026-W34"})

    assert response.status_code == 200
    body = response.json()
    assert body["count_by_category"] == {}
    assert body["area_by_category_ha"] == {}
    assert body["highest_risk_cell"] is None
    assert body["by_kecamatan"] == []


def test_summary_bogus_week_400():
    response = client.get("/landslide/summary", params={"week": "2099-W99"})

    assert response.status_code == 400


def test_grid_w30_returns_20_rows_with_features():
    response = client.get("/landslide/grid", params={"week": "2026-W30"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 20
    assert all(row["grid_id"].startswith("LS-") for row in body)
    assert any(row["slope_degrees"] is not None for row in body)
    assert any(row["cumulative_rainfall_mm"] is not None for row in body)


def test_grid_w34_empty_list():
    response = client.get("/landslide/grid", params={"week": "2026-W34"})

    assert response.status_code == 200
    assert response.json() == []


def test_overlay_ok_w31():
    response = client.get("/landslide/overlay", params={"week": "2026-W31"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["png_url"] == "/generated/overlays/2026-W31_landslide_risk.png"
    assert len(body["bounds"]) == 2 and len(body["bounds"][0]) == 2


def test_overlay_mock_placeholder_w34():
    # w34's landslide_risk_tif is a real mock_placeholder in ingest_log -- no synthetic row needed.
    response = client.get("/landslide/overlay", params={"week": "2026-W34"})

    assert response.status_code == 200
    assert response.json()["status"] == "mock_placeholder"


def test_overlay_bogus_week_400():
    response = client.get("/landslide/overlay", params={"week": "2099-W99"})

    assert response.status_code == 400
