# Phase 10 — Map Navigation · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session adds real map navigation to the Command Map screen
(`frontend/src/components/MapView.tsx`), which is currently fully static
(`dragging={false}`, `scrollWheelZoom={false}`, `zoomControl={false}`,
`doubleClickZoom={false}`, `boxZoom={false}`, `touchZoom={false}`,
`keyboard={false}`) — a gap against PRD.md §"Performance" ("map
interactions (pan/zoom/opacity) stay client-side") and PRD.md §User Flow 6
(clicking an alert/area "zooms/pans the map"), and nothing else:
1. **Zoom in/out** — mouse scroll wheel, `+`/`-` on a visible zoom
   control, and double-click-to-zoom.
2. **Pan** — click-drag to move the map.
3. **Click-to-zoom on a kecamatan polygon** — clicking a kecamatan
   boundary (the map's only real geo-accurate clickable layer, per the
   Phase 07 CLAUDE.md note — grid-tier cells have no coordinates in any
   backend route) both opens the existing inspect popup (unchanged
   behavior) AND smooth-zooms/pans the map to fit that polygon's bounds.

Reference: PRD.md §"Performance" note, §User Flow 6, architecture.md §4
(map component), storyboard.md Screen 1 (Command Map).

## Scope Boundary
- In scope: `MapView.tsx`'s `MapContainer` interaction props, a visible
  zoom control, and the existing `onEachKec` click handler extended to
  also call `map.fitBounds(...)` on the clicked layer.
- Out of scope — do NOT touch: the Alert Summary panel's own
  "zoom-to-alert-area" behavior (it currently only flashes matching
  cells — see Phase 07 CLAUDE.md note — leave that as-is, do not wire it
  to the new zoom capability); GridCellList (still has no coordinates,
  still cannot zoom the map); any backend route; overlay bounds-fitting
  logic (`activeBounds`, unchanged — it still sets the *initial* view on
  week/hazard/overlay change, real user zoom/pan on top of that is what
  this phase adds); Phase 11 (observability) and Phase 12 (security
  audit) content.

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. Frontend-only change — no container/env
  impact.
- **Graphify (required, start AND end of this phase):**
  - At the start, run `graphify` to map the existing architecture of the
    module(s) this phase touches plus the proposed changes, before writing
    any code.
  - Use the graph to find hidden dependencies that this phase could break.
  - At the end, run `graphify` again to verify the resulting "after" state
    matches the intended design — if the graph looks like spaghetti, the
    solution is not elegant; simplify before closing the phase.
- **Recall (required, throughout):** Use `recall` to cross-reference prior
  state and context — CLAUDE.md, tasks/todo.md, tasks/lessons.md, and
  earlier phases' code and tests — before and during implementation, so
  this phase does not regress or contradict work already approved.
- **TDD:** Write automated tests alongside or prior to the implementation.
  All tests from previous phases must still pass.
- **Ponytail (required, level: ultra):** Verify the ponytail plugin is
  active at this level before writing code (`/ponytail` reports the
  current level; set it with `/ponytail ultra` if needed). Apply its
  ladder to every change: does this need to exist → reuse what's in the
  codebase → stdlib → native platform feature → installed dependency → one
  line → only then the minimum that works. Never cut validation, error
  handling, security, or accessibility in its name. In particular: this
  is a Leaflet `MapContainer` prop flip plus one `fitBounds` call inside
  the existing click handler — do not introduce new state, new
  components, or a new library for it.
- **Multi-Agent Execution (required):**
  1. Scout first: spawn a subagent to run graphify + recall on the
     modules this phase touches and report back the dependency map plus
     relevant prior context, before any implementation starts.
  2. Parallelize research: independent exploration/analysis tasks each go
     to their own subagent — one task per subagent — fed the scout's
     graphify output.
  3. Implement in the main thread: a single writer avoids file conflicts
     between agents.
  4. Review before close: a separate reviewer subagent independently
     verifies the phase — tests pass, the storyboard/walkthrough contract
     is met — before the phase is marked done.
- **State Management:** Before finishing, update CLAUDE.md: build
  commands, test commands, and current development state.
- **Tooling Protocol:** Primary runner is Claude Code — enter plan mode
  before implementing, per CLAUDE.md. For portability, when running
  outside Claude Code, load and execute this prompt via Caveman.

## Visual Reference (UI track, phases that build UI)
No new screens or layout — must continue to match
`images/screen-01-dashboard.png`. Only the map's interaction behavior
changes: a small zoom control (`+`/`-`) becomes visible in a corner that
doesn't collide with the existing `.map-title`, `.compass`, `.map-hud`,
or `.map-legend` overlays; everything else on Screen 1 is unchanged.
Cross-reference storyboard.md Screen 1.

## Deliverables
- `frontend/src/components/MapView.tsx`:
  - `dragging`, `scrollWheelZoom`, `doubleClickZoom` set to enabled;
    `zoomControl` enabled (or an explicit `<ZoomControl position="..."/>`
    placed to avoid the existing HUD overlays); `boxZoom`/`touchZoom`/
    `keyboard` enabled unless a specific one conflicts with an existing
    interaction (state the reason if any stays off).
  - `onEachKec`'s click handler calls `map.fitBounds(layer.getBounds(),
    { padding: [...] })` (or `layer.getBounds()` via the event's own
    target) in addition to the existing `openPopup(...)` call — use the
    already-mounted `mapRef`/map instance, don't create a second one.
- Tests: verify the `MapContainer` interaction props are enabled (not
  hardcoded `false`), and that clicking a kecamatan feature triggers a
  bounds-fit call on the map instance (mock/spy Leaflet's `fitBounds`,
  same style as existing `MapView`/`CommandMapScreen` tests stub
  `react-leaflet`/`leaflet`).
- `scripts/run-phase-10.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-10.sh`, executable, no arguments. It must:
- Start the shared postgres (`mata_api_algo-postgres-1`) if down, same
  check as every prior `run-phase-NN.sh`.
- Apply `migrations/0001_initial_schema.sql`.
- `docker compose up -d --build`, wait until `api` reports healthy.
- Run `ingest.py` for `data/2026_w34`, `_w31`, `_w30` only if `ingest_log`
  is empty (skip if already ingested, fast re-run otherwise — same
  pattern as `run-phase-09.sh`).
- Print the frontend URL and a short manual checklist: scroll the mouse
  wheel over the map and confirm it zooms in/out centered on the cursor;
  click-drag the map and confirm it pans; double-click the map and
  confirm it zooms in one level; click the visible `+`/`-` zoom control;
  click a kecamatan polygon and confirm the map smooth-zooms/pans to fit
  that polygon's bounds AND the existing inspect popup still opens.
It only starts the stack (with real data loaded) and tells the user what
to click — it does NOT assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-10.sh`, follow the printed
     checklist — scroll-zoom, drag-pan, double-click-zoom, zoom-control
     buttons, and kecamatan-click-to-zoom all work and the inspect popup
     still opens on that same click.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
