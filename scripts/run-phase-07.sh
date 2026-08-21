#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01/02/03/04/05/06.sh.
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
  echo "ingest_log already has $ingest_log_rows row(s) — skipping ingest (re-run scripts/run-phase-04.sh if you need a fresh re-ingest)."
fi

echo
echo "Frontend: http://localhost:5173"
echo
echo "Manual checklist:"
echo "  - Switch between all 3 real weeks (2026-W34/W31/W30) and both hazards (Fire/Landslide)."
echo "  - Drag a layer's opacity slider and confirm the raster overlay dims/brightens."
echo "  - Click a kecamatan polygon on the map, and a row in the left sidebar's Grid Cells list —"
echo "    confirm the inspect popup shows real numbers for each."
echo "  - Click each of the 3 Alert Summary cards (Fire / Landslide / Combined) — confirm the toast"
echo "    count matches the card, and the landslide card flashes matching Grid Cells rows."
echo "  - Select 2026-W99 from the week dropdown — confirm the Empty Week screen."
echo "  - Run 'docker compose stop api', then click the header's LINK pill or wait for a fetch to"
echo "    fail — confirm the Connection Error screen."
echo "  - Run 'docker compose start api', click Retry Connection — confirm it returns to a live"
echo "    Command Map with real data."
