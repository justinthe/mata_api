# Phase 03 — Ingest Pipeline · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, DATABASE.md, and CLAUDE.md in the
> workspace. Read CLAUDE.md first, enter plan mode before implementing,
> and verify ponytail is active. Portable: outside Claude Code, load and
> run this prompt via Caveman.

## Context Initialization
This session builds exactly the following, and nothing else:
- `ingest.py`: CLI entry point, `python ingest.py data/2026_w34` (etc.),
  that loads one week's files into Postgres per DATABASE.md tables +
  the new `ingest_log`/`raster_overlay` tables from architecture.md §3.
- `ingest/parsers/fire.py`: parses `fire_risk_*.json`, `fire_scores_*.csv`,
  `fire_weekly_features_*.csv` into `weekly_feature`, `fire_risk_prediction`
  rows.
- `ingest/parsers/landslide.py`: parses `landslide_risk_*.json`,
  `landslide_scores_*.csv`, `landslide_reclassified_*.csv`,
  `landslide_static_features_*.csv`, `landslide_dynamic_features_*.csv`
  into `landslide_weekly_score`, `landslide_static_feature`,
  `landslide_dynamic_feature` rows.
- `ingest/parsers/sar.py`: parses `fire_sar_result_*.csv`,
  `fire_sar_burned_area_*.json` into `sar_burned_area_detection` rows.
- `ingest/rasterize.py`: reads each risk/burned-area GeoTIFF with
  `rasterio`, colorizes per the fixed schemes in PRD.md §5/F4 (fire risk
  red/yellow/green; burned area band 1 0.0–1.0 red/yellow/green; landslide
  risk band 2 values 2/3/4 red/yellow/green) with Pillow, writes PNG to
  `generated/overlays/`, and upserts a `raster_overlay` row (bounds from
  the raster's geo-transform).
- `shared/boundary.py`: implement the stub from Phase 01 — dissolve
  `data/kelurahan.geojson` into `kecamatan_boundary` rows (45 Majalengka
  kecamatan; per DATABASE.md's noted `MultiPolygon` border-fragment
  workaround, keep only the largest sub-polygon).
- Idempotency: re-running `ingest.py` for an already-ingested week must not
  create duplicate rows (upsert on natural keys) — PRD.md F1.
- Partial-week tolerance: a week missing or `.mock`-only for a given file
  ingests what it has and records the rest as `mock_placeholder`/`missing`
  in `ingest_log`, without failing the run — PRD.md F1, matches the real
  gaps already observed in `data/2026_w34` (kecamatan tif + landslide tif
  are `.mock`, no landslide CSVs) and `data/2026_w30` (no fire grid tif, no
  fire_scores/fire_weekly_features CSVs).
- Reference: PRD.md §5 (F1), architecture.md §3 (Data Models — `ingest_log`,
  `raster_overlay`), §8 (Dependency Graph — `ingest.py` module list),
  DATABASE.md full schema.

## Scope Boundary
- In scope: `ingest.py` and its parser/rasterize modules, `shared/boundary.py`
  real implementation, running ingest against all 3 real sample weeks
  (`data/2026_w30`, `_w31`, `_w34`).
- Out of scope — do NOT touch: any HTTP API route (Phases 04–09), any
  frontend code, `hotspot_detection`/`known_fire_event`/`known_landslide_event`/
  `model_run`/`acquisition_log` tables (no source file in `data/` populates
  these — leave them empty, do not invent data for them).

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. `ingest.py` runs as a one-off inside the `api`
  container (`docker compose run --rm api python ingest.py data/2026_w34`),
  per architecture.md §5 — it is not a long-running service.
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
- `ingest.py`, `ingest/parsers/{fire,landslide,sar}.py`, `ingest/rasterize.py`.
- `shared/boundary.py` real dissolve implementation.
- `generated/overlays/*.png` for all rasters across the 3 real weeks.
- Automated tests covering: each parser against a real sample file, the
  rasterize color mapping (spot-check known pixel values against expected
  colors), idempotent re-ingest, partial-week tolerance.
- `scripts/run-phase-03.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-03.sh`, executable, no arguments. It must:
- Run `ingest.py` against `data/2026_w34`, `data/2026_w31`,
  `data/2026_w30` in sequence, printing each week's summary as it goes.
- Print a `psql` one-liner the user can paste to browse the ingested
  rows (e.g. row counts per table per week).
- Print the list of `generated/overlays/*.png` files produced, so the
  user can open a few directly in an image viewer and eyeball the
  red/yellow/green color mapping themselves.
It only runs the ingest and points the user at the results — it does NOT
assert pass/fail itself; the user opens the PNGs and DB rows and judges.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-03.sh`, inspect the resulting DB
     rows and open a few `generated/overlays/` PNGs directly, re-run once
     more and confirm row counts are unchanged.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
