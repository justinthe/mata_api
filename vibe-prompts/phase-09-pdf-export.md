# Phase 09 — PDF Export · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session builds exactly the following, and nothing else:
- `POST /reports/pdf` — body `{week, hazard, map_image_base64}`, returns a
  PDF binary. Uses `reportlab` to compose: the client-captured map
  snapshot, a per-kecamatan risk table (from the same summary data as
  `/fire/summary`/`/landslide/summary`), and the list of HIGH-alert areas
  (from `/alerts`, reused directly — do not duplicate the threshold logic
  from Phase 06). Writes nothing to the database — generation only.
- Frontend: the Export modal (built mocked in Phase 02) now captures a
  real map snapshot (e.g. via `leaflet-image` or an equivalent canvas
  capture of the live Leaflet map), POSTs it with the current week/hazard
  filter, and triggers a real file download of the returned PDF named
  `mata-hazard-<week>-<hazard>.pdf`.
- Reference: PRD.md §5 (F7), §Assumptions (PDF contents), architecture.md
  §4 (`POST /reports/pdf`), §8 (Dependency Graph — `routers/reports.py`,
  `ExportButton.tsx`), storyboard.md Screen 1 Journey Summary step 6.

## Scope Boundary
- In scope: `/reports/pdf` route and the Export modal's real
  generate/download flow.
- Out of scope — do NOT touch: any other route or screen; this phase must
  not introduce a new way to compute alert/summary data — it calls the
  existing Phase 04/05/06 functions.

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. PDF generation happens synchronously inside the
  `api` container request handler — no new service, no headless browser,
  per architecture.md §2's reportlab choice.
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
The Export modal's shape (fields, spinner state, success state, toast)
must continue to match mockup.html's export flow, embedded in
storyboard.md Screen 1 — only the "Generate Report" action now performs a
real POST + download instead of a `setTimeout` mock.

## Deliverables
- `backend/app/routers/reports.py`.
- Frontend map-snapshot capture + real download wiring in the Export
  modal.
- Tests: `/reports/pdf` returns a valid PDF (parseable, non-empty) for a
  known week/hazard combination; the per-kecamatan table and HIGH-alert
  list in the generated PDF match the same week's `/fire/summary` (or
  `/landslide/summary`) and `/alerts` responses exactly.
- `scripts/run-phase-09.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-09.sh`, executable, no arguments. It must:
- `docker compose up -d --build`, wait until all containers are healthy.
- Run `ingest.py` for the sample weeks if the DB is empty (skip if
  already ingested).
- Print the frontend URL and the exact click path: "open the URL, select
  week 2026-W31, click Export PDF Summary, click Generate Report, then
  open the downloaded PDF and check the map image, kecamatan table, and
  HIGH-alert list are all there and correct."
It only starts the stack (with real data loaded) and tells the user
exactly what to click — it does NOT assert pass/fail itself; the user
opens the downloaded PDF and judges it by eye.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-09.sh`, follow the printed click
     path — on the live Command Map, select 2026-W31 with a mix of tiers
     visible, click Export, generate the report, open the downloaded PDF,
     and confirm the map snapshot, table, and alert list are present and
     correct for that week/hazard.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
