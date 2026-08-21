from ingest.parsers import sar

W31 = "data/2026_w31"


def test_parse_sar_burned_area():
    row = sar.parse(
        f"{W31}/fire_sar_burned_area_2026-W31.json",
        f"{W31}/fire_sar_result_2026-W31.csv",
        f"{W31}/fire_sar_burned_area_2026-W31.tif",
    )

    assert row["iso_week"] == "2026-W31"
    assert row["burned_area_hectares"] == 28894.0
    assert row["pre_start"] is None
    assert row["classification_diagnostics"]["cluster_mean_rbd_vh_burned"] > 0
    assert row["geotiff_path"].endswith("fire_sar_burned_area_2026-W31.tif")
