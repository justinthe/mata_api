#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01/02/03.sh.
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

# Re-run ingest for all 3 weeks -- idempotent, and keeps ingest_log/raster_overlay
# in sync with whatever's currently on disk in data/ (e.g. stale .mock sidecars
# removed since the last ingest run).
for week in data/2026_w34 data/2026_w31 data/2026_w30; do
  docker compose run --rm api python ingest.py "$week"
done

echo "Waiting for api to report healthy..."
until [ "$(docker compose ps -q api | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do
  sleep 2
done

echo
echo "Swagger docs: http://localhost:8001/docs"
echo
echo "Example URLs to eyeball:"
echo "  http://localhost:8001/weeks"
echo "  http://localhost:8001/fire/summary?week=2026-W31"
echo "  http://localhost:8001/fire/grid?week=2026-W31"
echo "  http://localhost:8001/fire/overlay/kecamatan?week=2026-W34"
echo "  http://localhost:8001/fire/overlay/grid?week=2026-W30   (missing this week — no grid tif)"
