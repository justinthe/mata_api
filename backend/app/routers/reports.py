import base64
from datetime import datetime, timezone
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.routers import alerts, fire, landslide
from shared.db import read_rows

router = APIRouter(prefix="/reports")

# Sitrep palette: near-black ink on paper, tier colors read as alert flags,
# not decoration. No gradients, no rounded corners, no card chrome.
INK = colors.HexColor("#1c1c1a")
PAPER = colors.white
MUTED = colors.HexColor("#5c5c56")
RULE = colors.HexColor("#c9c7bd")
HIGH = colors.HexColor("#8b1a1a")
MEDIUM = colors.HexColor("#a66a00")
LOW = colors.HexColor("#3d5a2c")
TIER_COLOR = {"HIGH": HIGH, "MEDIUM": MEDIUM, "LOW": LOW}
TIER_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
TIER_LETTER = {"HIGH": "H", "MEDIUM": "M", "LOW": "L"}

CONTENT_WIDTH = 17.5 * cm
PAGE_MARGIN = (A4[0] - CONTENT_WIDTH) / 2

TITLE_STYLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=16, textColor=PAPER, leading=18)
SUBHEAD_STYLE = ParagraphStyle("subhead", fontName="Courier", fontSize=8.5, textColor=MUTED, leading=12)
HEADING_STYLE = ParagraphStyle("heading", fontName="Helvetica-Bold", fontSize=11, textColor=INK, leading=13)
BOX_NUM_STYLE = ParagraphStyle("boxnum", fontName="Helvetica-Bold", fontSize=22, textColor=PAPER, leading=24, alignment=TA_CENTER)
BOX_LABEL_STYLE = ParagraphStyle("boxlabel", fontName="Helvetica-Bold", fontSize=8, textColor=PAPER, leading=10, alignment=TA_CENTER)
PRIORITY_STYLE = ParagraphStyle("priority", fontName="Helvetica-Bold", fontSize=10.5, textColor=PAPER, leading=13)
LIST_STYLE = ParagraphStyle("list", fontName="Courier", fontSize=9, textColor=INK, leading=13)
CELL_STYLE = ParagraphStyle("cell", fontName="Helvetica", fontSize=9, textColor=INK, leading=11)
CELL_MONO_STYLE = ParagraphStyle("cellmono", fontName="Courier", fontSize=9, textColor=INK, leading=11)


class ReportRequest(BaseModel):
    week: str
    hazard: Literal["fire", "landslide"]
    map_image_base64: str


def _tier(hazard: str, row: dict) -> str:
    if hazard == "fire":
        return row["risk_tier"]
    # landslide's risk_category isn't a fixed 3-tier enum -- bucket by score_255
    # using the same thresholds the frontend already uses (types.ts::landslideTierClass).
    score = row["mean_score_255"]
    return "HIGH" if score >= 180 else "MEDIUM" if score >= 60 else "LOW"


def _priority_line(hazard: str, summary: dict, kec_name_by_id: dict[str, str]) -> str | None:
    if hazard == "fire":
        h = summary["highest_predicted"]
        if not h:
            return None
        loc = kec_name_by_id.get(h["spatial_unit_id"], h["spatial_unit_id"])
        return f"{loc} -- predicted {h['predicted_next_week_count']} hotspot(s) next week"
    h = summary["highest_risk_cell"]
    if not h:
        return None
    loc = kec_name_by_id.get(h["kecamatan_id"], h["kecamatan_id"] or h["grid_id"])
    return f"{loc} -- cell {h['grid_id']}, score {h['score_255']:.0f}/255"


def _table_columns(hazard: str, rows: list[dict]) -> tuple[list[str], list[list], list[float]]:
    if hazard == "fire":
        header = ["", "KECAMATAN", "PREDICTED NEXT WK"]
        body = [[r["kecamatan_name"] or r["kecamatan_id"], str(r["predicted_next_week_count"])] for r in rows]
        widths = [1.1 * cm, 10.4 * cm, 6 * cm]
    else:
        header = ["", "KECAMATAN", "HIGHEST CATEGORY", "MEAN SCORE"]
        body = [[r["kecamatan_name"] or r["kecamatan_id"], r["highest_category"], f"{r['mean_score_255']:.0f}"] for r in rows]
        widths = [1.1 * cm, 8 * cm, 5.5 * cm, 2.9 * cm]
    return header, body, widths


def _heading(text: str) -> Table:
    t = Table([[Paragraph(text.upper(), HEADING_STYLE)]], colWidths=[CONTENT_WIDTH])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.2, INK), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def _stat_band(tier_counts: dict[str, int]) -> Table:
    cells = []
    for tier in ("HIGH", "MEDIUM", "LOW"):
        cells.append(
            [Paragraph(str(tier_counts.get(tier, 0)), BOX_NUM_STYLE), Paragraph(f"{tier} SECTORS", BOX_LABEL_STYLE)]
        )
    t = Table([cells], colWidths=[CONTENT_WIDTH / 3] * 3)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]
    for i, tier in enumerate(("HIGH", "MEDIUM", "LOW")):
        style.append(("BACKGROUND", (i, 0), (i, 0), TIER_COLOR[tier]))
    t.setStyle(TableStyle(style))
    return t


