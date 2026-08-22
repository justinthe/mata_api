#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01..12.sh.
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
echo "Manual checklist (Phase 13 — mobile responsive layout):"
echo "  Open browser devtools responsive mode at ~390x844 (iPhone-class) and confirm:"
echo "  1. Command Map shows the map, then all 3 alert cards, then the filters, in that scroll order."
echo "  2. Header fits on one line with no horizontal scrollbar."
echo "  3. Ingest Log's table scrolls horizontally without crushing its columns."
echo "  4. Empty Week / Error State (via the 'Simulate Connection Loss' button) text doesn't touch the screen edges."
echo "  5. Resize back up through 900px and full desktop width and confirm the existing tablet/desktop layouts are unchanged."
