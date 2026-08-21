import { useState } from "react";
import { useDashboard } from "../screens/dashboard-context";
import ExportModal from "./ExportModal";

export default function AlertPanel() {
  const { week, alerts, flashAlerts } = useDashboard();
  const [exportOpen, setExportOpen] = useState(false);

  return (
    <>
      <div className="section-label">Alert Summary — {week}</div>
      <div className="alert-card fire" onClick={() => flashAlerts("fire")}>
        <div className="n">{alerts.fire}</div>
        <div className="lbl">FIRE · HIGH RISK CELLS</div>
      </div>
      <div className="alert-card landslide" onClick={() => flashAlerts("landslide")}>
        <div className="n">{alerts.landslide}</div>
        <div className="lbl">LANDSLIDE · EXPECTED / ACTIVE</div>
      </div>
      <div className="alert-card combined" onClick={() => flashAlerts("combined")}>
        <div className="n">{alerts.combined}</div>
        <div className="lbl">COMBINED · BOTH HIGH</div>
      </div>
      <div className="section-label">Report</div>
      <button className="btn" onClick={() => setExportOpen(true)}>
        Export PDF Summary
      </button>
      {exportOpen && <ExportModal onClose={() => setExportOpen(false)} />}
    </>
  );
}
