from ingest.parsers import fire

W31 = "data/2026_w31"


def test_parse_weekly_features_grid_and_kecamatan():
    rows = fire.parse_weekly_features(f"{W31}/fire_weekly_features_2026-W31.csv")

    assert len(rows) == 1475
    types = {r["spatial_unit_type"] for r in rows}
    assert types == {"GRID", "KECAMATAN"}
    kec = next(r for r in rows if r["spatial_unit_id"] == "KEC-01")
    assert kec["iso_week"] == "2026-W31"
    assert kec["hotspot_count"] == 0
    assert kec["mean_confidence"] is None  # blank in source CSV


def test_parse_scores_infers_spatial_unit_type():
    rows = fire.parse_scores(f"{W31}/fire_scores_2026-W31.csv")

    assert len(rows) == 1475
    grid_row = next(r for r in rows if r["spatial_unit_id"] == "GRID-00001")
    assert grid_row["spatial_unit_type"] == "GRID"
    kec_row = next(r for r in rows if r["spatial_unit_id"] == "KEC-01")
    assert kec_row["spatial_unit_type"] == "KECAMATAN"
    assert kec_row["risk_tier"] == "LOW"


def test_parse_risk_summary_is_well_formed():
    summary = fire.parse_risk_summary(f"{W31}/fire_risk_2026-W31.json")

    assert summary["iso_week"] == "2026-W31"
    assert len(summary["by_kecamatan"]) == 45
