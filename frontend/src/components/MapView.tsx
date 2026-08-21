import { useRef } from "react";
import type { RefObject } from "react";
import { GeoJSON, ImageOverlay, MapContainer, TileLayer, ZoomControl } from "react-leaflet";
import type {
  Layer,
  LeafletMouseEvent,
  Map as LeafletMap,
  Polygon as LeafletPolygon,
  PathOptions,
} from "leaflet";
import type { Feature, Geometry } from "geojson";
import { HAZARD_LAYERS, fireTierClass, landslideTierClass } from "../types";
import { useDashboard } from "../screens/dashboard-context";

// No real geometry exists for grid-tier cells (fire's ~1450 GRID rows,
// landslide's 50) in any backend route -- kecamatan polygons (/boundaries)
// are the only geo-accurate, clickable map layer. Grid-tier detail lives in
// GridCellList instead (see CLAUDE.md Phase 07 notes).
const FALLBACK_BOUNDS: [[number, number], [number, number]] = [
  [-7.0, 108.05],
  [-6.6, 108.35],
];

const TIER_COLOR = { low: "var(--green)", med: "var(--yellow)", high: "var(--red)" };

export default function MapView({ loading }: { loading: boolean }) {
  const {
    week,
    hazard,
    layers,
    overlays,
    boundaries,
    fireSummary,
    landslideSummary,
    flashingIds,
    openPopup,
    mapRef,
  } = useDashboard();
  const wrapRef = useRef<HTMLDivElement>(null);
  const hudRef = useRef<HTMLDivElement>(null);

  const visibleLayers = HAZARD_LAYERS[hazard].filter((key) => {
    const layer = layers[key];
    const ov = overlays[key];
    return layer.visible && ov.status === "ok" && ov.bounds && ov.pngUrl;
  });

  const activeBounds = visibleLayers.map((key) => overlays[key].bounds).find(Boolean) ?? FALLBACK_BOUNDS;

  const handleMouseMove = (ev: React.MouseEvent) => {
    const rect = wrapRef.current!.getBoundingClientRect();
    const fx = (ev.clientX - rect.left) / rect.width;
    const fy = (ev.clientY - rect.top) / rect.height;
    const lat = (-6.7 - fy * 0.3).toFixed(4);
    const lon = (108.05 + fx * 0.3).toFixed(4);
    if (hudRef.current) hudRef.current.textContent = `LAT ${lat}   LON ${lon}`;
  };

  const kecTier = (kecId: string) => {
    if (hazard === "fire") {
      const row = fireSummary?.by_kecamatan.find((r) => r.kecamatan_id === kecId);
      return row ? fireTierClass(row.risk_tier) : "low";
    }
    const row = landslideSummary?.by_kecamatan.find((r) => r.kecamatan_id === kecId);
    return row ? landslideTierClass(row.mean_score_255) : "low";
  };

  const kecStyle = (feature?: Feature<Geometry, { kecamatan_id: string }>): PathOptions => {
    const kecId = feature!.properties.kecamatan_id;
    const flashing = flashingIds.has(kecId);
    return {
      color: TIER_COLOR[kecTier(kecId)],
      weight: flashing ? 4 : 1.5,
      fillOpacity: 0.15,
      opacity: flashing ? 1 : 0.8,
    };
  };

  const onEachKec = (feature: Feature<Geometry, { kecamatan_id: string }>, layer: Layer) => {
    layer.on("click", (ev: LeafletMouseEvent) => {
      const rect = wrapRef.current!.getBoundingClientRect();
      const oe = ev.originalEvent;
      const x = Math.min(oe.clientX - rect.left + 10, rect.width - 220);
      const y = Math.min(oe.clientY - rect.top + 10, rect.height - 160);
      const kecId = feature.properties.kecamatan_id;
      openPopup(
        hazard === "fire"
          ? { kind: "fire", spatialId: kecId, x, y }
          : { kind: "landslideKec", kecamatanId: kecId, x, y },
      );
      const map = mapRef.current;
      if (map) map.fitBounds((layer as LeafletPolygon).getBounds(), { padding: [40, 40] });
    });
  };

  return (
    <div className="map-wrap" ref={wrapRef} onMouseMove={handleMouseMove}>
      <MapContainer
        // react-leaflet v4's MapContainer ref prop is typed non-nullable
        // (RefObject<Map>) even though it's genuinely null before mount --
        // known upstream typing gap, not a runtime concern.
        ref={mapRef as RefObject<LeafletMap>}
        bounds={activeBounds}
        boundsOptions={{ padding: [0, 0] }}
        zoomControl={false}
        dragging={true}
        scrollWheelZoom={true}
        doubleClickZoom={true}
        boxZoom={true}
        touchZoom={true}
        keyboard={true}
        attributionControl={false}
      >
        <TileLayer
          url="https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
          subdomains={["0", "1", "2", "3"]}
        />
        <ZoomControl position="topright" />
        {visibleLayers.map((key) => {
          const overlay = overlays[key];
          return (
            <ImageOverlay
              key={key}
              url={overlay.pngUrl!}
              bounds={overlay.bounds!}
              opacity={layers[key].opacity / 100}
            />
          );
        })}
        {boundaries && (
          <GeoJSON
            key={`${hazard}-${week}`}
            data={boundaries as GeoJSON.FeatureCollection}
            style={kecStyle as (feature?: GeoJSON.Feature) => PathOptions}
            onEachFeature={onEachKec as (feature: GeoJSON.Feature, layer: Layer) => void}
          />
        )}
      </MapContainer>

      <div className="map-title">
        SECTOR <b>MAJALENGKA</b> &nbsp;·&nbsp; WEEK <b>{week}</b>
      </div>
      <div className="compass">
        N
        <br />▲
      </div>

      {loading && (
        <div className="map-loading">
          <span className="spinner-line">LOADING...</span>
        </div>
      )}

      <div className="map-hud" ref={hudRef}>
        LAT -6.8000 &nbsp; LON 108.2000
      </div>
      <div className="map-legend legend">
        <div>
          <span className="swatch" style={{ background: "var(--red)" }} />
          HIGH / EXPECTED+
        </div>
        <div>
          <span className="swatch" style={{ background: "var(--yellow)" }} />
          MEDIUM / MODEST
        </div>
        <div>
          <span className="swatch" style={{ background: "var(--green)" }} />
          LOW / UNLIKELY
        </div>
      </div>
    </div>
  );
}
