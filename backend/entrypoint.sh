#!/bin/sh
set -e

psql "$DATABASE_URL" -f migrations/0001_initial_schema.sql

# Always re-ingest: the DB (Postgres) persists across boots, but Render's
# disk is ephemeral, so generated/overlays/*.png from a prior boot is gone
# on every fresh container -- skipping by ingest_log row count left the
# overlay PNGs 404ing after any redeploy while the DB still had stale rows.
python ingest.py data/2026_w30
python ingest.py data/2026_w31
python ingest.py data/2026_w34

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
