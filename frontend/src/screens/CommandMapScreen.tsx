import { useEffect, useRef, useState } from "react";
import type { Map as LeafletMap } from "leaflet";
import MapView from "../components/MapView";
import LayerControls from "../components/LayerControls";
import AlertPanel from "../components/AlertPanel";
import InspectPopup from "../components/InspectPopup";
import GridCellList from "../components/GridCellList";
import * as api from "../api/client";
import { ConnectionError } from "../api/client";
import {
  LAYER_META,
  type AlertCounts,
  type BoundaryFeatureCollection,
  type FireGridRow,
  type FireSummary,
  type Hazard,
  type LandslideGridRow,
  type LandslideSummary,
  type LayerKey,
  type LayerState,
  type OverlayImage,
  type Week,
} from "../types";
import { DashboardContext, type DashboardContextValue, type PopupTarget } from "./dashboard-context";

const ALL_LAYER_KEYS = Object.keys(LAYER_META) as LayerKey[];

const DEFAULT_UI_LAYERS: Record<LayerKey, { visible: boolean; opacity: number }> = {
  fireGrid: { visible: true, opacity: 80 },
  fireKec: { visible: true, opacity: 60 },
  burned: { visible: false, opacity: 70 },
  landslideRisk: { visible: true, opacity: 75 },
};

const EMPTY_OVERLAY: OverlayImage = { pngUrl: null, bounds: null, status: "missing" };
const EMPTY_ALERTS: AlertCounts = { fire: 0, landslide: 0, combined: 0 };

