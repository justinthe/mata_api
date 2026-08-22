import { readFileSync } from "node:fs";
import { expect, it } from "vitest";

const css = readFileSync(`${__dirname}/theme.css`, "utf-8");

it("theme.css defines a 480px phone breakpoint that reorders map, right sidebar, left sidebar", () => {
  const block = css.split("@media (max-width: 480px)")[1];
  expect(block).toBeDefined();
  expect(block).toMatch(/\.map-wrap\s*\{[^}]*order:\s*1/);
  expect(block).toMatch(/aside\.right\s*\{[^}]*order:\s*2/);
  expect(block).toMatch(/aside:not\(\.right\)\s*\{[^}]*order:\s*3/);
});
