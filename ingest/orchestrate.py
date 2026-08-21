import os
import sys

from ingest.parsers import fire, landslide, sar
from ingest.rasterize import rasterize
from shared.boundary import dissolve_kelurahan_to_kecamatan
from shared.db import delete_rows, read_rows, upsert_rows, write_rows

KELURAHAN_GEOJSON = "data/kelurahan.geojson"
OVERLAY_DIR = "generated/overlays"

# (file_type, hazard, filename builder) -- drives both presence classification
# and the ingest_log rows. file_type naming matches DATABASE.md's example
# convention (e.g. "fire_risk_json", "landslide_risk_tif").
FILE_TYPES = [
    ("fire_risk_json", "fire", lambda iso: f"fire_risk_{iso}.json"),
    ("fire_risk_grid_tif", "fire", lambda iso: f"fire_risk_{iso}_grid.tif"),
    ("fire_risk_kecamatan_tif", "fire", lambda iso: f"fire_risk_{iso}_kecamatan.tif"),
    ("fire_scores_csv", "fire", lambda iso: f"fire_scores_{iso}.csv"),
    ("fire_weekly_features_csv", "fire", lambda iso: f"fire_weekly_features_{iso}.csv"),
    ("fire_sar_result_csv", "fire", lambda iso: f"fire_sar_result_{iso}.csv"),
    ("fire_sar_burned_area_json", "fire", lambda iso: f"fire_sar_burned_area_{iso}.json"),
    ("fire_sar_burned_area_tif", "fire", lambda iso: f"fire_sar_burned_area_{iso}.tif"),
    ("landslide_risk_json", "landslide", lambda iso: f"landslide_risk_{iso}.json"),
    ("landslide_risk_tif", "landslide", lambda iso: f"landslide_risk_{iso}.tif"),
    ("landslide_scores_csv", "landslide", lambda iso: f"landslide_scores_{iso}.csv"),
    ("landslide_reclassified_csv", "landslide", lambda iso: f"landslide_reclassified_{iso}.csv"),
    ("landslide_static_features_csv", "landslide", lambda iso: f"landslide_static_features_{iso}.csv"),
    ("landslide_dynamic_features_csv", "landslide", lambda iso: f"landslide_dynamic_features_{iso}.csv"),
]

TIF_LAYER_TYPES = {
    "fire_risk_grid_tif": "fire_grid",
    "fire_risk_kecamatan_tif": "fire_kecamatan",
    "fire_sar_burned_area_tif": "burned_area",
    "landslide_risk_tif": "landslide_risk",
}


def week_to_iso(week_dir: str) -> str:
    # "data/2026_w34" -> "2026-W34"
    name = os.path.basename(week_dir.rstrip("/"))
    year, week = name.split("_w")
    return f"{year}-W{week}"


def classify_files(week_dir: str, iso_week: str) -> dict:
    """file_type -> (status, path_or_None), status in ok/mock_placeholder/missing."""
    classified = {}
    for file_type, _hazard, filename_fn in FILE_TYPES:
        real_path = os.path.join(week_dir, filename_fn(iso_week))
        if os.path.exists(real_path):
            classified[file_type] = ("ok", real_path)
        elif os.path.exists(real_path + ".mock"):
            classified[file_type] = ("mock_placeholder", None)
        else:
            classified[file_type] = ("missing", None)
    return classified


def ensure_kecamatan_boundary() -> int:
    # kecamatan_id is the table's own PK -- a real natural key, unlike the
    # bigserial-PK hazard tables -- so ON CONFLICT upsert applies directly.
    # (delete-then-insert would violate landslide_grid_cell's FK to this
    # table for the brief window a referenced kecamatan_id is missing.)
    rows = dissolve_kelurahan_to_kecamatan(KELURAHAN_GEOJSON)
    upsert_rows("kecamatan_boundary", rows, conflict_columns=["kecamatan_id"])
    return len(rows)


