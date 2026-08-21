# Phase 04 — Fire API · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session builds exactly the following, and nothing else:
- `GET /weeks` — list of `iso_week`s present in `ingest_log`/DB, most
  recent first.
- `GET /boundaries` — `kecamatan_boundary` rows as GeoJSON.
- `GET /fire/summary?week=` — count-by-tier, highest-predicted,
  by-kecamatan, mirroring the shape of `fire_risk_*.json` (built from
  `weekly_feature` + `fire_risk_prediction`).
- `GET /fire/grid?week=` — per-grid tier/score list for click-to-inspect.
- `GET /fire/overlay/{layer}?week=` — `layer` = `grid`\|`kecamatan`\|
  `burned_area`; returns `{png_url, bounds}` from `raster_overlay`
  (404 if that layer wasn't ingested for the week — surface as
  `mock_placeholder` vs `missing` per `ingest_log`, not a bare 404).
- Reference: PRD.md §5 (F2–F4), architecture.md §4 (API Boundaries — fire
  rows), §7 (Security Posture — param validation).

## Scope Boundary
- In scope: the 5 routes above, reading only from tables populated by
  Phase 03's ingest (`weekly_feature`, `fire_risk_prediction`,
  `sar_burned_area_detection`, `kecamatan_boundary`, `raster_overlay`,
  `ingest_log`).
- Out of scope — do NOT touch: `/landslide/*` (Phase 05), `/alerts`,
  `/cells/*` (Phase 06), `/ingest-status` (Phase 08), `/reports/pdf`
  (Phase 09), any frontend code.

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. Routes live in `backend/app/routers/` and run
  inside the `api` container from Phase 01; no new services.
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

## Deliverables
- `backend/app/routers/weeks.py`, `boundaries.py`, `fire.py`.
- Static file mount for `generated/overlays/` (if not already added in
  Phase 01).
- Automated API tests for all 5 routes against the DB state left by
  Phase 03's ingest of `data/2026_w34`, `_w31`, `_w30` — including the
  `week=2026-W34` case where the kecamatan overlay is `mock_placeholder`.
- Server-side validation: `week` checked against real ingested weeks,
  `layer` checked against the fixed enum, 400 on anything else
  (architecture.md §7).
- `scripts/run-phase-04.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-04.sh`, executable, no arguments. It must:
- `docker compose up -d`, wait until the `api` container is healthy.
- Print the FastAPI docs URL (e.g. `http://localhost:8000/docs`) so the
  user can open it in a browser and try each fire route by hand from the
  Swagger UI.
- Print 2–3 ready-to-paste example URLs (e.g.
  `http://localhost:8000/fire/summary?week=2026-W34`,
  `http://localhost:8000/fire/overlay/kecamatan?week=2026-W34`) the user
  can open directly to eyeball the JSON response.
It only starts the stack and points the user at `/docs` — it does NOT
assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-04.sh`, use the printed `/docs` URL
     to try each route for 2026-W34, 2026-W31, 2026-W30, and a bogus week
     — confirm correct data, correct 404/400 behavior, and that
     `fire/overlay/kecamatan?week=2026-W34` reports its `mock_placeholder`
     status rather than pretending to be live data.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
