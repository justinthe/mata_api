from collections import Counter

from fastapi import APIRouter, HTTPException

from shared.db import read_rows

router = APIRouter(prefix="/fire")

# layer -> (raster_overlay.layer_type, ingest_log.file_type), names match
# ingest/orchestrate.py's TIF_LAYER_TYPES / FILE_TYPES verbatim.
LAYER_INFO = {
    "grid": ("fire_grid", "fire_risk_grid_tif"),
    "kecamatan": ("fire_kecamatan", "fire_risk_kecamatan_tif"),
    "burned_area": ("burned_area", "fire_sar_burned_area_tif"),
}


def _ensure_valid_week(week: str) -> None:
    if not read_rows("ingest_log", {"iso_week": week}):
        raise HTTPException(400, f"unknown week: {week}")


def _predictions_for_week(week: str) -> tuple[list[dict], dict[int, dict]]:
    features = read_rows("weekly_feature", {"iso_week": week})
    feature_by_id = {f["feature_id"]: f for f in features}
    feature_ids = list(feature_by_id)
    predictions = read_rows("fire_risk_prediction", {"feature_id": feature_ids}) if feature_ids else []
    return predictions, feature_by_id


@router.get("/summary")
def fire_summary(week: str):
    _ensure_valid_week(week)
    predictions, feature_by_id = _predictions_for_week(week)

    tier_counts = Counter(p["risk_tier"] for p in predictions)
    count_by_tier = {tier: tier_counts.get(tier, 0) for tier in ("LOW", "MEDIUM", "HIGH")}

    with_value = [p for p in predictions if p["predicted_next_week_count"] is not None]
    highest = max(with_value, key=lambda p: p["predicted_next_week_count"], default=None)
    highest_predicted = None if highest is None else {
        "spatial_unit_id": feature_by_id[highest["feature_id"]]["spatial_unit_id"],
        "predicted_next_week_count": highest["predicted_next_week_count"],
    }

    kec_name_by_id = {r["kecamatan_id"]: r["kecamatan_name"] for r in read_rows("kecamatan_boundary")}
    by_kecamatan = sorted(
        (
            {
                "kecamatan_id": feature_by_id[p["feature_id"]]["spatial_unit_id"],
                "kecamatan_name": kec_name_by_id.get(feature_by_id[p["feature_id"]]["spatial_unit_id"]),
                "risk_tier": p["risk_tier"],
                "predicted_next_week_count": p["predicted_next_week_count"],
            }
            for p in predictions
            if feature_by_id[p["feature_id"]]["spatial_unit_type"] == "KECAMATAN"
        ),
        key=lambda x: x["kecamatan_id"],
    )

    return {
        "iso_week": week,
        "count_by_tier": count_by_tier,
        "highest_predicted": highest_predicted,
        "by_kecamatan": by_kecamatan,
    }


@router.get("/grid")
def fire_grid(week: str):
    _ensure_valid_week(week)
    predictions, feature_by_id = _predictions_for_week(week)
    return sorted(
        (
            {
                "grid_id": feature_by_id[p["feature_id"]]["spatial_unit_id"],
                "risk_tier": p["risk_tier"],
                "predicted_next_week_count": p["predicted_next_week_count"],
            }
            for p in predictions
            if feature_by_id[p["feature_id"]]["spatial_unit_type"] == "GRID"
        ),
        key=lambda x: x["grid_id"],
    )


@router.get("/overlay/{layer}")
def fire_overlay(layer: str, week: str):
    if layer not in LAYER_INFO:
        raise HTTPException(400, f"unknown layer: {layer}")
    _ensure_valid_week(week)
    layer_type, file_type = LAYER_INFO[layer]

    overlays = read_rows("raster_overlay", {"iso_week": week, "layer_type": layer_type})
    if overlays:
        row = overlays[0]
        return {"status": "ok", "png_url": f"/{row['png_path']}", "bounds": row["bounds"]}

    logs = read_rows("ingest_log", {"iso_week": week, "file_type": file_type})
    log = logs[0] if logs else None
    return {
        "status": log["status"] if log else "missing",
        "detail": log["detail"] if log else None,
        "png_url": None,
        "bounds": None,
    }
