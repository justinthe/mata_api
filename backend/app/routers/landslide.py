from collections import Counter

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from shared.db import get_connection, read_rows

router = APIRouter(prefix="/landslide")


def _ensure_valid_week(week: str) -> None:
    if not read_rows("ingest_log", {"iso_week": week}):
        raise HTTPException(400, f"unknown week: {week}")


def _grid_kecamatan_map() -> dict[str, str]:
    return {r["grid_id"]: r["kecamatan_id"] for r in read_rows("landslide_grid_cell")}


def _area_ha_by_grid() -> dict[str, float]:
    # ST_Area needs a geography cast for real geodesic hectares -- shared/db.py's
    # read_rows has no computed-column support, so this is the one raw query here.
    engine = get_connection()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT grid_id, ST_Area(geom::geography) / 10000 AS area_ha FROM landslide_grid_cell"))
        return {row.grid_id: row.area_ha for row in rows}


@router.get("/summary")
def landslide_summary(week: str):
    _ensure_valid_week(week)
    scores = read_rows("landslide_weekly_score", {"iso_week": week})

    count_by_category = dict(Counter(s["risk_category"] for s in scores))

    area_ha = _area_ha_by_grid()
    area_by_category: dict[str, float] = {}
    for s in scores:
        area_by_category[s["risk_category"]] = area_by_category.get(s["risk_category"], 0) + area_ha.get(s["grid_id"], 0)

    with_score = [s for s in scores if s["score_255"] is not None]
    highest = max(with_score, key=lambda s: s["score_255"], default=None)
    grid_kec = _grid_kecamatan_map()
    highest_risk_cell = None if highest is None else {
        "grid_id": highest["grid_id"],
        "kecamatan_id": grid_kec.get(highest["grid_id"]),
        "score_255": highest["score_255"],
    }

    kec_name_by_id = {r["kecamatan_id"]: r["kecamatan_name"] for r in read_rows("kecamatan_boundary")}
    by_kec: dict[str, list[dict]] = {}
    for s in with_score:
        kec_id = grid_kec.get(s["grid_id"])
        if kec_id is not None:
            by_kec.setdefault(kec_id, []).append(s)
    by_kecamatan = sorted(
        (
            {
                "kecamatan_id": kec_id,
                "kecamatan_name": kec_name_by_id.get(kec_id),
                "mean_score_255": round(sum(s["score_255"] for s in rows) / len(rows), 2),
                "highest_category": max(rows, key=lambda s: s["score_255"])["risk_category"],
            }
            for kec_id, rows in by_kec.items()
        ),
        key=lambda x: x["kecamatan_id"],
    )

    return {
        "iso_week": week,
        "count_by_category": count_by_category,
        "area_by_category_ha": {k: round(v, 4) for k, v in area_by_category.items()},
        "highest_risk_cell": highest_risk_cell,
        "by_kecamatan": by_kecamatan,
    }


@router.get("/grid")
def landslide_grid(week: str):
    _ensure_valid_week(week)
    scores = read_rows("landslide_weekly_score", {"iso_week": week})
    grid_ids = [s["grid_id"] for s in scores]

    static = {f["grid_id"]: f for f in read_rows("landslide_static_feature", {"grid_id": grid_ids})} if grid_ids else {}
    dynamic = {f["grid_id"]: f for f in read_rows("landslide_dynamic_feature", {"grid_id": grid_ids, "iso_week": week})} if grid_ids else {}

    return sorted(
        (
            {
                "grid_id": s["grid_id"],
                "score_255": s["score_255"],
                "risk_category": s["risk_category"],
                "factor_breakdown": s["factor_breakdown"],
                "slope_degrees": static.get(s["grid_id"], {}).get("slope_degrees"),
                "cumulative_rainfall_mm": dynamic.get(s["grid_id"], {}).get("cumulative_rainfall_mm"),
            }
            for s in scores
        ),
        key=lambda x: x["grid_id"],
    )


@router.get("/overlay")
def landslide_overlay(week: str):
    _ensure_valid_week(week)

    overlays = read_rows("raster_overlay", {"iso_week": week, "layer_type": "landslide_risk"})
    if overlays:
        row = overlays[0]
        return {"status": "ok", "png_url": f"/{row['png_path']}", "bounds": row["bounds"]}

    logs = read_rows("ingest_log", {"iso_week": week, "file_type": "landslide_risk_tif"})
    log = logs[0] if logs else None
    return {
        "status": log["status"] if log else "missing",
        "detail": log["detail"] if log else None,
        "png_url": None,
        "bounds": None,
    }
