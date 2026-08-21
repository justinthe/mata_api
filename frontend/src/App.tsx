import { useCallback, useEffect, useState } from "react";
import Header from "./components/Header";
import Toast from "./components/Toast";
import CommandMapScreen from "./screens/CommandMapScreen";
import IngestLogScreen from "./screens/IngestLogScreen";
import EmptyWeekScreen from "./screens/EmptyWeekScreen";
import ErrorScreen from "./screens/ErrorScreen";
import { getWeeks, ConnectionError } from "./api/client";
import type { Week } from "./types";

export type Screen = "dashboard" | "ingest-status" | "empty-week" | "error-state";

const SCREENS: Screen[] = ["dashboard", "ingest-status", "empty-week", "error-state"];

// Manual QA aid (phase-07 run script's checklist relies on it) -- no real
// week is ever named "2026-W99", so it's always a safe "no data" trigger.
const NO_DATA_WEEK = "2026-W99";

function screenFromHash(): Screen {
  const h = window.location.hash.replace("#", "") as Screen;
  return SCREENS.includes(h) ? h : "dashboard";
}

export default function App() {
  const [screen, setScreenState] = useState<Screen>(screenFromHash);
  const [weeks, setWeeks] = useState<Week[] | null>(null);
  const [week, setWeekState] = useState<Week | null>(null);
  const [lastValidWeek, setLastValidWeek] = useState<Week | null>(null);
  const [toast, setToastState] = useState<string | null>(null);
  const [errorTrace, setErrorTrace] = useState("");
  const [loadKey, setLoadKey] = useState(0);

  const navigate = useCallback((next: Screen) => {
    setScreenState(next);
    window.location.hash = next;
  }, []);

  useEffect(() => {
    const onHashChange = () => setScreenState(screenFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    let cancelled = false;
    getWeeks()
      .then((list) => {
        if (cancelled) return;
        setWeeks(list);
        setWeekState((prev) => prev ?? list[0]);
        setLastValidWeek((prev) => prev ?? list[0]);
      })
      .catch((err) => {
        if (cancelled || !(err instanceof ConnectionError)) return;
        setErrorTrace(`GET /weeks → connection failed`);
        navigate("error-state");
      });
    return () => {
      cancelled = true;
    };
  }, [loadKey, navigate]);

  const showToast = useCallback((msg: string) => {
    setToastState(msg);
    setTimeout(() => setToastState(null), 3000);
  }, []);

  const selectWeek = useCallback(
    (wk: Week) => {
      setWeekState(wk);
      if (weeks?.includes(wk)) {
        setLastValidWeek(wk);
        navigate("dashboard");
      } else {
        navigate("empty-week");
      }
    },
    [navigate, weeks],
  );

  const onConnectionError = useCallback(
    (trace: string) => {
      setErrorTrace(trace);
      navigate("error-state");
    },
    [navigate],
  );

  const onEmptyWeek = useCallback(() => navigate("empty-week"), [navigate]);

  const retry = useCallback(() => {
    showToast("Connection restored.");
    setLoadKey((k) => k + 1);
    navigate("dashboard");
  }, [navigate, showToast]);

  const weekOptions = weeks ? [...weeks, NO_DATA_WEEK] : [];

  return (
    <>
      <Header screen={screen} onNavigate={navigate} />
      {screen === "dashboard" && week && (
        <CommandMapScreen
          week={week}
          weekOptions={weekOptions}
          onSelectWeek={selectWeek}
          showToast={showToast}
          onConnectionError={onConnectionError}
          onEmptyWeek={onEmptyWeek}
        />
      )}
      {screen === "dashboard" && !week && (
        <div style={{ height: "calc(100vh - 52px)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span className="spinner-line">LOADING...</span>
        </div>
      )}
      {screen === "ingest-status" && week && (
        <IngestLogScreen week={week} onSelectWeek={setWeekState} onConnectionError={onConnectionError} />
      )}
      {screen === "empty-week" && <EmptyWeekScreen week={week ?? NO_DATA_WEEK} onBack={() => selectWeek(lastValidWeek ?? NO_DATA_WEEK)} />}
      {screen === "error-state" && <ErrorScreen trace={errorTrace} onRetry={retry} />}
      <Toast message={toast} />
    </>
  );
}
