import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Map as LMap } from "leaflet";
import App from "../App";
import { installMockFetch } from "../api/mockFetch";

describe("Command Map screen", () => {
  it("hazard toggle swaps the layer list", async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(await screen.findByText("Fire Risk — Grid")).toBeInTheDocument();
    await user.click(screen.getByText("Landslide"));
    expect(screen.queryByText("Fire Risk — Grid")).not.toBeInTheDocument();
    expect(screen.getByText("Landslide Risk")).toBeInTheDocument();
  });

  it("dragging a layer's opacity slider updates its value", async () => {
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    const slider = document.querySelector('input[type="range"]') as HTMLInputElement;
    expect(slider).toBeTruthy();
    const user = userEvent.setup();
    slider.focus();
    await user.keyboard("{ArrowRight}");
    expect(Number(slider.value)).toBeGreaterThan(80 - 1);
  });

  it("clicking a grid cell opens the inspect popup with real cell detail", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    const row = document.querySelector(".gcl-row") as HTMLElement;
    expect(row).toBeTruthy();
    await user.click(row);
    expect(screen.getByText("CELL DETAIL")).toBeInTheDocument();
    expect(await screen.findByText("Spatial Unit")).toBeInTheDocument();
  });

  it("clicking a landslide grid cell shows its factor breakdown", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    await user.click(screen.getByText("Landslide"));
    const row = document.querySelector(".gcl-row") as HTMLElement;
    expect(row).toBeTruthy();
    await user.click(row);
    expect(screen.getByText("slope")).toBeInTheDocument();
    expect(screen.getByText("rainfall")).toBeInTheDocument();
  });

  it("clicking the landslide alert card switches hazard, flashes matching list rows, and shows a toast", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    const lsCount = Number(
      screen.getByText(/LANDSLIDE · EXPECTED/).closest(".alert-card")!.querySelector(".n")!.textContent,
    );
    expect(lsCount).toBeGreaterThan(0);
    await user.click(screen.getByText(/LANDSLIDE · EXPECTED/).closest(".alert-card")!);
    expect(await screen.findByText(new RegExp(`Zoomed to ${lsCount} landslide alert area\\(s\\)\\.`))).toBeInTheDocument();
    expect(document.querySelectorAll(".gcl-row.flash").length).toBe(lsCount);
  });

  it("alert cards reflect real /alerts counts", async () => {
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    const fireCount = screen.getByText(/FIRE · HIGH RISK CELLS/).closest(".alert-card")!.querySelector(".n")!.textContent;
    expect(fireCount).toBe("1");
  });

  it("switching weeks re-fetches data for the new week", async () => {
    const fetchMock = installMockFetch();
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    fetchMock.mockClear();
    await user.selectOptions(screen.getByRole("combobox"), "2026-W31");
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([u]) => String(u).includes("week=2026-W31"))).toBe(true),
    );
  });

  it("selecting a week with no data navigates to the empty-week screen", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    await user.selectOptions(screen.getByRole("combobox"), "2026-W99");
    expect(await screen.findByText(/NO DATA INGESTED — 2026-W99/)).toBeInTheDocument();
    await user.click(screen.getByText("← Back to Command Map"));
    expect(await screen.findByText("Export PDF Summary")).toBeInTheDocument();
  });

  it("a week that's in /weeks but whose summary comes back empty also navigates to the empty-week screen", async () => {
    installMockFetch("empty");
    render(<App />);
    expect(await screen.findByText(/NO DATA INGESTED — 2026-W34/)).toBeInTheDocument();
  });

  it("a real fetch failure shows the Connection Error screen, and retry recovers", async () => {
    installMockFetch("down");
    render(<App />);
    expect(await screen.findByText(/CONNECTION LOST/)).toBeInTheDocument();
    installMockFetch("ok");
    const user = userEvent.setup();
    await user.click(screen.getByText("Retry Connection"));
    expect(await screen.findByText("Export PDF Summary")).toBeInTheDocument();
  });

  it("map interaction props (pan/zoom) are enabled, not the old static false", async () => {
    // "initialize" is Leaflet's real constructor hook (leaflet-src.js) that every
    // L.Map instance runs through -- not in @types/leaflet's public surface, hence the cast.
    const initSpy = vi.spyOn(LMap.prototype as any, "initialize");
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    expect(initSpy).toHaveBeenCalled();
    const options = initSpy.mock.calls[0][1] as Record<string, unknown>;
    for (const key of ["dragging", "scrollWheelZoom", "doubleClickZoom", "boxZoom", "touchZoom", "keyboard"]) {
      expect(options[key]).toBe(true);
    }
    initSpy.mockRestore();
  });

  it("clicking a kecamatan polygon fits the map to its bounds and still opens the inspect popup", async () => {
    const fitBoundsSpy = vi.spyOn(LMap.prototype, "fitBounds");
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Fire Risk — Grid");
    const path = await waitFor(() => {
      const el = document.querySelector(".leaflet-overlay-pane path");
      if (!el) throw new Error("no kecamatan polygon rendered yet");
      return el as SVGPathElement;
    });
    await user.click(path);
    expect(fitBoundsSpy).toHaveBeenCalled();
    expect(await screen.findByText("Spatial Unit")).toBeInTheDocument();
    fitBoundsSpy.mockRestore();
  });
});
