import type {
  AlertsResponse,
  BoundaryFeatureCollection,
  FireCellDetail,
  FireGridRow,
  FireSummary,
  IngestStatusRow,
  LandslideGridRow,
  LandslideSummary,
  OverlayResponse,
} from "../types";

// Thrown for network failure or a 5xx -- anything that should surface as
// Screen 4 (Connection Error). A 4xx (bad/unknown week) is not this: it's
// handled by callers as an expected "no data for this week" case.
export class ConnectionError extends Error {
  constructor(
    public method: string,
    public url: string,
  ) {
    super(`${method} ${url} failed`);
  }
}

// Empty in local dev -- the Vite proxy handles relative paths. Set on the
// deployed Static Site, where the frontend and API are different origins.
const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

function absolutize(path: string): string {
  return path.startsWith("/") ? `${API_BASE}${path}` : path;
}

async function fetchOk(method: string, url: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(absolutize(url), init);
  } catch {
    throw new ConnectionError(method, url);
  }
  if (res.status >= 500) throw new ConnectionError(method, url);
  if (!res.ok) {
    const err = new Error(`${method} ${url} -> ${res.status}`) as Error & { status: number };
    err.status = res.status;
    throw err;
  }
  return res;
}

async function get<T>(url: string): Promise<T> {
  const res = await fetchOk("GET", url);
  return res.json() as Promise<T>;
}

export const getWeeks = () => get<string[]>("/weeks");
export const getBoundaries = () => get<BoundaryFeatureCollection>("/boundaries");

export const getFireSummary = (week: string) => get<FireSummary>(`/fire/summary?week=${week}`);
export const getFireGrid = (week: string) => get<FireGridRow[]>(`/fire/grid?week=${week}`);
async function getOverlay(url: string): Promise<OverlayResponse> {
  const overlay = await get<OverlayResponse>(url);
  return overlay.png_url ? { ...overlay, png_url: absolutize(overlay.png_url) } : overlay;
}

export const getFireOverlay = (layer: "grid" | "kecamatan" | "burned_area", week: string) =>
  getOverlay(`/fire/overlay/${layer}?week=${week}`);

export const getLandslideSummary = (week: string) => get<LandslideSummary>(`/landslide/summary?week=${week}`);
export const getLandslideGrid = (week: string) => get<LandslideGridRow[]>(`/landslide/grid?week=${week}`);
export const getLandslideOverlay = (week: string) => getOverlay(`/landslide/overlay?week=${week}`);

export const getAlerts = (week: string, hazard: "fire" | "landslide" | "combined") =>
  get<AlertsResponse>(`/alerts?week=${week}&hazard=${hazard}`);

export const getFireCell = (spatialId: string, week: string) =>
  get<FireCellDetail>(`/cells/fire/${spatialId}?week=${week}`);

export const getIngestStatus = (week: string) => get<IngestStatusRow[]>(`/ingest-status?week=${week}`);

export async function postReportsPdf(week: string, hazard: "fire" | "landslide", mapImageBase64: string): Promise<Blob> {
  const res = await fetchOk("POST", "/reports/pdf", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ week, hazard, map_image_base64: mapImageBase64 }),
  });
  return res.blob();
}
