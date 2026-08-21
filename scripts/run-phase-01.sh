#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one.
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

echo "Waiting for containers to report healthy..."
for service in api web; do
  until [ "$(docker compose ps -q "$service" | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do
    sleep 2
  done
done

echo
echo "Frontend: http://localhost:5173"
echo "Backend health check: http://localhost:8001/health"
echo 'frontend shows {"db": "ok"} — open the URL above and confirm.'
