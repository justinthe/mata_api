"""Runs against the real shared Postgres -- run via `docker compose run --rm api pytest`."""
import io

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.main import app
from app.routers import alerts, fire, landslide

client = TestClient(app)

# 1x1 transparent PNG.
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _pdf_text(response) -> str:
    reader = PdfReader(io.BytesIO(response.content))
    return "\n".join(page.extract_text() for page in reader.pages)


def test_reports_pdf_fire_w31_matches_summary_and_alerts():
    response = client.post(
        "/reports/pdf",
        json={"week": "2026-W31", "hazard": "fire", "map_image_base64": TINY_PNG_B64},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")

    text = _pdf_text(response)
    by_kecamatan = fire.fire_summary("2026-W31")["by_kecamatan"]
    assert by_kecamatan, "fixture week should have kecamatan rows"
    for row in by_kecamatan:
        assert row["kecamatan_name"] in text
        assert row["risk_tier"] in text

    alert_ids = alerts.alerts("2026-W31", "fire")["spatial_unit_ids"]
    for alert_id in alert_ids:
        assert alert_id in text


def test_reports_pdf_landslide_w30_matches_summary_and_alerts():
    response = client.post(
        "/reports/pdf",
        json={"week": "2026-W30", "hazard": "landslide", "map_image_base64": TINY_PNG_B64},
    )

    assert response.status_code == 200
    text = _pdf_text(response)

    by_kecamatan = landslide.landslide_summary("2026-W30")["by_kecamatan"]
    assert by_kecamatan
    for row in by_kecamatan:
        assert row["kecamatan_name"] in text

    alert_ids = alerts.alerts("2026-W30", "landslide")["spatial_unit_ids"]
    assert alert_ids == ["LS-00019"]  # Phase 06 note: the one real HIGH landslide cell
    for alert_id in alert_ids:
        assert alert_id in text


def test_reports_pdf_bogus_week_400():
    response = client.post(
        "/reports/pdf",
        json={"week": "2099-W99", "hazard": "fire", "map_image_base64": TINY_PNG_B64},
    )

    assert response.status_code == 400


def test_reports_pdf_bogus_hazard_422():
    response = client.post(
        "/reports/pdf",
        json={"week": "2026-W31", "hazard": "flood", "map_image_base64": TINY_PNG_B64},
    )

    assert response.status_code == 422
