import { useEffect, useState } from "react";
import type { Screen } from "../App";

function tick(): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Jakarta",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(new Date());
  const get = (type: string) => parts.find((p) => p.type === type)!.value;
  return `${get("year")}-${get("month")}-${get("day")} ${get("hour")}:${get("minute")}:${get("second")} WIB`;
}

export default function Header({
  screen,
  onNavigate,
}: {
  screen: Screen;
  onNavigate: (screen: Screen) => void;
}) {
  const [clock, setClock] = useState(tick);

  useEffect(() => {
    const id = setInterval(() => setClock(tick()), 1000);
    return () => clearInterval(id);
  }, []);

  const offline = screen === "error-state";

  return (
    <header>
      <div className="brand">
        <span className="dot" />
        MATA HAZARD COMMAND <small>// MAJALENGKA SECTOR</small>
      </div>
      <nav className="tabs">
        <button className={screen === "dashboard" ? "active" : ""} onClick={() => onNavigate("dashboard")}>
          Command Map
        </button>
        <button className={screen === "ingest-status" ? "active" : ""} onClick={() => onNavigate("ingest-status")}>
          Ingest Log
        </button>
      </nav>
      <div className="status-block">
        <span id="clock">{clock}</span>
        <span
          className={"link-pill" + (offline ? " offline" : "")}
          title="click to simulate link status"
          onClick={() => onNavigate("error-state")}
        >
          <span className="led" />
          <span>{offline ? "LINK OFFLINE" : "LINK OK"}</span>
        </span>
      </div>
    </header>
  );
}
