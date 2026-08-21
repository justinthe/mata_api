import { useEffect, useState } from "react";
import * as api from "../api/client";
import type { FireCellDetail } from "../types";
import { useDashboard } from "../screens/dashboard-context";

export default function InspectPopup() {
  const { popup, week, landslideGrid, landslideSummary, closePopup } = useDashboard();
  const [fireCell, setFireCell] = useState<FireCellDetail | null>(null);
  const [fireError, setFireError] = useState<string | null>(null);

  useEffect(() => {
    if (!popup || popup.kind !== "fire") return;
    let cancelled = false;
    setFireCell(null);
    setFireError(null);
    api
      .getFireCell(popup.spatialId, week)
      .then((cell) => !cancelled && setFireCell(cell))
      .catch(() => !cancelled && setFireError("Could not load cell detail."));
    return () => {
      cancelled = true;
    };
  }, [popup, week]);

  if (!popup) return null;

  return (
    <div className="popup-card" style={{ left: popup.x, top: popup.y }}>
      <div className="pc-head">
        <b>CELL DETAIL</b>
        <span className="pc-close" onClick={closePopup}>
          ✕
        </span>
      </div>
      {popup.kind === "fire" && (
        <>
          {fireError && <div className="pc-row">{fireError}</div>}
          {!fireError && !fireCell && <div className="pc-row">Loading…</div>}
          {fireCell && (
            <>
              <div className="pc-row">
                <span>Spatial Unit</span>
                <span>{fireCell.spatial_unit_id}</span>
              </div>
              <div className="pc-row">
                <span>Risk Tier</span>
                <span className={"tier-pill " + fireCell.risk_tier.toLowerCase()}>{fireCell.risk_tier}</span>
              </div>
              <div className="pc-row">
                <span>Predicted Count</span>
                <span>{fireCell.predicted_next_week_count ?? "—"}</span>
              </div>
              <div className="pc-row">
                <span>Hotspot Count</span>
                <span>{fireCell.hotspot_count ?? "—"}</span>
              </div>
              <div className="pc-row">
                <span>Hotspot Density</span>
                <span>{fireCell.hotspot_density ?? "—"}</span>
              </div>
              <div className="pc-row">
                <span>Max FRP</span>
                <span>{fireCell.max_frp ?? "—"} MW</span>
              </div>
            </>
          )}
        </>
      )}
      {popup.kind === "landslideGrid" &&
        (() => {
          const cell = landslideGrid.find((c) => c.grid_id === popup.gridId);
          if (!cell) return <div className="pc-row">Cell not found.</div>;
          return (
            <>
              <div className="pc-row">
                <span>Grid ID</span>
                <span>{cell.grid_id}</span>
              </div>
              <div className="pc-row">
                <span>Category</span>
                <span>{cell.risk_category}</span>
              </div>
              <div className="pc-row">
                <span>Score (0-255)</span>
                <span>{cell.score_255}</span>
              </div>
              <div className="pc-row">
                <span>Slope</span>
                <span>{cell.slope_degrees ?? "—"}°</span>
              </div>
              <div className="pc-row">
                <span>7d Rainfall</span>
                <span>{cell.cumulative_rainfall_mm ?? "—"} mm</span>
              </div>
              {Object.entries(cell.factor_breakdown ?? {}).map(([factor, score]) => (
                <div className="pc-row" key={factor}>
                  <span>{factor}</span>
                  <span>{score}</span>
                </div>
              ))}
            </>
          );
        })()}
      {popup.kind === "landslideKec" &&
        (() => {
          const kec = landslideSummary?.by_kecamatan.find((k) => k.kecamatan_id === popup.kecamatanId);
          if (!kec) return <div className="pc-row">Kecamatan not found.</div>;
          return (
            <>
              <div className="pc-row">
                <span>Kecamatan</span>
                <span>{kec.kecamatan_name ?? kec.kecamatan_id}</span>
              </div>
              <div className="pc-row">
                <span>Category</span>
                <span>{kec.highest_category}</span>
              </div>
              <div className="pc-row">
                <span>Mean Score (0-255)</span>
                <span>{kec.mean_score_255}</span>
              </div>
            </>
          );
        })()}
    </div>
  );
}
