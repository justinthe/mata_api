import { createContext, useContext, type RefObject } from "react";
import type { Map as LeafletMap } from "leaflet";
import type {
  AlertCounts,
  BoundaryFeatureCollection,
  FireGridRow,
  FireSummary,
  Hazard,
  LandslideGridRow,
  LandslideSummary,
  LayerKey,
  LayerState,
  OverlayImage,
  Week,
} from "../types";

export type PopupTarget =
  | { kind: "fire"; spatialId: string; x: number; y: number }
  | { kind: "landslideGrid"; gridId: string; x: number; y: number }
  | { kind: "landslideKec"; kecamatanId: string; x: number; y: number };

export interface DashboardContextValue {
  week: Week;
  hazard: Hazard;
  setHazard: (h: Hazard) => void;
  layers: Record<LayerKey, LayerState>;
  overlays: Record<LayerKey, OverlayImage>;
  toggleLayer: (key: LayerKey) => void;
  setLayerOpacity: (key: LayerKey, value: number) => void;
  boundaries: BoundaryFeatureCollection | null;
  fireSummary: FireSummary | null;
  fireGrid: FireGridRow[];
  landslideGrid: LandslideGridRow[];
  landslideSummary: LandslideSummary | null;
  alerts: AlertCounts;
  flashingIds: Set<string>;
  flashAlerts: (kind: "fire" | "landslide" | "combined") => void;
  popup: PopupTarget | null;
  openPopup: (target: PopupTarget) => void;
  closePopup: () => void;
  showToast: (msg: string) => void;
  onSelectWeek: (week: Week) => void;
  mapRef: RefObject<LeafletMap | null>;
}

export const DashboardContext = createContext<DashboardContextValue | null>(null);

export function useDashboard(): DashboardContextValue {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error("useDashboard must be used within CommandMapScreen");
  return ctx;
}
