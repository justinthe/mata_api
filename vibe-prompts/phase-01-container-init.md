# Phase 01 — Container & Environment Init · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify ponytail
> is active. Portable: outside Claude Code, load and run this prompt via
> Caveman.

## Context Initialization
This session builds exactly the following, and nothing else:
- `docker-compose.yml` with 3 services: `postgres` (PostGIS), `api`
  (FastAPI), `web` (Vite/React dev server), per architecture.md §5.
- `.env` wiring (`DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
  `POSTGRES_DB`) — reuse the existing `.env` in this repo, do not overwrite
  its values, only add anything missing.
- `migrations/0001_initial_schema.sql`: all 14 tables from DATABASE.md
  §Schema, plus the 2 new tables from architecture.md §3 (`ingest_log`,
  `raster_overlay`). `IF NOT EXISTS` throughout, idempotent re-run safe.
- `shared/db.py`: `get_connection()`, `write_rows(table, rows)`,
  `read_rows(table, filters)` per DATABASE.md's documented IO layer
  (SQLAlchemy + GeoAlchemy2, table reflection, no ORM models).
- `shared/boundary.py`: stub for dissolving `data/kelurahan.geojson` into
  `kecamatan_boundary` rows (real dissolve logic lands in Phase 03 — this
  phase only needs the function signature + a `NotImplementedError` body
  tagged `# implemented in phase 03`).
- `backend/` FastAPI app skeleton: `app/main.py` with a single
  `GET /health` route that runs `SELECT 1` against the DB and returns
  `{"db": "ok"}` or a 503 with `{"db": "unreachable"}`.
- `frontend/` Vite + React skeleton: one page that fetches `/health` on
  load and displays the result. No styling, no map, no other routes —
  that is Phase 02.
- Reference: architecture.md §1 (System Topology), §2 (Tech Stack), §5
  (Containerization & Environments), §6 (`/health`); DATABASE.md
  §Connection, §Schema.

## Scope Boundary
- In scope: compose file, schema migration, `shared/db.py`,
  `shared/boundary.py` stub, `/health` endpoint, minimal frontend shell
  that calls it.
- Out of scope — do NOT touch: any UI beyond the health-check page (Phase
  02), ingest logic (Phase 03), any `/fire`, `/landslide`, `/alerts`,
  `/cells`, `/ingest-status`, `/reports` routes (Phases 04–09), PNG overlay
  generation, PDF generation.

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. Everything in this project runs via
  `docker compose up -d` (Postgres/PostGIS + FastAPI `api` + Vite `web`,
  per architecture.md §5); no service assumes a locally-installed Postgres
  or Node outside its container.
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
- `docker-compose.yml` (postgres, api, web services).
- `migrations/0001_initial_schema.sql`.
- `shared/db.py`, `shared/boundary.py` (stub).
- `backend/app/main.py` with `GET /health`.
- `frontend/` Vite/React app with a single health-check page.
- `scripts/run-phase-01.sh` — one-command launcher for manual eyeball
  checking (see below).
- `CLAUDE.md` updated with build/test commands and current state.

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-01.sh`, executable, no arguments. It must:
- `docker compose up -d --build`, wait until all 3 containers report
  healthy.
- Print the frontend URL (e.g. `http://localhost:5173`) and the backend
  URL (e.g. `http://localhost:8000/health`) to open in a browser.
- Print one line telling the user what they should see: "frontend shows
  {\"db\": \"ok\"} — open the URL above and confirm."
It only stands the stack up and tells the user where to look — it does
NOT assert pass/fail itself; the user judges the result by eye.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-01.sh`, open the printed frontend
     URL, confirm it shows `{"db": "ok"}`; stop the `postgres` container
     and confirm `/health` now returns 503; restart it.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