def _priority_band(text: str | None) -> Table:
    body = f"PRIORITY: {text}" if text else "PRIORITY: NO DATA FOR THIS WEEK"
    t = Table([[Paragraph(body, PRIORITY_STYLE)]], colWidths=[CONTENT_WIDTH])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HIGH if text else MUTED),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return t


def _sector_table(hazard: str, rows: list[dict]) -> Table:
    header, body, widths = _table_columns(hazard, rows)
    table_data = [header]
    for row, cells in zip(rows, body):
        styled = [Paragraph(c, CELL_STYLE) for c in cells[:-1]] + [Paragraph(cells[-1], CELL_MONO_STYLE)]
        swatch = Paragraph(TIER_LETTER[row["_tier"]], BOX_LABEL_STYLE)
        table_data.append([swatch] + styled)
    if not rows:
        table_data.append([Paragraph("NO SECTOR DATA FOR THIS WEEK", CELL_STYLE)] + [""] * (len(header) - 1))

    t = Table(table_data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), PAPER),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if rows:
        for i, row in enumerate(rows, start=1):
            style.append(("BACKGROUND", (0, i), (0, i), TIER_COLOR[row["_tier"]]))
            style.append(("ALIGN", (0, i), (0, i), "CENTER"))
    else:
        style.append(("SPAN", (0, 1), (-1, 1)))
    t.setStyle(TableStyle(style))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(1.5 * cm, 1.4 * cm, A4[0] - 1.5 * cm, 1.4 * cm)
    canvas.setFont("Courier", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.5 * cm, 1 * cm, "MATA HAZARD COMMAND -- INTERNAL USE ONLY")
    canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"PAGE {canvas.getPageNumber()}")
    canvas.restoreState()


def _compose_pdf(
    week: str,
    hazard: str,
    image_bytes: bytes,
    rows: list[dict],
    tier_counts: dict[str, int],
    priority_text: str | None,
    alert_lines: list[str],
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
    )
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    title_bar = Table(
        [[Paragraph("MATA HAZARD SITREP", TITLE_STYLE), Paragraph(hazard.upper(), TITLE_STYLE)]],
        colWidths=[13 * cm, CONTENT_WIDTH - 13 * cm],
    )
    title_bar.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), INK),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (0, 0), 10),
                ("RIGHTPADDING", (1, 0), (1, 0), 10),
            ]
        )
    )

    story = [
        title_bar,
        Spacer(1, 4),
        Paragraph(f"SECTOR: MAJALENGKA REGENCY   |   WEEK: {week}   |   GENERATED: {generated} UTC", SUBHEAD_STYLE),
        Spacer(1, 14),
        _heading("Status at a Glance"),
        Spacer(1, 6),
        _stat_band(tier_counts),
        Spacer(1, 14),
        _priority_band(priority_text),
        Spacer(1, 16),
        _heading("Area of Operations"),
        Spacer(1, 8),
    ]

    pil_img = PILImage.open(BytesIO(image_bytes))
    scale = doc.width / pil_img.width
    story.append(RLImage(BytesIO(image_bytes), width=doc.width, height=pil_img.height * scale))
    story.append(Spacer(1, 16))

    story.append(_heading("Flagged Sectors"))
    story.append(Spacer(1, 6))
    if alert_lines:
        story.extend(Paragraph(f"-- {line}", LIST_STYLE) for line in alert_lines)
    else:
        story.append(Paragraph("NO SECTORS FLAGGED.", LIST_STYLE))
    story.append(Spacer(1, 16))

    story.append(_heading("Sector Breakdown"))
    story.append(Spacer(1, 8))
    story.append(_sector_table(hazard, rows))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


@router.post("/pdf")
def reports_pdf(body: ReportRequest):
    fire._ensure_valid_week(body.week)

    summary = fire.fire_summary(body.week) if body.hazard == "fire" else landslide.landslide_summary(body.week)
    kec_name_by_id = {r["kecamatan_id"]: r["kecamatan_name"] for r in read_rows("kecamatan_boundary")}

    rows = summary["by_kecamatan"]
    for r in rows:
        r["_tier"] = _tier(body.hazard, r)
    rows.sort(key=lambda r: (-TIER_RANK[r["_tier"]], r["kecamatan_name"] or ""))
    tier_counts = {tier: sum(1 for r in rows if r["_tier"] == tier) for tier in ("HIGH", "MEDIUM", "LOW")}

    priority_text = _priority_line(body.hazard, summary, kec_name_by_id)

    alert_ids = alerts.alerts(body.week, body.hazard)["spatial_unit_ids"]
    alert_lines = [f"{kec_name_by_id[i]} ({i})" if i in kec_name_by_id else i for i in alert_ids]

    data = body.map_image_base64
    if data.startswith("data:"):
        data = data.split(",", 1)[1]
    image_bytes = base64.b64decode(data)

    pdf_bytes = _compose_pdf(body.week, body.hazard, image_bytes, rows, tier_counts, priority_text, alert_lines)
    filename = f"mata-hazard-{body.week}-{body.hazard}.pdf"
    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
