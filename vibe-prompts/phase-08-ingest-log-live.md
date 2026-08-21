# Phase 08 — Ingest Log Live · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session builds exactly the following, and nothing else:
- `GET /ingest-status?week=` — returns the `ingest_log` rows for a week
  (file_type, status, detail), per architecture.md §4.
- Wires the Ingest Log screen (Screen 2, built with mock data in Phase 02)
  to this real endpoint, replacing `INGEST_STATUS`/`INGEST_FILES` mock
  fixtures with a live fetch.
- Reference: PRD.md §5 (F1's observability requirement, persona Budi),
  architecture.md §4 (`/ingest-status`), §6 (Observability Plan —
  `ingest_log` as the queryable ingest record), storyboard.md Screen 2.

## Scope Boundary
- In scope: the `/ingest-status` route and Screen 2's data wiring.
- Out of scope — do NOT touch: Command Map, Empty Week, Connection Error
  screens (already live from Phase 07), `/reports/pdf` (Phase 09).

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. Route lives in `backend/app/routers/`, runs
  inside the `api` container; frontend calls it via the same
  `api/client.ts` base URL established in Phase 07.
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
Screen 2 must continue to match `images/screen-02-ingest-status.png`
exactly — only the data source changes from the Phase 02 mock table to a
live fetch. Cross-reference storyboard.md Screen 2 for its single
data-driven state (status chip per row: OK / MOCK PLACEHOLDER / MISSING).

## Deliverables
- `backend/app/routers/ingest_status.py`.
- Screen 2 re-wired to `GET /ingest-status`.
- Tests: `/ingest-status?week=2026-W34` returns the exact OK/MOCK/MISSING
  pattern matching the real `data/2026_w34/` contents ingested in Phase 03
  (kecamatan tif + landslide tif = MOCK, all landslide CSVs = MISSING,
  everything else = OK); `week=2026-W99` (never ingested) returns all rows
  MISSING or a clean empty result, not an error.
- `scripts/run-phase-08.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-08.sh`, executable, no arguments. It must:
- `docker compose up -d`, wait until all containers are healthy.
- Print the frontend URL and instruct: open it, click the "Ingest Log"
  tab, switch between 2026-W34/W31/W30/W99, and eyeball whether the
  status chips match reality (W34 should show kecamatan-tif and
  landslide-tif as MOCK PLACEHOLDER and all landslide CSVs as MISSING).
It only starts the stack and points the user at the screen — it does NOT
assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-08.sh`, open Screen 2 for
     2026-W34, 2026-W31, 2026-W30 and confirm the displayed statuses
     match what Phase 03's ingest actually recorded for each week
     (cross-check against the `ingest_log` table directly if unsure).

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
