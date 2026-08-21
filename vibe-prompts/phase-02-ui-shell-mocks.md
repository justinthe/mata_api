# Phase 02 — UI Shell + Mock Data · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, mockup.html, images/, and CLAUDE.md in
> the workspace. Read CLAUDE.md first, enter plan mode before implementing,
> and verify ponytail is active. Portable: outside Claude Code, load and
> run this prompt via Caveman.

## Context Initialization
This session builds exactly the following, and nothing else:
- The full React UI shell for all 4 screens in storyboard.md — Command Map,
  Ingest Log, Empty Week, Connection Error — wired to **local mock
  fixtures only** (no real backend calls yet; `/health` from Phase 01 may
  stay wired since it already exists).
- react-leaflet map with the real Google Satellite XYZ basemap (per
  architecture.md §2) and Leaflet `ImageOverlay` layers driven by mock PNG
  placeholders + mock bounds (real overlays come from the backend in
  Phase 07).
- All interactive elements from mockup.html: week selector, Fire/Landslide
  hazard toggle (no "Both" — per the approved revision), per-layer
  visibility + opacity controls, click-to-inspect popup, alert summary
  cards with flash/zoom behavior, PDF export modal (mocked
  generate → toast, no real PDF yet), header nav between Command Map and
  Ingest Log, link-status pill.
- Reference: PRD.md §5 (F2–F6), §6 (User Flows), architecture.md §2 (Tech
  Stack — React/Vite, Google Satellite tiles), storyboard.md Screens 1–4.

## Scope Boundary
- In scope: all visual/interactive UI, componentized from the single-file
  mockup.html into a proper React app structure, using mock data functions
  that mirror the real API response shapes documented in architecture.md
  §4 (so swapping to real `fetch` calls in later phases is a small change).
- Out of scope — do NOT touch: `backend/` beyond what Phase 01 already
  created, `ingest.py`, any real `/fire`, `/landslide`, `/alerts`,
  `/cells`, `/ingest-status`, `/reports/pdf` endpoint implementation —
  those are mocked client-side this phase and implemented for real in
  Phases 03–09.

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. Frontend work happens inside the `web` container
  from Phase 01 (`docker compose up -d web`); no new services introduced.
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
Build all 4 screens to visually and behaviorally match their captures:
- Command Map → `images/screen-01-dashboard.png` (storyboard.md Screen 1)
- Ingest Log → `images/screen-02-ingest-status.png` (Screen 2)
- Empty Week → `images/screen-03-empty-week.png` (Screen 3)
- Connection Error → `images/screen-04-error-state.png` (Screen 4)

Match the militaristic dark theme exactly as implemented in mockup.html:
angular clipped panel corners, monospace font, phosphor-green accent,
red/yellow/green tier colors, the exact copy/labels shown (e.g. "SECTOR
MAJALENGKA", "ALERT SUMMARY", status chip text). Reuse mockup.html's CSS
values (color variables, clip-path polygons) rather than re-deriving them.
Cross-reference storyboard.md for each screen's states/transitions —
implement every state and transition listed there, including the
disabled/no-raster layer row state and the popup's per-hazard field sets.

## Deliverables
- `frontend/src/` componentized React app: `MapView`, `LayerControls`,
  `AlertPanel`, `InspectPopup`, `ExportModal`, `IngestLogScreen`,
  `EmptyWeekScreen`, `ErrorScreen`, `Header`, plus a router (hash or React
  Router) matching the 4 `data-screen` names from mockup.html.
- `frontend/src/mocks/` fixtures shaped like the real API responses
  (architecture.md §4) for weeks 2026-W34/W31/W30/W99.
- Component/interaction tests (React Testing Library or equivalent)
  covering: hazard toggle, opacity slider, cell click → popup, alert card
  click → flash, export modal happy path, week-select → empty-week
  navigation, link-pill → error-state navigation.
- `scripts/run-phase-02.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-02.sh`, executable, no arguments. It must:
- Start (or confirm running) the `web` dev server.
- Print the frontend URL to open in a browser.
- Print a short numbered checklist mirroring storyboard.md's Journey
  Summary (switch hazard, drag opacity, click a cell, click an alert
  card, open Export, switch to Ingest Log, pick the no-data week, trigger
  the error state) so the user can click through every screen/state by
  hand and see it for themselves.
It only starts the dev server and tells the user where to look and what
to click — it does NOT assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4) — reviewer
   must open each screen and confirm it matches its `images/screen-NN-*`
   reference.
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-02.sh`, walk through the printed
     checklist end to end against mock data; confirm nothing calls a real
     backend route other than `/health`.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
