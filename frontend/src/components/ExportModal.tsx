import { useState } from "react";
import html2canvas from "html2canvas";
import { useDashboard } from "../screens/dashboard-context";
import { ConnectionError, postReportsPdf } from "../api/client";

export default function ExportModal({ onClose }: { onClose: () => void }) {
  const { week, hazard, mapRef, showToast } = useDashboard();
  const [status, setStatus] = useState<"idle" | "working" | "done" | "error">("idle");
  const [filename, setFilename] = useState("");

  const generate = async () => {
    setStatus("working");
    const filename = `mata-hazard-${week}-${hazard}.pdf`;
    try {
      const canvas = await html2canvas(mapRef.current!.getContainer());
      const mapImageBase64 = canvas.toDataURL("image/png");
      const blob = await postReportsPdf(week, hazard, mapImageBase64);

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);

      setFilename(filename);
      setStatus("done");
      showToast(`Report generated: ${filename}`);
      setTimeout(onClose, 1200);
    } catch (err) {
      setStatus("error");
      showToast(err instanceof ConnectionError ? "Report generation failed: connection error." : "Report generation failed.");
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h3>&gt; EXPORT PDF SUMMARY</h3>
        <div className="row">
          <label>Week</label>
          <div>{week}</div>
        </div>
        <div className="row">
          <label>Hazard Filter</label>
          <div>{hazard.toUpperCase()}</div>
        </div>
        <div className="row">
          <label>Status</label>
          <div>
            {status === "idle" && "Ready to generate."}
            {status === "working" && <span className="spinner-line">COMPILING REPORT...</span>}
            {status === "done" && (
              <>
                <span style={{ color: "var(--accent)" }}>READY:</span> {filename}
              </>
            )}
            {status === "error" && <span style={{ color: "var(--red)" }}>FAILED — try again.</span>}
          </div>
        </div>
        <div className="modal-actions">
          <button className="btn ghost" onClick={onClose} disabled={status === "working"}>
            Cancel
          </button>
          <button className="btn" onClick={generate} disabled={status === "working" || status === "done"}>
            {status === "idle" ? "Generate Report" : status === "working" ? "Working..." : status === "error" ? "Retry" : "Done"}
          </button>
        </div>
      </div>
    </div>
  );
}
