"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_weeks_returns_all_three_most_recent_first():
    response = client.get("/weeks")

    assert response.status_code == 200
    assert response.json() == ["2026-W34", "2026-W31", "2026-W30"]


def test_boundaries_returns_45_features():
    response = client.get("/boundaries")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 45

    by_id = {f["properties"]["kecamatan_id"]: f for f in body["features"]}
    assert by_id["KEC-01"]["properties"]["kecamatan_name"] == "Argapura"
    assert by_id["KEC-01"]["geometry"]["type"] == "Polygon"
