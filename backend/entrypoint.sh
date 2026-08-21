#!/bin/sh
set -e

psql "$DATABASE_URL" -f migrations/0001_initial_schema.sql

rows=$(psql "$DATABASE_URL" -tAc "SELECT count(*) FROM ingest_log")
if [ "$rows" -eq 0 ]; then
  python ingest.py data/2026_w30
  python ingest.py data/2026_w31
  python ingest.py data/2026_w34
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
