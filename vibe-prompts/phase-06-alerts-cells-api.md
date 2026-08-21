# Phase 06 — Alerts & Cell Detail API · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session builds exactly the following, and nothing else:
- `GET /alerts?week=&hazard=` — HIGH-alert areas per PRD.md's Assumptions
  threshold: fire = `risk_tier == "HIGH"`; landslide = `risk_category` in
  `{"Landslides Expected", "Active Landslides"}`; `hazard=combined` = a
  spatial unit HIGH on both. Feeds storyboard.md Screen 1's Alert Summary
  panel (fire count, landslide count, combined count, plus the list of
  matching spatial unit ids for zoom/flash).
- `GET /cells/{hazard}/{spatial_id}?week=` — full detail for one clicked
  grid/kecamatan (fire: tier, predicted count, hotspot count/density,
  mean/max FRP; landslide: score, category, factor breakdown, slope,
  rainfall) — this is what powers storyboard.md Screen 1's click-to-inspect
  popup, matching the exact fields shown in mockup.html's popup for each
  hazard.
- Reference: PRD.md §5 (F5, F6), §Assumptions (alert threshold
  definition), architecture.md §4 (API Boundaries — `/alerts`, `/cells`).

## Scope Boundary
- In scope: the 2 routes above, built on top of the fire and landslide
  data already exposed by Phase 04 and Phase 05's routers (reuse their
  query logic, do not duplicate it — import/call the same DB-reading
  functions rather than re-writing equivalent queries).
- Out of scope — do NOT touch: `/fire/*`, `/landslide/*` (already built),
  `/ingest-status` (Phase 08), `/reports/pdf` (Phase 09), any frontend
  code.

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
- `backend/app/routers/alerts.py`, `cells.py`.
- Automated API tests: `/alerts` counts for 2026-W31 verified by hand
  against the raw `landslide_scores_2026-W31.csv`/`fire_scores_2026-W34.csv`
  data (cross-check at least one known HIGH/Expected row); `/cells`
  returns 404 for an unknown `spatial_id` and exact field matches for a
  known one.
- `scripts/run-phase-06.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-06.sh`, executable, no arguments. It must:
- `docker compose up -d`, wait until the `api` container is healthy.
- Print the FastAPI docs URL (`http://localhost:8000/docs`) so the user
  can try `/alerts` and `/cells` by hand from the Swagger UI.
- Print 2–3 ready-to-paste example URLs (e.g.
  `http://localhost:8000/alerts?week=2026-W31&hazard=combined`,
  `http://localhost:8000/cells/landslide/LS-00250?week=2026-W31`) the
  user can open directly to eyeball the JSON response.
It only starts the stack and points the user at `/docs` — it does NOT
assert pass/fail itself.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-06.sh`, open
     `/alerts?week=2026-W31&hazard=combined` and manually cross-check the
     returned count against the two source CSVs for that week; open
     `/cells/landslide/LS-00250?week=2026-W31` (the documented
     `highest_risk_cell` for that week) and confirm the score matches
     `landslide_risk_2026-W31.json`'s `highest_risk_cell.score_255` (83.0).

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
