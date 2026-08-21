import csv
import json


def _int(v):
    return int(v) if v != "" else None


def _float(v):
    return float(v) if v != "" else None


def _bool(v):
    return v == "True" if v != "" else None


def parse_weekly_features(csv_path: str) -> list[dict]:
    """fire_weekly_features_*.csv -> weekly_feature rows (GRID + KECAMATAN)."""
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "spatial_unit_type": r["spatial_unit_type"],
            "spatial_unit_id": r["spatial_unit_id"],
            "iso_week": r["iso_week"],
            "hotspot_count": _int(r["hotspot_count"]),
            "hotspot_density": _float(r["hotspot_density"]),
            "mean_confidence": _float(r["mean_confidence"]),
            "max_confidence": _float(r["max_confidence"]),
            "mean_frp": _float(r["mean_frp"]),
            "max_frp": _float(r["max_frp"]),
            "trend_delta": _float(r["trend_delta"]),
            "land_cover_class": r["land_cover_class"] or None,
            "cumulative_rainfall_mm": _float(r["cumulative_rainfall_mm"]),
            "days_since_rain": _int(r["days_since_rain"]),
            "dry_spell_length": _int(r["dry_spell_length"]),
            "viirs_available": _bool(r["viirs_available"]),
        }
        for r in rows
    ]


def parse_scores(csv_path: str) -> list[dict]:
    """fire_scores_*.csv -> {spatial_unit_type (inferred from id prefix),
    spatial_unit_id, iso_week, risk_tier, predicted_next_week_count}."""
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    result = []
    for r in rows:
        spatial_unit_id = r["spatial_unit_id"]
        if spatial_unit_id.startswith("GRID-"):
            spatial_unit_type = "GRID"
        elif spatial_unit_id.startswith("KEC-"):
            spatial_unit_type = "KECAMATAN"
        else:
            raise ValueError(f"unrecognized spatial_unit_id prefix: {spatial_unit_id!r}")
        result.append({
            "spatial_unit_type": spatial_unit_type,
            "spatial_unit_id": spatial_unit_id,
            "iso_week": r["iso_week"],
            "risk_tier": r["risk_tier"],
            "predicted_next_week_count": _float(r["predicted_next_week_count"]),
        })
    return result


def parse_risk_summary(json_path: str) -> dict:
    """fire_risk_*.json -> parsed dict, for ingest_log validation only.

    Its by_kecamatan/count_by_tier/highest_predicted fields are aggregates
    already derivable from parse_weekly_features/parse_scores — nothing here
    is written to a DB table.
    """
    with open(json_path) as f:
        return json.load(f)
