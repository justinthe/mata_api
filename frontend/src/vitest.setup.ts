import "@testing-library/jest-dom/vitest";
import { beforeEach } from "vitest";
import { installMockFetch } from "./api/mockFetch";

// jsdom has no SVG geometry engine -- Leaflet feature-detects SVG support via
// `svgEl.createSVGRect`, and without it every vector layer (react-leaflet's
// <GeoJSON>) crashes on mount. This is the standard minimal shim for
// Leaflet-under-jsdom; a real browser always has this method.
if (typeof SVGElement !== "undefined" && !("createSVGRect" in SVGElement.prototype)) {
  (SVGElement.prototype as unknown as { createSVGRect: () => DOMRect }).createSVGRect = () =>
    ({ x: 0, y: 0, width: 0, height: 0 }) as DOMRect;
}

beforeEach(() => {
  installMockFetch();
});
