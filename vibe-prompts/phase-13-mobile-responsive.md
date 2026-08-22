# Phase 13 — Mobile Responsive Layout · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session ports the mockup's new phone breakpoint into the real
frontend. `mockup.html`/`storyboard.md` were revised (2026-08-22, see
`vibe-pipeline-state.md`) to add a `@media (max-width:480px)` layout —
the live app's `frontend/src/theme.css` mirrors the mockup's structure
1:1 (same class names, same existing `@media (max-width:900px)` block at
`theme.css:177`) but has no phone-width breakpoint yet, so on an actual
phone (~375-430px) the dashboard is a cramped single column: filters,
then a 60vh map, then the alert sidebar, all full-height stacked blocks
the operator has to scroll through before ever seeing an alert count —
and the Ingest Log's 3-column table (`theme.css:151`) squeezes to
illegible widths.

Reference: PRD.md (mobile/responsive requirement), storyboard.md's
"Mobile (≤480px)" subsection on each of the 4 screens (embeds the target
screenshots at `images/mobile/*.png`), architecture.md §4 (frontend
layout).

## Scope Boundary
- In scope: `frontend/src/theme.css` (new `@media (max-width:480px)`
  block + the modal-width clamp), `frontend/src/screens/
  IngestLogScreen.tsx` (wrap `<table>` in a scroll container).
- Out of scope — do NOT touch: the existing `@media (max-width:900px)`
  tablet block (leave as-is, it already stacks the 3-column grid to
  1-column — the phone block only adds finer-grained rules on top of
  it); any component logic/state/props; the backend; Phase 10's map
  interaction props; Phase 11/12 content.

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. Frontend-only change — no container/env
  impact.
- **Graphify (required, start AND end of this phase):**
  - At the start, run `graphify` to map `theme.css`'s existing responsive
    rules and every component that renders inside `#dashboard .layout`
    (`Header`, `LayerControls`, `MapView`, `AlertPanel`, `IngestLogScreen`)
    before writing any code.
  - Use the graph to find hidden dependencies this phase could break —
    in particular any inline style or JS measurement (e.g. map resize
    logic) that assumes the existing DOM order or fixed heights.
  - At the end, run `graphify` again to verify the resulting "after"
    state matches the intended design — if the graph looks like
    spaghetti, the solution is not elegant; simplify before closing.
- **Recall (required, throughout):** Use `recall` to cross-reference
  prior state and context — CLAUDE.md, tasks/todo.md, tasks/lessons.md,
  and Phase 02/07/10's map/layout code and tests — before and during
  implementation, so this phase does not regress or contradict work
  already approved.
- **TDD:** Write automated tests alongside or prior to the implementation.
  All tests from previous phases must still pass.
- **Ponytail (required, level: ultra):** Verify the ponytail plugin is
  active at this level before writing code (`/ponytail` reports the
  current level; set it with `/ponytail ultra` if needed). Apply its
  ladder to every change: does this need to exist → reuse what's in the
  codebase → stdlib → native platform feature → installed dependency →
  one line → only then the minimum that works. Never cut validation,
  error handling, security, or accessibility in its name. In particular:
  this is CSS media-query rules plus one JSX wrapper `<div>` — do not
  introduce a CSS-in-JS library, a breakpoint hook, or any new
  dependency for it; port the mockup's already-approved CSS values
  rather than inventing new ones.
- **Multi-Agent Execution (required):**
  1. Scout first: spawn a subagent to run graphify + recall on the
     modules this phase touches and report back the dependency map plus
     relevant prior context, before any implementation starts.
  2. Parallelize research: independent exploration/analysis tasks each
     go to their own subagent — one task per subagent — fed the scout's
     graphify output.
  3. Implement in the main thread: a single writer avoids file conflicts
     between agents.
  4. Review before close: a separate reviewer subagent independently
     verifies the phase — tests pass, the storyboard contract is met —
     before the phase is marked done.
- **State Management:** Before finishing, update CLAUDE.md: build
  commands, test commands, and current development state.
- **Tooling Protocol:** Primary runner is Claude Code — enter plan mode
  before implementing, per CLAUDE.md. For portability, when running
  outside Claude Code, load and execute this prompt via Caveman.

