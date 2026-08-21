"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_fire_cell_w31_exact_match():
    response = client.get("/cells/fire/GRID-00013", params={"week": "2026-W31"})

    assert response.status_code == 200
    assert response.json() == {
        "spatial_unit_id": "GRID-00013",
        "spatial_unit_type": "GRID",
        "risk_tier": "HIGH",
        "predicted_next_week_count": 1.0,
        "hotspot_count": 1,
        "hotspot_density": 1.2203739625863173,
        "mean_frp": 0.91,
        "max_frp": 0.91,
    }


def test_landslide_cell_w30_exact_score():
    # LS-00019 is the real highest_risk_cell in the live DB -- W31's own
    # landslide_weekly_score is 100% risk_category=masked/score_255=0.0
    # (confirmed live), so W30 is the week with real signal to check.
    response = client.get("/cells/landslide/LS-00019", params={"week": "2026-W30"})

    assert response.status_code == 200
    body = response.json()
    assert body["grid_id"] == "LS-00019"
    assert body["score_255"] == 92.0
    assert body["risk_category"] == "Landslides Expected"
    assert "factor_breakdown" in body


def test_fire_cell_unknown_id_404():
    response = client.get("/cells/fire/GRID-99999", params={"week": "2026-W31"})

    assert response.status_code == 404


def test_landslide_cell_unknown_id_404():
    response = client.get("/cells/landslide/LS-99999", params={"week": "2026-W31"})

    assert response.status_code == 404


def test_cells_bogus_hazard_400():
    response = client.get("/cells/flood/GRID-00013", params={"week": "2026-W31"})

    assert response.status_code == 400


def test_cells_bogus_week_400():
    response = client.get("/cells/fire/GRID-00013", params={"week": "2099-W99"})

    assert response.status_code == 400
