// Static file_type -> human description lookup for the Ingest Log screen.
// ingest_log has no description column, so this stays client-side; keys and
// order match ingest/orchestrate.py's FILE_TYPES exactly (the real ingest
// canonical list), not the old glob-name mock this replaced.
export const FILE_TYPE_INFO: [string, string][] = [
  ["fire_risk_json", "Fire — risk summary"],
  ["fire_risk_grid_tif", "Fire — grid raster"],
  ["fire_risk_kecamatan_tif", "Fire — kecamatan raster"],
  ["fire_scores_csv", "Fire — grid score/prediction"],
  ["fire_weekly_features_csv", "Fire — weekly features"],
  ["fire_sar_result_csv", "Fire — SAR pixel result"],
  ["fire_sar_burned_area_json", "Fire — burned area (summary)"],
  ["fire_sar_burned_area_tif", "Fire — burned area raster"],
  ["landslide_risk_json", "Landslide — risk summary"],
  ["landslide_risk_tif", "Landslide — risk raster"],
  ["landslide_scores_csv", "Landslide — grid scores"],
  ["landslide_reclassified_csv", "Landslide — reclassified"],
  ["landslide_static_features_csv", "Landslide — static features"],
  ["landslide_dynamic_features_csv", "Landslide — dynamic features"],
];
