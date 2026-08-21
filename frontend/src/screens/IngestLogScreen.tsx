import { useEffect, useState } from "react";
import { getIngestStatus, ConnectionError } from "../api/client";
import { FILE_TYPE_INFO } from "../mocks/ingest";
import { WEEKS } from "../mocks/weeks";
import type { IngestStatusRow, Week } from "../types";

const STATUS_META: Record<string, { label: string; cls: string }> = {
  ok: { label: "OK", cls: "status-ok" },
  mock_placeholder: { label: "MOCK PLACEHOLDER", cls: "status-mock" },
  missing: { label: "MISSING", cls: "status-missing" },
  error: { label: "ERROR", cls: "status-error" },
};

export default function IngestLogScreen({
  week,
  onSelectWeek,
  onConnectionError,
}: {
  week: Week;
  onSelectWeek: (week: Week) => void;
  onConnectionError: (trace: string) => void;
}) {
  const [rows, setRows] = useState<IngestStatusRow[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    setRows(null);
    getIngestStatus(week)
      .then((r) => !cancelled && setRows(r))
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ConnectionError) onConnectionError(`${err.method} ${err.url} → connection failed`);
        else throw err;
      });
    return () => {
      cancelled = true;
    };
  }, [week, onConnectionError]);

  const byFileType = new Map(rows?.map((r) => [r.file_type, r]));

  return (
    <section id="ingest-status">
      <div className="wrap">
        <h2>&gt; INGEST LOG — OPERATOR VIEW</h2>
        <div className="section-label" style={{ marginTop: 16 }}>
          Week
        </div>
        <select
          className="week-select"
          style={{ width: "auto" }}
          value={week}
          onChange={(e) => onSelectWeek(e.target.value as Week)}
        >
          {WEEKS.map((w) => (
            <option key={w.value} value={w.value}>
              {w.value}
            </option>
          ))}
        </select>
        {rows === null ? (
          <p className="spinner-line" style={{ marginTop: 16 }}>
            LOADING...
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>File Type</th>
                <th>Status</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {FILE_TYPE_INFO.filter(([fileType]) => byFileType.has(fileType)).map(([fileType, description]) => {
                const row = byFileType.get(fileType)!;
                return (
                  <tr key={fileType}>
                    <td>
                      {fileType}
                      <br />
                      <span style={{ color: "var(--text-dim)", fontSize: 10 }}>{description}</span>
                    </td>
                    <td className={STATUS_META[row.status]?.cls ?? "status-missing"}>
                      <span className="chip">{STATUS_META[row.status]?.label ?? row.status.toUpperCase()}</span>
                    </td>
                    <td style={{ color: "var(--text-dim)" }}>{row.detail}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
