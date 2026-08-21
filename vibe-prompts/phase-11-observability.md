# Phase 11 — Observability · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session implements architecture.md §6 (Observability Plan) end to
end, and nothing else:
- Structured JSON logging for both `api` (FastAPI) and `ingest.py`:
  timestamp, level, a request/run correlation id, message — every request
  handler and every ingest run emits these consistently.
- `GET /health` (scaffolded in Phase 01) verified end-to-end: confirms it
  correctly reports DB-down when Postgres is unreachable, not just the
  happy path.
- `ingest_log` (already written by Phase 03) confirmed as the durable,
  queryable observability record, surfaced via `/ingest-status`
  (Phase 08) — this phase's job is to verify and, if gaps exist, close
  them so every ingest run is fully traceable after the fact.
- Reference: architecture.md §6 (Observability Plan), §3 (`ingest_log`).

## Scope Boundary
- In scope: logging format/wiring across `api` and `ingest.py`, `/health`
  hardening, closing any gap found in `ingest_log` coverage.
- Out of scope — do NOT touch: no error-tracking service (e.g. Sentry) —
  explicitly out of scope for v1 per architecture.md §6; no new business
  logic or routes beyond what already exists.

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. Logs go to stdout/stderr inside each container
  (standard docker-compose log capture), no external log shipping added
  in v1.
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
- JSON logging wired in `backend/app/` (request middleware/logger) and
  `ingest.py` (per-run logger).
- `/health` test covering both the DB-up and DB-down cases.
- Any missing `ingest_log` coverage closed (e.g. an untracked file type
  found during review).
- `scripts/run-phase-11.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-11.sh`, executable, no arguments. It must:
- `docker compose up -d`, wait until all containers are healthy.
- Tail `docker compose logs -f api` for a few seconds (or print the
  command for the user to run themselves) so the user can eyeball that
  log lines are valid JSON with the expected fields.
- Print the `/health` URL and the exact steps to stop/restart `postgres`
  to see the DB-down case.
It only starts the stack and points the user at the logs/URL — it does
NOT assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-11.sh`, watch `docker compose logs
     api` and confirm every line is valid JSON with the expected fields;
     stop `postgres`, open `/health`, confirm 503 + JSON detail; run
     `ingest.py` once more and confirm its log output is structured the
     same way.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
