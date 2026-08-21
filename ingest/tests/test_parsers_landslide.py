from ingest.parsers import landslide

W30 = "data/2026_w30"
W31 = "data/2026_w31"


def test_parse_scores_handles_python_repr_factor_breakdown():
    rows = landslide.parse_scores(f"{W31}/landslide_scores_2026-W31.csv")

    assert len(rows) == 500
    row = rows[0]
    assert row["grid_id"] == "LS-00001"
    assert isinstance(row["factor_breakdown"], dict)
    assert row["factor_breakdown"]["ndvi_score"] is None
    assert row["factor_breakdown"]["slope_score"] == 3.0


def test_parse_static_features():
    rows = landslide.parse_static_features(f"{W30}/landslide_static_features_2026-W30.csv")

    assert len(rows) == 500
    assert rows[0]["grid_id"] == "LS-00001"
    assert rows[0]["aspect_class"] == "E"


def test_parse_dynamic_features():
    rows = landslide.parse_dynamic_features(f"{W30}/landslide_dynamic_features_2026-W30.csv")

    assert len(rows) == 500
    assert rows[0]["iso_week"] == "2026-W30"
    assert rows[0]["ndvi"] is not None


def test_parse_reclassified_splits_static_and_dynamic():
    static_rows, dynamic_rows = landslide.parse_reclassified(f"{W31}/landslide_reclassified_2026-W31.csv")

    assert len(static_rows) == len(dynamic_rows) == 500
    assert static_rows[0]["grid_id"] == dynamic_rows[0]["grid_id"] == "LS-00001"
    assert "slope_degrees" in static_rows[0]
    assert "cumulative_rainfall_mm" in dynamic_rows[0]
    assert "slope_score" not in static_rows[0]


def test_parse_risk_summary_is_well_formed():
    summary = landslide.parse_risk_summary(f"{W31}/landslide_risk_2026-W31.json")

    assert summary["iso_week"] == "2026-W31"
    assert "count_by_category" in summary
