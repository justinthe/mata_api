// @types/node isn't a dependency here — this repo's tests otherwise never
// touch Node builtins. Minimal ambient types for the two calls
// theme.css.test.ts needs to read the stylesheet source directly (Vite's
// `?raw` CSS import isn't honored by this project's Vite version).
declare module "node:fs" {
  export function readFileSync(path: string, encoding: string): string;
}
declare const __dirname: string;
