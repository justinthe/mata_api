import { HAZARD_LAYERS } from "../types";
import { useDashboard } from "../screens/dashboard-context";

export default function LayerControls() {
  const { hazard, setHazard, layers, toggleLayer, setLayerOpacity } = useDashboard();

  return (
    <>
      <div className="section-label">Hazard Filter</div>
      <div className="seg">
        <button className={hazard === "fire" ? "active" : ""} onClick={() => setHazard("fire")}>
          Fire
        </button>
        <button className={hazard === "landslide" ? "active" : ""} onClick={() => setHazard("landslide")}>
          Landslide
        </button>
      </div>

      <div className="section-label">Layers</div>
      <div>
        {HAZARD_LAYERS[hazard].map((key) => {
          const layer = layers[key];
          const disabled = layer.status !== "ok";
          return (
            <div className={"layer-row" + (disabled ? " disabled" : "")} key={key}>
              <div className="layer-head">
                <label>
                  <input
                    type="checkbox"
                    checked={layer.visible}
                    disabled={disabled}
                    onChange={() => toggleLayer(key)}
                  />
                  <span className="swatch" style={{ background: layer.color }} />
                  {layer.label}
                </label>
              </div>
              {disabled ? (
                <div style={{ fontSize: 9, color: "var(--text-dim)", marginTop: 6 }}>
                  no raster ingested for this week
                </div>
              ) : (
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={layer.opacity}
                  onChange={(e) => setLayerOpacity(key, Number(e.target.value))}
                />
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}
