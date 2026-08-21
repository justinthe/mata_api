#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01/02.sh.
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

docker compose build api

for week in data/2026_w34 data/2026_w31 data/2026_w30; do
  echo
  echo "=== ingesting $week ==="
  docker compose run --rm api python ingest.py "$week"
done

echo
echo "Browse ingested rows — paste this to open a psql shell:"
echo "  docker exec -it mata_api_algo-postgres-1 psql -U $POSTGRES_USER -d $POSTGRES_DB"
echo "Then, e.g.:"
cat <<'SQL'
  SELECT iso_week, file_type, status, detail FROM ingest_log ORDER BY iso_week, file_type;
  SELECT iso_week, count(*) FROM weekly_feature GROUP BY iso_week;
  SELECT iso_week, count(*) FROM landslide_weekly_score GROUP BY iso_week;
  SELECT iso_week, layer_type, png_path FROM raster_overlay ORDER BY iso_week, layer_type;
SQL

echo
echo "Generated overlay PNGs (open a few directly and eyeball red/yellow/green):"
ls -1 generated/overlays/*.png 2>/dev/null || echo "  (none produced)"