## Visual Reference (UI track, phases that build UI)
Must match storyboard.md's "Mobile (≤480px)" subsection on each screen
and the corresponding `images/mobile/screen-NN-*-mobile.png`:
- Screen 1: at ≤480px the dashboard column order becomes map (42vh) →
  right sidebar (alert cards + Export/System buttons) → left sidebar
  (Week/Hazard/Layers) — all 3 alert cards visible without scrolling
  past the map. Header subtitle (`<small>` in `Header.tsx`) and the
  `.status-block` (clock/link pill) hidden; nav tab padding/font shrink
  further than the existing 900px values.
- Screen 2: the `<table>` scrolls horizontally inside a `min-width:480px`
  wrapper instead of columns shrinking illegibly.
- Screens 3/4: `.empty-body`/`.error-body` get side padding so text
  doesn't touch the viewport edge; their `p`/`.trace` width-cap so long
  lines wrap instead of overflowing.
Desktop (`images/screen-01..04*.png`) and tablet (900px) are unchanged —
verify nothing in this phase alters `theme.css:177-184`'s existing block.

## Deliverables
- `frontend/src/theme.css`:
  - New `@media (max-width:480px)` block (after the existing 900px
    block) porting the values from `mockup.html`'s equivalent block:
    header/brand/nav shrink + subtitle hidden; `#dashboard .layout`
    switched to `display:flex; flex-direction:column` with `order` on
    `.map-wrap` (1), `aside.right` (2), `aside:not(.right)` (3), map
    height `42vh`; smaller `.section-label`/`.alert-card`/`.map-title`/
    `.map-hud`/`.compass`/`.map-legend` sizing; `.popup-card` width
    clamped via `min(210px, calc(100vw - 40px))`; `#ingest-status .wrap`
    padding reduced; `.empty-body`/`.error-body` side padding +
    `.empty-body p`/`.error-body .trace` max-width clamp.
  - `.table-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;
    margin-top:14px;}` and `table{min-width:480px;margin-top:0;}` (mirrors
    `mockup.html`'s change — table no longer sets its own `margin-top`,
    the wrapper does).
  - `.modal{width:340px;max-width:calc(100vw - 32px);...}` — clamp added
    to the existing rule, not a new selector.
- `frontend/src/screens/IngestLogScreen.tsx`: wrap the existing `<table>`
  (currently a direct child of the `.wrap` div, per `IngestLogScreen.tsx`
  around line 66) in `<div className="table-scroll">...</div>`. No other
  JSX/logic change — `id="ingestTableBody"`-equivalent state/handlers
  untouched.
- Tests: a rendered-width assertion (jsdom viewport can't truly emulate
  a media query, so assert structurally) — `IngestLogScreen` renders its
  `<table>` inside an element with `className="table-scroll"`; a CSS
  regression check that the new `@media (max-width:480px)` block exists
  in `theme.css` and contains the `#dashboard .layout{order` reorder
  rules (simple string/regex assertion against the stylesheet source,
  same spirit as any existing CSS-presence test in this repo — check
  first via `recall`/graphify whether one already exists to extend
  rather than duplicate).
- `scripts/run-phase-13.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-13.sh`, executable, no arguments. It must:
- Start the shared postgres (`mata_api_algo-postgres-1`) if down, same
  check as every prior `run-phase-NN.sh`.
- Apply `migrations/0001_initial_schema.sql`.
- `docker compose up -d --build`, wait until `api` reports healthy.
- Run `ingest.py` for `data/2026_w34`, `_w31`, `_w30` only if
  `ingest_log` is empty (skip if already ingested — same pattern as
  `run-phase-10.sh`).
- Print the frontend URL and a short manual checklist: open browser
  devtools responsive mode at ~390×844 (iPhone-class) and confirm — (1)
  Command Map shows the map, then all 3 alert cards, then the filters,
  in that scroll order; (2) header fits on one line with no horizontal
  scrollbar; (3) Ingest Log's table scrolls horizontally without
  crushing its columns; (4) Empty Week / Error State (via the "Simulate
  Connection Loss" button) text doesn't touch the screen edges; (5)
  resize back up through 900px and full desktop width and confirm the
  existing tablet/desktop layouts are unchanged.
It only starts the stack (with real data loaded) and tells the user what
to click — it does NOT assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-13.sh`, follow the printed
     checklist at a 390×844 viewport, then confirm desktop/tablet are
     unaffected.
   - Automated: `cd frontend && npm test` and `npm run typecheck`.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
