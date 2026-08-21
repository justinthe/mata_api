import ast
import csv
import json


def _float(v):
    return float(v) if v not in ("", None) else None


def parse_scores(csv_path: str) -> list[dict]:
    """landslide_scores_*.csv -> landslide_weekly_score rows.

    factor_breakdown is a Python dict repr (single quotes, bare None), not
    JSON -- ast.literal_eval, not json.loads.
    """
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "grid_id": r["grid_id"],
            "iso_week": r["iso_week"],
            "score_255": _float(r["score_255"]),
            "risk_category": r["risk_category"],
            "factor_breakdown": ast.literal_eval(r["factor_breakdown"]),
        }
        for r in rows
    ]


def parse_static_features(csv_path: str) -> list[dict]:
    """landslide_static_features_*.csv -> landslide_static_feature rows."""
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "grid_id": r["grid_id"],
            "slope_degrees": _float(r["slope_degrees"]),
            "aspect_class": r["aspect_class"] or None,
            "land_cover_class": r["land_cover_class"] or None,
            "soil_texture_class": r["soil_texture_class"] or None,
            "drainage_distance_m": _float(r["drainage_distance_m"]),
        }
        for r in rows
    ]


def parse_dynamic_features(csv_path: str) -> list[dict]:
    """landslide_dynamic_features_*.csv -> landslide_dynamic_feature rows."""
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "grid_id": r["grid_id"],
            "iso_week": r["iso_week"],
            "cumulative_rainfall_mm": _float(r["cumulative_rainfall_mm"]),
            "ndvi": _float(r["ndvi"]),
        }
        for r in rows
    ]


def parse_reclassified(csv_path: str) -> tuple[list[dict], list[dict]]:
    """landslide_reclassified_*.csv -> (static rows, dynamic rows).

    Used only when a week ships this combined file instead of the split
    static/dynamic CSVs. Per-factor *_score/masked columns are ignored --
    that breakdown comes from landslide_scores_*.csv's factor_breakdown.
    """
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    static_rows = [
        {
            "grid_id": r["grid_id"],
            "slope_degrees": _float(r["slope_degrees"]),
            "aspect_class": r["aspect_class"] or None,
            "land_cover_class": r["land_cover_class"] or None,
            "soil_texture_class": r["soil_texture_class"] or None,
            "drainage_distance_m": _float(r["drainage_distance_m"]),
        }
        for r in rows
    ]
    dynamic_rows = [
        {
            "grid_id": r["grid_id"],
            "iso_week": r["iso_week"],
            "cumulative_rainfall_mm": _float(r["cumulative_rainfall_mm"]),
            "ndvi": _float(r["ndvi"]),
        }
        for r in rows
    ]
    return static_rows, dynamic_rows


def parse_risk_summary(json_path: str) -> dict:
    """landslide_risk_*.json -> parsed dict, for ingest_log validation only.

    It's an aggregate summary (count_by_category, by_kecamatan means,
    highest_risk_cell) with no per-grid rows -- no matching DB table.
    """
    with open(json_path) as f:
        return json.load(f)
