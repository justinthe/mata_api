# HOWTO — deployed MATA Hazard Command

Where this app lives, why it behaves the way it does, and how to operate it.

## URLs

- Frontend: https://mata-hazard-web.onrender.com
- Backend API: https://mata-api-3egi.onrender.com (health check: `/health`)
- Database: Supabase Postgres/PostGIS, project `wpnmwcgkfxhrrfqksifi`

## Waking the backend after it sleeps

**Why it sleeps**: the backend runs on Render's free Web Service tier, which
spins the container down after 15 minutes with no requests. This is a Render
platform limit, not something in this app's config — the only way off it is
a paid plan.

**Why cold start is slow (~5 min)**: on every boot, `backend/entrypoint.sh`
re-applies the DB migration and re-runs `ingest.py` for all 3 sample weeks
before starting the server. This is deliberate, not a bug: Render's disk is
ephemeral, so the overlay PNGs (`generated/overlays/*.png`) written by a
previous boot don't survive a restart, even though the database itself
(Supabase, separate service) does. Skipping ingest when the DB already had
rows — the original design — left the overlay images 404ing after every
sleep/wake cycle, so the entrypoint always regenerates them now instead.

**How to wake it**: just visit the frontend or hit
https://mata-api-3egi.onrender.com/health. Any request wakes the container;
no dashboard button needed. Give it ~5 minutes before the app is fully
responsive — the migration + 3-week ingest has to finish before uvicorn
starts accepting requests.

**To avoid this entirely**: upgrade the Render web service to a paid plan
(Starter, $7/mo) — no sleep, and persistent disk means ingest only needs to
run once, ever, not on every cold boot.

## Redeploying after a code change

Render is connected to the GitHub repo as a **Public Git Repository**, not
via the GitHub App integration — this means **no push webhook**, so
`git push` alone does *not* trigger a redeploy. After pushing:

1. Go to the Render dashboard → `mata_api` service → **Manual Deploy** →
   **Deploy latest commit**.
2. Same for the static site (`mata-hazard-web`) if frontend code changed.

## Credentials

Real secret values (DB password, full connection strings, service IDs) live
in `deploy-credentials.md` at the repo root — **gitignored, never
committed**. That file is the only copy; Supabase only shows a DB password
once, at creation/reset time, so if it's lost the fix is resetting it again
(Supabase dashboard → Database Settings → Reset database password), then
updating `DATABASE_URL` in Render's Environment tab and manually redeploying.

**Gotcha if you ever reset the password again**: percent-encode any special
characters before putting it in `DATABASE_URL` — e.g. a literal `%` becomes
`%25`. An unencoded special character breaks Postgres's URI parser in a
confusing way (it misparses the port instead of complaining about the
password).

**Gotcha with Render's env var editor**: editing an existing variable's
value in place has been unreliable — the UI shows "saved" but the redeploy
runs with the old value. If a `DATABASE_URL`/env var change doesn't seem to
take effect, delete the row entirely and re-add it fresh rather than editing.

## Known gap: landslide per-cell data

Fire data and both raster overlay layers (fire + landslide) work fully.
Landslide's *per-cell* scores (`/landslide/summary`, `/landslide/grid`) come
back empty. Cause: the 50-row `landslide_grid_cell` seed table was
originally populated by a separate sibling project (`mata_api_algo`)
directly into the old local shared Postgres container — never part of this
repo's own migration or `ingest.py`. That seed step has no equivalent here,
so the fresh Supabase database never gets those 50 rows. Not a regression
from this deploy — it's a gap that only became visible once the app left the
local shared-Postgres setup that `mata_api_algo` was quietly feeding.

## Free-tier limits to know about

- **Render web service**: sleeps after 15 min idle (see above).
- **Supabase free project**: pauses after 7 days with zero API/DB activity.
  Unpausing needs a manual click in the Supabase dashboard (an incoming
  request doesn't auto-wake it, unlike Render).
- **Render free Postgres** was considered but not used (wanted a card on
  file even for the free tier) — Supabase was the workaround, see earlier
  chat history for that decision.

## Troubleshooting: `/health` returns `{"db":"unreachable"}`

Two different causes produce this exact same symptom. Check which one first
before doing anything — the fixes are unrelated.

### Cause 1: Supabase's connection pooler is exhausted (seen 2026-08-21)

**What happened**: `shared/db.py::get_connection()` used to call
`create_engine()` on *every* database operation — every single API request
opened a brand-new SQLAlchemy connection pool that never got disposed. Against
Supabase's session-mode pooler, which hard-caps at 15 concurrent client
connections on the free tier, this exhausted the pool within minutes of
normal traffic. Once exhausted, *every* new connection attempt fails
server-side with `FATAL: (EMAXCONNSESSION) max clients reached in session
mode` — including the migration step's own `psql` connection on the next
boot, so even redeploying didn't fix it; the stale connections had to be
force-cleared. This is fixed now (`get_connection()` caches one `Engine` per
process, see `shared/db.py`), but if it (or something like it — a new code
path that creates its own engine/connections without reusing the shared one)
ever recurs:

**How to recognize it**: Supabase's project dashboard
(https://supabase.com/dashboard/project/wpnmwcgkfxhrrfqksifi) shows
**Status: Healthy** (not paused/restarting) — the project itself is fine,
it's just out of connection slots. Render's logs
(service → Logs) show `FATAL: (EMAXCONNSESSION) max clients reached in
session mode` or `sqlalchemy.exc.OperationalError` mentioning the pooler
host.

**Fix**:
1. Supabase dashboard → Settings → General → **Project availability** →
   **Restart project**. This force-closes every open connection (few
   minutes of DB downtime while it restarts).
2. Once Supabase is back (its REST API at
   `https://wpnmwcgkfxhrrfqksifi.supabase.co/rest/v1/` returns `401`
   instead of timing out/erroring — that means it's up, `401` just means no
   API key was sent), go to Render → `mata_api` service → **Manual Deploy**
   → **Deploy latest commit** to reconnect the backend with a clean pool.

**If it keeps recurring**: something is creating connections outside the
cached-engine path again. `DATABASE_URL` is currently on Supabase's
**session pooler** (port 5432, 15-client cap). Switching to the
**transaction pooler** (port 6543 — same connection string shape, ask
Supabase's Connect dialog for it) tolerates many more short-lived app
connections and is generally more forgiving for a typical request/response
API like this one.

### Cause 2: Supabase project auto-paused (7 days with zero activity)

**How to recognize it**: Supabase dashboard shows the project as **Paused**,
not Healthy.

**Fix**: Supabase dashboard → click **Restore project**, wait a minute or
two, no Render redeploy needed (Render's connection retries on its own).
