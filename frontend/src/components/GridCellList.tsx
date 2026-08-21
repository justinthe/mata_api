import { fireTierClass, landslideTierClass } from "../types";
import { useDashboard } from "../screens/dashboard-context";

// Grid-tier cells (fire's ~1450/week, landslide's 50) have no real
// coordinates in any backend route -- kecamatan polygons on the map are the
// only geo-accurate clickable layer (see CLAUDE.md Phase 07 notes). This
// list is the real click-to-inspect path for grid-tier detail.
const FIRE_TIER_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 };

export default function GridCellList() {
  const { hazard, fireGrid, landslideGrid, flashingIds, openPopup } = useDashboard();

  const rows =
    hazard === "fire"
      ? [...fireGrid]
          .sort((a, b) => FIRE_TIER_ORDER[a.risk_tier] - FIRE_TIER_ORDER[b.risk_tier])
          .map((r) => ({ id: r.grid_id, label: r.grid_id, tier: fireTierClass(r.risk_tier) }))
      : [...landslideGrid]
          .sort((a, b) => b.score_255 - a.score_255)
          .map((r) => ({ id: r.grid_id, label: `${r.grid_id} · ${r.score_255}`, tier: landslideTierClass(r.score_255) }));

  const handleClick = (id: string) => {
    openPopup(
      hazard === "fire"
        ? { kind: "fire", spatialId: id, x: 240, y: 60 }
        : { kind: "landslideGrid", gridId: id, x: 240, y: 60 },
    );
  };

  return (
    <>
      <div className="section-label">Grid Cells</div>
      <div className="gcl-list">
        {rows.map((row) => (
          <button
            key={row.id}
            className={"gcl-row" + (flashingIds.has(row.id) ? " flash" : "")}
            onClick={() => handleClick(row.id)}
          >
            <span>{row.label}</span>
            <span className={"tier-pill " + row.tier}>{row.tier.toUpperCase()}</span>
          </button>
        ))}
      </div>
    </>
  );
}
