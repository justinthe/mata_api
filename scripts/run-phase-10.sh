#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01..09.sh.
if [ "$(docker inspect -f '{{.State.Running}}' mata_api_algo-postgres-1 2>/dev/null || true)" != "true" ]; then
  echo "Starting shared postgres (mata_api_algo-postgres-1)..."
  docker start mata_api_algo-postgres-1
fi
until [ "$(docker inspect -f '{{.State.Health.Status}}' mata_api_algo-postgres-1)" = "healthy" ]; do
  sleep 2
done

echo "Applying migrations/0001_initial_schema.sql (idempotent)..."
set -a; source .env; set +a
docker exec -i mata_api_algo-postgres-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < migrations/0001_initial_schema.sql

docker compose up -d --build

echo "Waiting for api to report healthy..."
until [ "$(docker compose ps -q api | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do
  sleep 2
done

ingest_log_rows=$(docker exec -i mata_api_algo-postgres-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT count(*) FROM ingest_log")
if [ "$ingest_log_rows" -eq 0 ]; then
  echo "ingest_log is empty — running ingest.py for all 3 sample weeks..."
  for week in data/2026_w34 data/2026_w31 data/2026_w30; do
    docker compose run --rm api python ingest.py "$week"
  done
else
  echo "ingest_log already has $ingest_log_rows row(s) — skipping ingest."
fi

echo
echo "Frontend: http://localhost:5173"
echo
echo "Manual checklist (Phase 10 — map navigation):"
echo "  - Scroll the mouse wheel over the map — it zooms in/out centered on the cursor."
echo "  - Click-drag the map — it pans."
echo "  - Double-click the map — it zooms in one level."
echo "  - Click the visible +/- zoom control (top-right, below the compass)."
echo "  - Click a kecamatan polygon — the map smooth-zooms/pans to fit its bounds AND"
echo "    the existing inspect popup still opens on that same click."
