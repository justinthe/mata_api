from fastapi import APIRouter, HTTPException

from app.routers import fire, landslide
from shared.db import read_rows

router = APIRouter()


def _fire_cell(spatial_id: str, week: str) -> dict:
    predictions, feature_by_id = fire._predictions_for_week(week)
    for p in predictions:
        feat = feature_by_id[p["feature_id"]]
        if feat["spatial_unit_id"] == spatial_id:
            return {
                "spatial_unit_id": feat["spatial_unit_id"],
                "spatial_unit_type": feat["spatial_unit_type"],
                "risk_tier": p["risk_tier"],
                "predicted_next_week_count": p["predicted_next_week_count"],
                "hotspot_count": feat["hotspot_count"],
                "hotspot_density": feat["hotspot_density"],
                "mean_frp": feat["mean_frp"],
                "max_frp": feat["max_frp"],
            }
    raise HTTPException(404, f"no fire cell {spatial_id} for week {week}")


def _landslide_cell(spatial_id: str, week: str) -> dict:
    scores = read_rows("landslide_weekly_score", {"iso_week": week, "grid_id": spatial_id})
    if not scores:
        raise HTTPException(404, f"no landslide cell {spatial_id} for week {week}")
    s = scores[0]
    static = read_rows("landslide_static_feature", {"grid_id": spatial_id})
    dynamic = read_rows("landslide_dynamic_feature", {"grid_id": spatial_id, "iso_week": week})
    return {
        "grid_id": s["grid_id"],
        "score_255": s["score_255"],
        "risk_category": s["risk_category"],
        "factor_breakdown": s["factor_breakdown"],
        "slope_degrees": static[0]["slope_degrees"] if static else None,
        "cumulative_rainfall_mm": dynamic[0]["cumulative_rainfall_mm"] if dynamic else None,
    }


@router.get("/cells/{hazard}/{spatial_id}")
def cell(hazard: str, spatial_id: str, week: str):
    if hazard == "fire":
        fire._ensure_valid_week(week)
        return _fire_cell(spatial_id, week)
    if hazard == "landslide":
        landslide._ensure_valid_week(week)
        return _landslide_cell(spatial_id, week)
    raise HTTPException(400, f"unknown hazard: {hazard}")
