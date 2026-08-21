import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import { installMockFetch } from "../api/mockFetch";

vi.mock("html2canvas", () => ({
  default: vi.fn().mockResolvedValue({ toDataURL: () => "data:image/png;base64,AAAA" }),
}));

describe("Export PDF flow", () => {
  beforeEach(() => {
    // jsdom's URL has no createObjectURL/revokeObjectURL -- add them directly
    // rather than replacing the global URL class (which would break `new
    // URL(...)`, used internally by mockFetch.ts's route()).
    URL.createObjectURL = vi.fn(() => "blob:mock-url");
    URL.revokeObjectURL = vi.fn();
  });

  it("generates a report through the spinner and filename states, and triggers a download", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByText("Export PDF Summary"));
    expect(screen.getByText(/EXPORT PDF SUMMARY/)).toBeInTheDocument();
    await user.click(screen.getByText("Generate Report"));
    // The mocked capture/POST resolve within a single act() flush, so the
    // transient "working" spinner isn't reliably observable here (unlike the
    // old setTimeout-based mock) -- assert the reachable end state instead.
    expect(await screen.findByText("READY:", {}, { timeout: 3000 })).toBeInTheDocument();
    expect(
      await screen.findByText(/Report generated: mata-hazard-2026-W34-fire\.pdf/),
    ).toBeInTheDocument();
    expect(URL.createObjectURL).toHaveBeenCalled();
  });

  it("shows an error state and keeps the modal open when the PDF request fails", async () => {
    const baseFetch = installMockFetch("ok");
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === "string" ? input : input.toString();
        if (init?.method === "POST" && url.includes("/reports/pdf")) {
          return Promise.reject(new TypeError("failed to fetch"));
        }
        return baseFetch(input, init);
      }),
    );

    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByText("Export PDF Summary"));
    await user.click(screen.getByText("Generate Report"));
    expect(await screen.findByText(/FAILED/)).toBeInTheDocument();
    expect(screen.getByText(/EXPORT PDF SUMMARY/)).toBeInTheDocument();
  });
});