def ingest_fire(iso_week: str, files: dict, log: dict) -> dict:
    counts = {"weekly_feature": 0, "fire_risk_prediction": 0}

    if files["fire_weekly_features_csv"][0] == "ok":
        try:
            rows = fire.parse_weekly_features(files["fire_weekly_features_csv"][1])
            # fire_risk_prediction.feature_id has no ON DELETE CASCADE --
            # drop the child rows referencing this week's weekly_feature
            # rows before the parent delete, or a re-ingest 409s on FK.
            old_ids = [f["feature_id"] for f in read_rows("weekly_feature", {"iso_week": iso_week})]
            if old_ids:
                delete_rows("fire_risk_prediction", {"feature_id": old_ids})
            delete_rows("weekly_feature", {"iso_week": iso_week})
            write_rows("weekly_feature", rows)
            counts["weekly_feature"] = len(rows)
        except Exception as e:
            log["fire_weekly_features_csv"] = ("error", str(e))

    if files["fire_scores_csv"][0] == "ok":
        try:
            rows = fire.parse_scores(files["fire_scores_csv"][1])
            features = read_rows("weekly_feature", {"iso_week": iso_week})
            feature_id_by_unit = {(f["spatial_unit_type"], f["spatial_unit_id"]): f["feature_id"] for f in features}

            matched, skipped = [], 0
            for r in rows:
                feature_id = feature_id_by_unit.get((r["spatial_unit_type"], r["spatial_unit_id"]))
                if feature_id is None:
                    skipped += 1
                    continue
                matched.append({
                    "feature_id": feature_id,
                    "model_version": None,
                    "risk_tier": r["risk_tier"],
                    "predicted_next_week_count": r["predicted_next_week_count"],
                })
            # safety net for a hypothetical week where fire_scores_csv is
            # re-ingested without fire_weekly_features_csv also refreshing
            # (the normal path already cleared these via the block above).
            matched_ids = [m["feature_id"] for m in matched]
            if matched_ids:
                delete_rows("fire_risk_prediction", {"feature_id": matched_ids})
            write_rows("fire_risk_prediction", matched)
            counts["fire_risk_prediction"] = len(matched)
            if skipped:
                log["fire_scores_csv"] = ("ok", f"{skipped}/{len(rows)} rows skipped: no matching weekly_feature row")
        except Exception as e:
            log["fire_scores_csv"] = ("error", str(e))

    if files["fire_risk_json"][0] == "ok":
        try:
            fire.parse_risk_summary(files["fire_risk_json"][1])
        except Exception as e:
            log["fire_risk_json"] = ("error", str(e))

    return counts


def ingest_sar(iso_week: str, files: dict, log: dict) -> dict:
    counts = {"sar_burned_area_detection": 0}
    if files["fire_sar_burned_area_json"][0] == "ok" and files["fire_sar_result_csv"][0] == "ok":
        try:
            tif_status, tif_path = files["fire_sar_burned_area_tif"]
            row = sar.parse(
                files["fire_sar_burned_area_json"][1],
                files["fire_sar_result_csv"][1],
                tif_path if tif_status == "ok" else None,
            )
            delete_rows("sar_burned_area_detection", {"iso_week": iso_week})
            write_rows("sar_burned_area_detection", [row])
            counts["sar_burned_area_detection"] = 1
        except Exception as e:
            log["fire_sar_burned_area_json"] = ("error", str(e))
    return counts


