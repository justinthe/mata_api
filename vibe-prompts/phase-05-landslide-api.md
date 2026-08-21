# Phase 05 — Landslide API · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session builds exactly the following, and nothing else:
- `GET /landslide/summary?week=` — count-by-category, area-by-category,
  highest-risk cell, by-kecamatan, mirroring `landslide_risk_*.json`
  (built from `landslide_weekly_score`).
- `GET /landslide/grid?week=` — per-grid score/category/factor-breakdown
  list for click-to-inspect (`landslide_weekly_score.factor_breakdown`
  jsonb, plus `landslide_static_feature`/`landslide_dynamic_feature`
  slope/rainfall for the popup fields shown in storyboard.md Screen 1).
- `GET /landslide/overlay?week=` — `{png_url, bounds}` for the landslide
  risk raster from `raster_overlay` (404-with-status if `mock_placeholder`
  or `missing`, same pattern as Phase 04's fire overlay route).
- Reference: PRD.md §5 (F2–F4), architecture.md §4 (API Boundaries —
  landslide rows), §7 (Security Posture — param validation).

## Scope Boundary
- In scope: the 3 routes above, reading only from
  `landslide_weekly_score`, `landslide_static_feature`,
  `landslide_dynamic_feature`, `raster_overlay`, `ingest_log`.
- Out of scope — do NOT touch: `/fire/*` (already built in Phase 04),
  `/alerts`, `/cells/*` (Phase 06), `/ingest-status` (Phase 08),
  `/reports/pdf` (Phase 09), any frontend code.

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
- `backend/app/routers/landslide.py`.
- Automated API tests for all 3 routes against the DB state left by
  Phase 03's ingest — including `week=2026-W34` where the landslide risk
  raster is `mock_placeholder` and no landslide CSVs were ingested at all
  (summary/grid should reflect that emptiness cleanly, not error).
- `scripts/run-phase-05.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-05.sh`, executable, no arguments. It must:
- `docker compose up -d`, wait until the `api` container is healthy.
- Print the FastAPI docs URL (`http://localhost:8000/docs`) so the user
  can try each landslide route by hand from the Swagger UI.
- Print 2–3 ready-to-paste example URLs (e.g.
  `http://localhost:8000/landslide/summary?week=2026-W31`,
  `http://localhost:8000/landslide/summary?week=2026-W34`) the user can
  open directly to eyeball the JSON response.
It only starts the stack and points the user at `/docs` — it does NOT
assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-05.sh`, use the printed `/docs` URL
     to try each route for 2026-W31 (fully populated) and 2026-W34 (no
     landslide CSVs ingested) — confirm W31 returns real
     scores/categories and W34 returns an empty-but-valid result rather
     than a 500.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
