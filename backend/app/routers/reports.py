import base64
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.routers import alerts, fire, landslide
from shared.db import read_rows

router = APIRouter(prefix="/reports")


class ReportRequest(BaseModel):
    week: str
    hazard: Literal["fire", "landslide"]
    map_image_base64: str


def _by_kecamatan_table(hazard: str, week: str) -> tuple[list[str], list[list]]:
    if hazard == "fire":
        rows = fire.fire_summary(week)["by_kecamatan"]
        return ["Kecamatan", "Risk Tier", "Predicted Next Week"], [
            [r["kecamatan_name"], r["risk_tier"], r["predicted_next_week_count"]] for r in rows
        ]
    rows = landslide.landslide_summary(week)["by_kecamatan"]
    return ["Kecamatan", "Highest Category", "Mean Score"], [
        [r["kecamatan_name"], r["highest_category"], r["mean_score_255"]] for r in rows
    ]


def _compose_pdf(week: str, hazard: str, image_bytes: bytes, header: list[str], rows: list[list], alert_lines: list[str]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"MATA Hazard Report — {week} — {hazard.upper()}", styles["Title"]), Spacer(1, 12)]

    pil_img = PILImage.open(BytesIO(image_bytes))
    scale = doc.width / pil_img.width
    story.append(RLImage(BytesIO(image_bytes), width=doc.width, height=pil_img.height * scale))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Per-Kecamatan Risk", styles["Heading2"]))
    table = Table([header] + rows)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("HIGH-Alert Areas", styles["Heading2"]))
    if alert_lines:
        story.extend(Paragraph(f"• {line}", styles["Normal"]) for line in alert_lines)
    else:
        story.append(Paragraph("None.", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()


@router.post("/pdf")
def reports_pdf(body: ReportRequest):
    fire._ensure_valid_week(body.week)

    header, rows = _by_kecamatan_table(body.hazard, body.week)

    alert_ids = alerts.alerts(body.week, body.hazard)["spatial_unit_ids"]
    kec_name_by_id = {r["kecamatan_id"]: r["kecamatan_name"] for r in read_rows("kecamatan_boundary")}
    alert_lines = [f"{kec_name_by_id[i]} ({i})" if i in kec_name_by_id else i for i in alert_ids]

    data = body.map_image_base64
    if data.startswith("data:"):
        data = data.split(",", 1)[1]
    image_bytes = base64.b64decode(data)

    pdf_bytes = _compose_pdf(body.week, body.hazard, image_bytes, header, rows, alert_lines)
    filename = f"mata-hazard-{body.week}-{body.hazard}.pdf"
    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