def ingest_landslide(iso_week: str, files: dict, log: dict) -> dict:
    counts = {"landslide_weekly_score": 0, "landslide_static_feature": 0, "landslide_dynamic_feature": 0}
    valid_grid_ids = {r["grid_id"] for r in read_rows("landslide_grid_cell", {})}

    def _filter(rows):
        kept = [r for r in rows if r["grid_id"] in valid_grid_ids]
        skipped = len(rows) - len(kept)
        return kept, skipped

    if files["landslide_scores_csv"][0] == "ok":
        try:
            rows = landslide.parse_scores(files["landslide_scores_csv"][1])
            kept, skipped = _filter(rows)
            delete_rows("landslide_weekly_score", {"iso_week": iso_week})
            write_rows("landslide_weekly_score", kept)
            counts["landslide_weekly_score"] = len(kept)
            if skipped:
                log["landslide_scores_csv"] = ("ok", f"{skipped}/{len(rows)} rows skipped: grid_id not in landslide_grid_cell")
        except Exception as e:
            log["landslide_scores_csv"] = ("error", str(e))

    static_rows = dynamic_rows = None
    if files["landslide_static_features_csv"][0] == "ok" and files["landslide_dynamic_features_csv"][0] == "ok":
        try:
            static_rows = landslide.parse_static_features(files["landslide_static_features_csv"][1])
            dynamic_rows = landslide.parse_dynamic_features(files["landslide_dynamic_features_csv"][1])
        except Exception as e:
            log["landslide_static_features_csv"] = ("error", str(e))
    elif files["landslide_reclassified_csv"][0] == "ok":
        try:
            static_rows, dynamic_rows = landslide.parse_reclassified(files["landslide_reclassified_csv"][1])
            log["landslide_reclassified_csv"] = ("ok", "derived landslide_static_feature + landslide_dynamic_feature rows")
        except Exception as e:
            log["landslide_reclassified_csv"] = ("error", str(e))

    if static_rows is not None:
        kept, skipped = _filter(static_rows)
        delete_rows("landslide_static_feature", {"grid_id": [r["grid_id"] for r in static_rows]})
        write_rows("landslide_static_feature", kept)
        counts["landslide_static_feature"] = len(kept)
        if skipped:
            note = f"{skipped}/{len(static_rows)} rows skipped: grid_id not in landslide_grid_cell"
            file_type = "landslide_static_features_csv" if files["landslide_static_features_csv"][0] == "ok" else "landslide_reclassified_csv"
            log[file_type] = ("ok", note)

    if dynamic_rows is not None:
        kept, skipped = _filter(dynamic_rows)
        delete_rows("landslide_dynamic_feature", {"iso_week": iso_week})
        write_rows("landslide_dynamic_feature", kept)
        counts["landslide_dynamic_feature"] = len(kept)
        if skipped:
            note = f"{skipped}/{len(dynamic_rows)} rows skipped: grid_id not in landslide_grid_cell"
            file_type = "landslide_dynamic_features_csv" if files["landslide_dynamic_features_csv"][0] == "ok" else "landslide_reclassified_csv"
            log[file_type] = ("ok", note)

    if files["landslide_risk_json"][0] == "ok":
        try:
            landslide.parse_risk_summary(files["landslide_risk_json"][1])
        except Exception as e:
            log["landslide_risk_json"] = ("error", str(e))

    return counts


def ingest_rasters(iso_week: str, files: dict, log: dict) -> int:
    count = 0
    for file_type, layer_type in TIF_LAYER_TYPES.items():
        status, path = files[file_type]
        if status != "ok":
            continue
        try:
            out_path = os.path.join(OVERLAY_DIR, f"{iso_week}_{layer_type}.png")
            bounds = rasterize(path, layer_type, out_path)
            upsert_rows("raster_overlay", [{
                "iso_week": iso_week,
                "layer_type": layer_type,
                "png_path": out_path,
                "bounds": bounds,
            }], conflict_columns=["iso_week", "layer_type"])
            count += 1
        except Exception as e:
            log[file_type] = ("error", str(e))
    return count


def ingest_week(week_dir: str) -> dict:
    iso_week = week_to_iso(week_dir)
    files = classify_files(week_dir, iso_week)
    log = {file_type: (files[file_type][0], None) for file_type, _, _ in FILE_TYPES}

    boundary_count = ensure_kecamatan_boundary()
    fire_counts = ingest_fire(iso_week, files, log)
    sar_counts = ingest_sar(iso_week, files, log)
    landslide_counts = ingest_landslide(iso_week, files, log)
    raster_count = ingest_rasters(iso_week, files, log)

    delete_rows("ingest_log", {"iso_week": iso_week})
    log_rows = [
        {"iso_week": iso_week, "hazard": hazard, "file_type": file_type, "status": log[file_type][0], "detail": log[file_type][1]}
        for file_type, hazard, _ in FILE_TYPES
    ]
    write_rows("ingest_log", log_rows)

    return {
        "iso_week": iso_week,
        "kecamatan_boundary": boundary_count,
        "raster_overlay": raster_count,
        **fire_counts,
        **sar_counts,
        **landslide_counts,
    }


def main():
    if len(sys.argv) != 2:
        print("usage: python ingest.py data/YYYY_wWW", file=sys.stderr)
        sys.exit(1)

    summary = ingest_week(sys.argv[1])
    print(f"-- {summary['iso_week']} --")
    for table, count in summary.items():
        if table != "iso_week":
            print(f"  {table}: {count}")
