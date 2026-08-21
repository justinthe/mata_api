import { vi } from "vitest";

// Test-only canned responses matching the real routers' shapes
// (backend/app/routers/{fire,landslide,alerts,cells,weeks,boundaries}.py) --
// used by vitest.setup.ts (default "ok" install before every test) and by
// individual tests that need a different mode (e.g. simulating an outage).
const WEEKS = ["2026-W34", "2026-W31", "2026-W30"];

const BOUNDARIES = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { kecamatan_id: "KEC-001", kecamatan_name: "Majalengka" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [108.05, -6.9],
            [108.15, -6.9],
            [108.15, -6.8],
            [108.05, -6.8],
            [108.05, -6.9],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: { kecamatan_id: "KEC-002", kecamatan_name: "Jatiwangi" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [108.15, -6.9],
            [108.25, -6.9],
            [108.25, -6.8],
            [108.15, -6.8],
            [108.15, -6.9],
          ],
        ],
      },
    },
  ],
};

function fireSummary(week: string) {
  return {
    iso_week: week,
    count_by_tier: { LOW: 8, MEDIUM: 2, HIGH: 1 },
    highest_predicted: { spatial_unit_id: "GRID-00001", predicted_next_week_count: 5 },
    by_kecamatan: [
      { kecamatan_id: "KEC-001", kecamatan_name: "Majalengka", risk_tier: "HIGH", predicted_next_week_count: 5 },
      { kecamatan_id: "KEC-002", kecamatan_name: "Jatiwangi", risk_tier: "LOW", predicted_next_week_count: 0 },
    ],
  };
}

function fireGrid() {
  return [
    { grid_id: "GRID-00001", risk_tier: "HIGH", predicted_next_week_count: 5 },
    { grid_id: "GRID-00002", risk_tier: "LOW", predicted_next_week_count: 0 },
  ];
}

function fireCell(id: string) {
  const high = id === "GRID-00001" || id === "KEC-001";
  return {
    spatial_unit_id: id,
    spatial_unit_type: id.startsWith("KEC") ? "KECAMATAN" : "GRID",
    risk_tier: high ? "HIGH" : "LOW",
    predicted_next_week_count: high ? 5 : 0,
    hotspot_count: high ? 3 : 0,
    hotspot_density: high ? 0.4 : 0,
    mean_frp: high ? 12.3 : 0,
    max_frp: high ? 30.1 : 0,
  };
}

function landslideSummary(week: string) {
  return {
    iso_week: week,
    count_by_category: { "Landslides Expected": 1, "Landslide Unlikely": 49 },
    area_by_category_ha: { "Landslides Expected": 0.8, "Landslide Unlikely": 40.2 },
    highest_risk_cell: { grid_id: "LS-00001", kecamatan_id: "KEC-001", score_255: 92 },
    by_kecamatan: [
      { kecamatan_id: "KEC-001", kecamatan_name: "Majalengka", mean_score_255: 80, highest_category: "Landslides Expected" },
      { kecamatan_id: "KEC-002", kecamatan_name: "Jatiwangi", mean_score_255: 5, highest_category: "Landslide Unlikely" },
    ],
  };
}

function landslideGrid() {
  return [
    {
      grid_id: "LS-00001",
      score_255: 92,
      risk_category: "Landslides Expected",
      factor_breakdown: { slope: 30, rainfall: 40 },
      slope_degrees: 30,
      cumulative_rainfall_mm: 40,
    },
    {
      grid_id: "LS-00002",
      score_255: 5,
      risk_category: "Landslide Unlikely",
      factor_breakdown: { slope: 5, rainfall: 2 },
      slope_degrees: 5,
      cumulative_rainfall_mm: 2,
    },
  ];
}

const OVERLAY_OK = { status: "ok", detail: null, png_url: "/generated/overlays/mock.png", bounds: [[-6.9, 108.05], [-6.7, 108.2]] };

function ingestStatus(week: string) {
  if (week === "2026-W99") return [];
  return [
    { file_type: "fire_risk_json", status: "ok", detail: "ingested" },
    { file_type: "landslide_risk_json", status: "ok", detail: "ingested" },
    {
      file_type: "landslide_risk_tif",
      status: week === "2026-W34" ? "mock_placeholder" : "ok",
      detail: week === "2026-W34" ? "placeholder written, no source raster" : "ingested",
    },
    {
      file_type: "landslide_scores_csv",
      status: week === "2026-W34" ? "missing" : "ok",
      detail: week === "2026-W34" ? "no file found" : "ingested",
    },
  ];
}

function alerts(hazard: string) {
  const ids = hazard === "landslide" ? ["LS-00001"] : ["KEC-001"];
  return { iso_week: "2026-W34", hazard, count: ids.length, spatial_unit_ids: ids };
}

function respond(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function route(url: string, empty: boolean, method: string): Response {
  const { pathname, searchParams } = new URL(url, "http://test.local");
  const week = searchParams.get("week") ?? "2026-W34";

  if (pathname === "/reports/pdf" && method === "POST") {
    return new Response(new Blob([new Uint8Array([0x25, 0x50, 0x44, 0x46])]), {
      status: 200,
      headers: { "content-type": "application/pdf" },
    });
  }
  if (pathname === "/weeks") return respond(WEEKS);
  if (pathname === "/boundaries") return respond(BOUNDARIES);
  if (pathname === "/fire/summary") return respond(empty ? { ...fireSummary(week), by_kecamatan: [] } : fireSummary(week));
  if (pathname === "/fire/grid") return respond(empty ? [] : fireGrid());
  if (pathname.startsWith("/fire/overlay/")) return respond(OVERLAY_OK);
  if (pathname === "/landslide/summary")
    return respond(empty ? { ...landslideSummary(week), by_kecamatan: [] } : landslideSummary(week));
  if (pathname === "/landslide/grid") return respond(empty ? [] : landslideGrid());
  if (pathname === "/landslide/overlay") return respond(OVERLAY_OK);
  if (pathname === "/alerts") return respond(alerts(searchParams.get("hazard") ?? "fire"));
  if (pathname.startsWith("/cells/fire/")) return respond(fireCell(pathname.split("/").pop()!));
  if (pathname === "/ingest-status") return respond(ingestStatus(week));
  return respond({ detail: "not found" }, 404);
}

/** Installs a stubbed global fetch. mode "ok" serves canned real-shaped
 * data; "empty" serves a valid but all-empty week (ingest_log row, no
 * actual data -- Phase 07's empty-summary Empty Week trigger); "down"
 * rejects every call (simulated API outage). */
export function installMockFetch(mode: "ok" | "empty" | "down" = "ok") {
  const impl =
    mode === "down"
      ? () => Promise.reject(new TypeError("failed to fetch"))
      : (input: RequestInfo | URL, init?: RequestInit) =>
          Promise.resolve(route(typeof input === "string" ? input : input.toString(), mode === "empty", init?.method ?? "GET"));
  const fn = vi.fn(impl);
  vi.stubGlobal("fetch", fn);
  return fn;
}