export default function CommandMapScreen({
  week,
  weekOptions,
  onSelectWeek,
  showToast,
  onConnectionError,
  onEmptyWeek,
}: {
  week: Week;
  weekOptions: Week[];
  onSelectWeek: (week: Week) => void;
  showToast: (msg: string) => void;
  onConnectionError: (trace: string) => void;
  onEmptyWeek: () => void;
}) {
  const mapRef = useRef<LeafletMap | null>(null);
  const [hazard, setHazard] = useState<Hazard>("fire");
  const [uiLayers, setUiLayers] = useState(DEFAULT_UI_LAYERS);
  const [flashingIds, setFlashingIds] = useState<Set<string>>(new Set());
  const [popup, setPopup] = useState<PopupTarget | null>(null);
  const [loading, setLoading] = useState(true);

  const [boundaries, setBoundaries] = useState<BoundaryFeatureCollection | null>(null);
  const [fireSummary, setFireSummary] = useState<FireSummary | null>(null);
  const [fireGrid, setFireGrid] = useState<FireGridRow[]>([]);
  const [landslideSummary, setLandslideSummary] = useState<LandslideSummary | null>(null);
  const [landslideGrid, setLandslideGrid] = useState<LandslideGridRow[]>([]);
  const [overlays, setOverlays] = useState<Record<LayerKey, OverlayImage>>({
    fireGrid: EMPTY_OVERLAY,
    fireKec: EMPTY_OVERLAY,
    burned: EMPTY_OVERLAY,
    landslideRisk: EMPTY_OVERLAY,
  });
  const [alerts, setAlerts] = useState<AlertCounts>(EMPTY_ALERTS);
  const [alertIds, setAlertIds] = useState<Record<"fire" | "landslide" | "combined", string[]>>({
    fire: [],
    landslide: [],
    combined: [],
  });

  // Boundaries are week-independent -- fetch once per mount.
  useEffect(() => {
    let cancelled = false;
    api
      .getBoundaries()
      .then((b) => !cancelled && setBoundaries(b))
      .catch((err) => {
        if (!cancelled && err instanceof ConnectionError) onConnectionError(`${err.method} ${err.url} → connection failed`);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setPopup(null);
    (async () => {
      try {
        const [fs, fg, ls, lg, gridOv, kecOv, burnedOv, lsOv, aFire, aLandslide, aCombined] = await Promise.all([
          api.getFireSummary(week),
          api.getFireGrid(week),
          api.getLandslideSummary(week),
          api.getLandslideGrid(week),
          api.getFireOverlay("grid", week),
          api.getFireOverlay("kecamatan", week),
          api.getFireOverlay("burned_area", week),
          api.getLandslideOverlay(week),
          api.getAlerts(week, "fire"),
          api.getAlerts(week, "landslide"),
          api.getAlerts(week, "combined"),
        ]);
        if (cancelled) return;
        // Phase-07 spec: Empty Week also triggers when a week's summary
        // comes back empty (not just when /weeks omits it) -- both hazards
        // returning nothing means an ingest_log row exists with no actual
        // rows behind it.
        if (fg.length === 0 && lg.length === 0 && fs.by_kecamatan.length === 0 && ls.by_kecamatan.length === 0) {
          onEmptyWeek();
          return;
        }
        setFireSummary(fs);
        setFireGrid(fg);
        setLandslideSummary(ls);
        setLandslideGrid(lg);
        setOverlays({
          fireGrid: { pngUrl: gridOv.png_url, bounds: gridOv.bounds, status: gridOv.status },
          fireKec: { pngUrl: kecOv.png_url, bounds: kecOv.bounds, status: kecOv.status },
          burned: { pngUrl: burnedOv.png_url, bounds: burnedOv.bounds, status: burnedOv.status },
          landslideRisk: { pngUrl: lsOv.png_url, bounds: lsOv.bounds, status: lsOv.status },
        });
        setAlerts({ fire: aFire.count, landslide: aLandslide.count, combined: aCombined.count });
        setAlertIds({ fire: aFire.spatial_unit_ids, landslide: aLandslide.spatial_unit_ids, combined: aCombined.spatial_unit_ids });
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ConnectionError) {
          onConnectionError(`${err.method} ${err.url} → connection failed`);
        } else {
          throw err;
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [week, onConnectionError, onEmptyWeek]);

  const toggleLayer = (key: LayerKey) => {
    setUiLayers((prev) => ({ ...prev, [key]: { ...prev[key], visible: !prev[key].visible } }));
  };

  const setLayerOpacity = (key: LayerKey, value: number) => {
    setUiLayers((prev) => ({ ...prev, [key]: { ...prev[key], opacity: value } }));
  };

  const layers = Object.fromEntries(
    ALL_LAYER_KEYS.map((key) => [
      key,
      {
        ...LAYER_META[key],
        ...uiLayers[key],
        status: overlays[key].status,
      },
    ]),
  ) as Record<LayerKey, LayerState>;

  const flashAlerts = (kind: "fire" | "landslide" | "combined") => {
    const ids = alertIds[kind];
    if (kind === "landslide" && hazard !== "landslide") setHazard("landslide");
    if (kind === "fire" && hazard !== "fire") setHazard("fire");
    setFlashingIds(new Set(ids));
    showToast(`Zoomed to ${ids.length} ${kind} alert area(s).`);
    setTimeout(() => setFlashingIds(new Set()), 4300);
  };

  const handleSelectWeek = (wk: Week) => {
    setPopup(null);
    onSelectWeek(wk);
  };

  const value: DashboardContextValue = {
    week,
    hazard,
    setHazard,
    layers,
    overlays,
    toggleLayer,
    setLayerOpacity,
    boundaries,
    fireSummary,
    fireGrid,
    landslideGrid,
    landslideSummary,
    alerts,
    flashingIds,
    flashAlerts,
    popup,
    openPopup: setPopup,
    closePopup: () => setPopup(null),
    showToast,
    onSelectWeek: handleSelectWeek,
    mapRef,
  };

  return (
    <DashboardContext.Provider value={value}>
      <section id="dashboard">
        <div className="layout">
          <aside>
            <div className="section-label">Week</div>
            <select id="weekSelect" value={week} onChange={(e) => handleSelectWeek(e.target.value)}>
              {weekOptions.map((w) => (
                <option key={w} value={w}>
                  {w === weekOptions[0] ? `${w} (latest)` : w === "2026-W99" ? `${w} — NO DATA` : w}
                </option>
              ))}
            </select>
            <LayerControls />
            <GridCellList />
          </aside>
          <MapView loading={loading} />
          <aside className="right">
            <AlertPanel />
          </aside>
        </div>
        {popup && <InspectPopup />}
      </section>
    </DashboardContext.Provider>
  );
}
