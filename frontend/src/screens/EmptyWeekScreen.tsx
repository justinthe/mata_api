import type { Week } from "../types";

export default function EmptyWeekScreen({ week, onBack }: { week: Week; onBack: () => void }) {
  return (
    <section id="empty-week">
      <div className="empty-body">
        <div className="glyph">▢</div>
        <h2>NO DATA INGESTED — {week}</h2>
        <p>
          No fire or landslide files were found under <code>data/{week.toLowerCase().replace("-", "_")}/</code>. Run the
          ingest script for this week, or select a different week from Command Map.
        </p>
        <button className="btn ghost" style={{ width: "auto", padding: "9px 22px" }} onClick={onBack}>
          ← Back to Command Map
        </button>
      </div>
    </section>
  );
}
