# Phase 07 — Command Map Live Integration · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session replaces every mock data call in the Command Map screen
(Phase 02) with the real endpoints built in Phases 04–06, and nothing
else:
- Week selector → `GET /weeks`.
- Kecamatan boundary lines → `GET /boundaries`.
- Hazard summary + grid → `GET /fire/summary`, `/fire/grid`,
  `/landslide/summary`, `/landslide/grid` depending on the active toggle.
- Raster `ImageOverlay`s → `GET /fire/overlay/{layer}`,
  `/landslide/overlay` — real PNGs at real bounds, opacity sliders now
  control the real Leaflet layer's opacity.
- Alert Summary cards → `GET /alerts`.
- Click-to-inspect popup → `GET /cells/{hazard}/{spatial_id}`.
- Empty Week screen (Screen 3) → triggered when `/weeks` doesn't include
  the selected week, or the week's summary comes back empty, instead of
  the mock "2026-W99" trigger from Phase 02.
- Connection Error screen (Screen 4) → triggered by a real fetch failure
  (network error or 5xx) on any of the above, replacing the mock
  "Simulate Connection Loss" button's behavior with real detection (the
  button may stay as a manual dev trigger, but the screen must also appear
  on genuine failures); Retry re-runs the failed fetch(es).
- Reference: PRD.md §5 (F2–F6), §6 (User Flows 1–6), architecture.md §4
  (API Boundaries), storyboard.md Screens 1, 3, 4.

## Scope Boundary
- In scope: Command Map, Empty Week, and Connection Error screens' data
  layer only — swap mocks for real `fetch` calls, add loading/error
  handling.
- Out of scope — do NOT touch: Ingest Log screen (Phase 08), PDF export
  (Phase 09), any backend route (already built in Phases 04–06 — this
  phase only consumes them).

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. Frontend calls the `api` container's routes via
  the compose network / configured base URL from architecture.md §5; no
  hardcoded ports outside that config.
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
  handling, security, or accessibility in its name.
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
No new visual elements this phase — the screens must continue to match
`images/screen-01-dashboard.png`, `images/screen-03-empty-week.png`, and
`images/screen-04-error-state.png` exactly; only the data source behind
them changes from mock fixtures to live `fetch` calls. Cross-reference
storyboard.md Screens 1, 3, 4 for the states/transitions that must now be
driven by real conditions instead of mock triggers.

## Deliverables
- `frontend/src/api/client.ts` — fetch wrappers for `/weeks`, `/boundaries`,
  `/fire/*`, `/landslide/*`, `/alerts`, `/cells/*`.
- Command Map, Empty Week, Connection Error screens re-wired to
  `api/client.ts` instead of `mocks/`.
- Loading state for in-flight requests (map/panels show a lightweight
  loading indicator, not a blank flash).
- Tests: mock the `fetch` layer (not the UI) to verify real week switching,
  real overlay opacity, real alert counts, empty-week trigger on a
  no-data week, error-screen trigger on a simulated network failure, and
  successful retry.
- `scripts/run-phase-07.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-07.sh`, executable, no arguments. It must:
- `docker compose up -d --build`, wait until all containers are healthy.
- Run `ingest.py` for `data/2026_w34`, `_w31`, `_w30` if the DB is empty
  (skip if already ingested, so re-runs are fast).
- Print the frontend URL and a short checklist: switch between the 3 real
  weeks and both hazards, drag an opacity slider, click a cell, click an
  alert card, pick 2026-W99 and confirm the Empty Week screen, stop the
  `api` container and confirm the Connection Error screen, restart it and
  click Retry.
It only starts the stack (with real data loaded) and tells the user what
to click — it does NOT assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-07.sh`, follow the printed
     checklist — select each real week and confirm overlays/alerts/
     popups show real ingested data; select a week not in `/weeks` and
     confirm Screen 3 appears; stop the `api` container and confirm
     Screen 4 appears, then restart it and confirm Retry recovers to
     Screen 1.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
