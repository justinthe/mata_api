# Phase 03 — Ingest Pipeline

Plan: /home/jthe/.claude/plans/witty-questing-simon.md

- [x] shared/db.py: delete_rows() + list-filter support in read_rows/delete_rows (+ upsert_rows)
- [x] shared/boundary.py: real dissolve (shapely unary_union, largest-sub-polygon rule)
- [x] shared/tests/test_boundary.py: real assertions
- [x] backend/requirements.txt: + rasterio, Pillow, shapely
- [x] backend/Dockerfile: COPY ingest.py, ingest/ (+ libexpat1 apt dep)
- [x] ingest/parsers/fire.py + tests
- [x] ingest/parsers/landslide.py + tests
- [x] ingest/parsers/sar.py + tests
- [x] ingest/rasterize.py + tests
- [x] ingest.py orchestration (as ingest/orchestrate.py, thin ingest.py shim)
- [x] ingest/tests/test_ingest_idempotent.py + test_ingest_partial_week.py
- [x] scripts/run-phase-03.sh
- [x] docker compose run --rm api pytest — 20/20 green
- [x] frontend npm test + npm run typecheck — still green
- [x] ./scripts/run-phase-03.sh manual run + eyeball PNGs + re-run idempotency check
- [x] /ponytail-review on diff (2 findings, both applied)
- [x] reviewer subagent sign-off — PASS
- [x] graphify re-run (end of phase) — clean, not spaghetti
- [x] CLAUDE.md state update

## Review

All 3 real sample weeks (2026_w30/w31/w34) ingest cleanly, idempotently, and
tolerate their real partial-data gaps without failing. Independent reviewer
subagent verified against the live DB and PASSed. Key design decisions made
with the user along the way: app-level delete-then-insert for idempotency
(no schema changes), skip-and-log landslide rows with no matching
landslide_grid_cell (only 50/500 bootstrapped), and a 45-kecamatan boundary
roster matching the real sample data's ids rather than the real 26-kecamatan
Majalengka. Full detail in CLAUDE.md's Project State section.

Bugs caught only by running against the real DB (not by static review):
ingest.py/ingest/ package name collision, 3D source geometry vs 2D column,
missing libexpat1 in the slim base image, and a delete-order FK bug on
re-ingest (fire_risk_prediction before weekly_feature).
