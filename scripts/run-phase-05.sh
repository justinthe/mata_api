#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01/02/03/04.sh.
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

echo
echo "Swagger docs: http://localhost:8001/docs"
echo
echo "Example URLs to eyeball:"
echo "  http://localhost:8001/landslide/summary?week=2026-W31"
echo "  http://localhost:8001/landslide/summary?week=2026-W34   (no landslide CSVs ingested this week — empty but valid)"
echo "  http://localhost:8001/landslide/overlay?week=2026-W34   (mock_placeholder)"
