#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Postgres/PostGIS is shared with the mata_api_algo project — start it if down,
# never create a second one. Same check as run-phase-01.sh.
if [ "$(docker inspect -f '{{.State.Running}}' mata_api_algo-postgres-1 2>/dev/null || true)" != "true" ]; then
  echo "Starting shared postgres (mata_api_algo-postgres-1)..."
  docker start mata_api_algo-postgres-1
fi
until [ "$(docker inspect -f '{{.State.Health.Status}}' mata_api_algo-postgres-1)" = "healthy" ]; do
  sleep 2
done

docker compose up -d --build

echo "Waiting for containers to report healthy..."
for service in api web; do
  until [ "$(docker compose ps -q "$service" | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do
    sleep 2
  done
done

echo
echo "Frontend: http://localhost:5173"
echo
echo "Manual checklist — walk through each screen/state by hand:"
echo "  1. Command Map loads with week 2026-W34, Fire hazard active, grid colored by fire tier."
echo "  2. Click 'Landslide' in the hazard toggle — map recolors, sidebar swaps to the Landslide Risk layer."
echo "  3. Drag the Landslide Risk opacity slider — layer dims/brightens."
echo "  4. Click a red (high-risk) grid cell — popup shows grid id, category, score, slope, rainfall."
echo "  5. Click an Alert Summary card — matching cells flash, a toast confirms the count."
echo "  6. Click 'Export PDF Summary' — modal opens, click 'Generate Report' — spinner, then a filename, then a toast, then it auto-closes."
echo "  7. Click 'Ingest Log' in the header — table shows per-file status for the week; switch weeks."
echo "  8. On Command Map, pick week 2026-W99 from the dropdown — Empty Week screen explains why; click back."
echo "  9. Click the header link-status pill (or 'Simulate Connection Loss') — Connection Error screen; click Retry."
echo
echo "Confirm in devtools' network tab that nothing calls a real backend route other than /health."
