#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01..08.sh.
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
# mount), and this phase added a new router + dependencies, so a rebuild is
# required for the running container to serve /reports/pdf.
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
echo "Manual checklist:"
echo "  - Open the URL, select week 2026-W31 (a mix of tiers is visible on both hazards)."
echo "  - Click 'Export PDF Summary', then 'Generate Report'."
echo "  - Open the downloaded mata-hazard-2026-W31-fire.pdf and confirm it has a map image,"
echo "    a per-kecamatan risk table, and a HIGH-alert area list matching the live Command Map."
echo "  - Note: the base satellite tile layer (mt{s}.google.com) has no CORS headers, so the"
echo "    captured map image may show blank/grey where the base imagery would be — the overlay"
echo "    PNGs and kecamatan boundaries (the actual hazard data) should still be visible. This is"
echo "    a known html2canvas/CORS limitation, not a bug."
echo "  - Repeat for hazard=landslide (toggle the hazard filter, regenerate)."
