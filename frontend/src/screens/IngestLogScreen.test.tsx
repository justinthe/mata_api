import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import App from "../App";
import { installMockFetch } from "../api/mockFetch";

async function openIngestLog(user: ReturnType<typeof userEvent.setup>) {
  render(<App />);
  await user.click(await screen.findByText("Ingest Log"));
  await screen.findByText(/INGEST LOG — OPERATOR VIEW/);
}

describe("Ingest Log screen", () => {
  it("shows W34's real statuses", async () => {
    const user = userEvent.setup();
    await openIngestLog(user);
    expect(await screen.findByText("MOCK PLACEHOLDER")).toBeInTheDocument();
    expect(screen.getByText("MISSING")).toBeInTheDocument();
    expect(screen.getAllByText("OK").length).toBeGreaterThan(0);
  });

  it("switching weeks re-fetches ingest status for the new week", async () => {
    const fetchMock = installMockFetch();
    const user = userEvent.setup();
    await openIngestLog(user);
    await screen.findByText("MOCK PLACEHOLDER");
    fetchMock.mockClear();
    await user.selectOptions(screen.getByRole("combobox"), "2026-W31");
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([u]) => String(u).includes("/ingest-status") && String(u).includes("week=2026-W31"))).toBe(
        true,
      ),
    );
  });

  it("a real fetch failure shows Connection Error, and retry recovers", async () => {
    const user = userEvent.setup();
    await openIngestLog(user);
    await screen.findByText("MOCK PLACEHOLDER");
    installMockFetch("down");
    await user.selectOptions(screen.getByRole("combobox"), "2026-W31");
    expect(await screen.findByText(/CONNECTION LOST/)).toBeInTheDocument();
    installMockFetch("ok");
    await user.click(screen.getByText("Retry Connection"));
    expect(await screen.findByText("Export PDF Summary")).toBeInTheDocument();
  });
});
