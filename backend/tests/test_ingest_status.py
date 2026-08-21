"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingest_status_w34_matches_real_ingest_log():
    # data/2026_w34/: 8 real fire files + landslide_risk json = ok, landslide_risk_tif
    # has only a .mock sidecar = mock_placeholder, all 4 landslide CSVs are absent = missing.
    response = client.get("/ingest-status", params={"week": "2026-W34"})

    assert response.status_code == 200
    rows = {r["file_type"]: r for r in response.json()}
    assert len(rows) == 14
    assert rows["fire_risk_kecamatan_tif"]["status"] == "ok"
    assert rows["landslide_risk_json"]["status"] == "ok"
    assert rows["landslide_risk_tif"]["status"] == "mock_placeholder"
    for file_type in [
        "landslide_scores_csv",
        "landslide_reclassified_csv",
        "landslide_static_features_csv",
        "landslide_dynamic_features_csv",
    ]:
        assert rows[file_type]["status"] == "missing"


def test_ingest_status_unknown_week_empty_not_error():
    response = client.get("/ingest-status", params={"week": "2026-W99"})

    assert response.status_code == 200
    assert response.json() == []
