import csv
import json
import os


def parse(json_path: str, csv_path: str, tif_path: str | None) -> dict:
    """fire_sar_burned_area_*.json + fire_sar_result_*.csv -> a single
    sar_burned_area_detection row (one row per week, not per-pixel).

    pre_start/pre_end/post_start/post_end aren't present anywhere in the
    real sample JSON -- left None rather than invented.
    """
    with open(json_path) as f:
        summary = json.load(f)

    with open(csv_path, newline="") as f:
        first_pixel = next(csv.DictReader(f), None)

    diagnostics = None
    if first_pixel is not None:
        diagnostics = {
            "cluster_mean_rbd_vh_burned": float(first_pixel["cluster_mean_rbd_vh_burned"]),
            "cluster_mean_rbd_vh_unburned": float(first_pixel["cluster_mean_rbd_vh_unburned"]),
        }

    return {
        "iso_week": summary["iso_week"],
        "method": summary["method"],
        "pre_start": None,
        "pre_end": None,
        "post_start": None,
        "post_end": None,
        "burned_area_hectares": summary.get("total_burned_area_hectares"),
        "classification_diagnostics": diagnostics,
        "geotiff_path": os.path.relpath(tif_path) if tif_path else None,
    }
