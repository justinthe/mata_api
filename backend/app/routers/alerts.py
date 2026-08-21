from fastapi import APIRouter, HTTPException

from app.routers import fire, landslide
from shared.db import read_rows

router = APIRouter()

HAZARDS = ("fire", "landslide", "combined")
LANDSLIDE_ALERT_CATEGORIES = {"Landslides Expected", "Active Landslides"}


def _fire_high_ids(week: str, kecamatan_only: bool = False) -> set[str]:
    predictions, feature_by_id = fire._predictions_for_week(week)
    return {
        feature_by_id[p["feature_id"]]["spatial_unit_id"]
        for p in predictions
        if p["risk_tier"] == "HIGH"
        and (not kecamatan_only or feature_by_id[p["feature_id"]]["spatial_unit_type"] == "KECAMATAN")
    }


def _landslide_alert_scores(week: str) -> list[dict]:
    scores = read_rows("landslide_weekly_score", {"iso_week": week})
    return [s for s in scores if s["risk_category"] in LANDSLIDE_ALERT_CATEGORIES]


@router.get("/alerts")
def alerts(week: str, hazard: str):
    if hazard not in HAZARDS:
        raise HTTPException(400, f"unknown hazard: {hazard}")
    fire._ensure_valid_week(week)

    if hazard == "fire":
        ids = _fire_high_ids(week)
    elif hazard == "landslide":
        ids = {s["grid_id"] for s in _landslide_alert_scores(week)}
    else:
        grid_kec = landslide._grid_kecamatan_map()
        landslide_kec_ids = {grid_kec.get(s["grid_id"]) for s in _landslide_alert_scores(week)}
        landslide_kec_ids.discard(None)
        ids = _fire_high_ids(week, kecamatan_only=True) & landslide_kec_ids

    return {
        "iso_week": week,
        "hazard": hazard,
        "count": len(ids),
        "spatial_unit_ids": sorted(ids),
    }
