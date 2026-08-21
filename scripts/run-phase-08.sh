#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01..07.sh.
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

# --build: backend code is baked into the api image at build time (no live
# mount), and this phase added a new router, so a rebuild is required for
# the running container to serve /ingest-status.
docker compose up -d --build

echo "Waiting for api to report healthy..."
until [ "$(docker compose ps -q api | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do
  sleep 2
done

echo
echo "Frontend: http://localhost:5173"
echo
echo "Manual checklist:"
echo "  - Click the 'Ingest Log' tab."
echo "  - Switch between 2026-W34, 2026-W31, 2026-W30, and 2026-W99."
echo "  - For 2026-W34, confirm: all 8 fire file types + landslide_risk_json show OK,"
echo "    landslide_risk_tif shows MOCK PLACEHOLDER, and the 4 landslide CSVs show MISSING."
echo "  - For 2026-W99 (never ingested), confirm the table shows no rows (clean empty state,"
echo "    not an error)."
