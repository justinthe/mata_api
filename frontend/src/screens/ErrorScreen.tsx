export default function ErrorScreen({ trace, onRetry }: { trace: string; onRetry: () => void }) {
  return (
    <section id="error-state">
      <div className="error-body">
        <div className="glyph">⨯</div>
        <h2>CONNECTION LOST — UNABLE TO REACH MATA API</h2>
        <div className="trace">{trace || "connection failed"}</div>
        <button className="btn" onClick={onRetry}>
          Retry Connection
        </button>
      </div>
    </section>
  );
}
