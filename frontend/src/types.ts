export type Hazard = "fire" | "landslide";

export type Tier = "low" | "med" | "high";

export function fireTierClass(tier: "LOW" | "MEDIUM" | "HIGH"): Tier {
  return tier === "HIGH" ? "high" : tier === "MEDIUM" ? "med" : "low";
}

// risk_category isn't a fixed enum (DATABASE.md: "5 categories + masked",
// varies by week) -- score_255 is always numeric, so tier coloring keys off
// the score rather than matching category strings.
export function landslideTierClass(score255: number): Tier {
  return score255 >= 180 ? "high" : score255 >= 60 ? "med" : "low";
}

// Real iso_week values are arbitrary strings from the DB (GET /weeks) --
// only the "2026-W99 — NO DATA" dropdown sentinel is hardcoded (App.tsx),
// so this stays a plain string rather than a fixed union.
export type Week = string;

// Overlay status is whatever ingest_log.status holds -- "ok" is the only
// value the UI treats specially (a renderable image); everything else
// (mock_placeholder, missing, any other ingest_log status) means unavailable.
export type MockStatus = string;

export interface LayerState {
  visible: boolean;
  opacity: number;
  label: string;
  color: string;
  status: MockStatus;
}

export interface AlertCounts {
  fire: number;
  landslide: number;
  combined: number;
}

export interface IngestRow {
  fileType: string;
  description: string;
  status: MockStatus;
  detail: string;
}

export interface OverlayImage {
  pngUrl: string | null;
  bounds: [[number, number], [number, number]] | null;
  status: MockStatus;
}

export type LayerKey = "fireGrid" | "fireKec" | "burned" | "landslideRisk";

export const HAZARD_LAYERS: Record<Hazard, LayerKey[]> = {
  fire: ["fireGrid", "fireKec", "burned"],
  landslide: ["landslideRisk"],
};

// Static per-layer cosmetics (label/color never change); runtime status/
// visibility/opacity are layered on top in CommandMapScreen.
export const LAYER_META: Record<LayerKey, { label: string; color: string }> = {
  fireGrid: { label: "Fire Risk — Grid", color: "var(--red)" },
  fireKec: { label: "Fire Risk — Kecamatan", color: "var(--amber)" },
  burned: { label: "Burned Area (SAR)", color: "var(--red)" },
  landslideRisk: { label: "Landslide Risk", color: "var(--yellow)" },
};

// ---------- real API response shapes ----------

export interface FireKecRow {
  kecamatan_id: string;
  kecamatan_name: string | null;
  risk_tier: "LOW" | "MEDIUM" | "HIGH";
  predicted_next_week_count: number | null;
}

export interface FireSummary {
  iso_week: string;
  count_by_tier: { LOW: number; MEDIUM: number; HIGH: number };
  highest_predicted: { spatial_unit_id: string; predicted_next_week_count: number } | null;
  by_kecamatan: FireKecRow[];
}

export interface FireGridRow {
  grid_id: string;
  risk_tier: "LOW" | "MEDIUM" | "HIGH";
  predicted_next_week_count: number | null;
}

export interface FireCellDetail {
  spatial_unit_id: string;
  spatial_unit_type: "GRID" | "KECAMATAN";
  risk_tier: "LOW" | "MEDIUM" | "HIGH";
  predicted_next_week_count: number | null;
  hotspot_count: number | null;
  hotspot_density: number | null;
  mean_frp: number | null;
  max_frp: number | null;
}

export interface LandslideKecRow {
  kecamatan_id: string;
  kecamatan_name: string | null;
  mean_score_255: number;
  highest_category: string;
}

export interface LandslideSummary {
  iso_week: string;
  count_by_category: Record<string, number>;
  area_by_category_ha: Record<string, number>;
  highest_risk_cell: { grid_id: string; kecamatan_id: string | null; score_255: number } | null;
  by_kecamatan: LandslideKecRow[];
}

export interface LandslideGridRow {
  grid_id: string;
  score_255: number;
  risk_category: string;
  factor_breakdown: Record<string, number> | null;
  slope_degrees: number | null;
  cumulative_rainfall_mm: number | null;
}

export interface OverlayResponse {
  status: string;
  detail?: string | null;
  png_url: string | null;
  bounds: [[number, number], [number, number]] | null;
}

export interface AlertsResponse {
  iso_week: string;
  hazard: "fire" | "landslide" | "combined";
  count: number;
  spatial_unit_ids: string[];
}

export type BoundaryFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Geometry,
  { kecamatan_id: string; kecamatan_name: string | null }
>;

export interface IngestStatusRow {
  file_type: string;
  status: MockStatus;
  detail: string;
}
