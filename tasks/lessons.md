# Lessons

## Don't assume the spec's docker-compose sketch is the ground truth for local infra

Phase 01's `docker-compose.yml` per architecture.md §5 assumed a fresh `postgres` service. In reality this dev machine already had `mata_api_algo-postgres-1` running with the exact same `mata_hazard` DB/credentials — a sibling project's container, not something to spin up a duplicate of. Same story for host ports: 8000 was already taken by an unrelated project (`tamaris-backend`).

**Pattern:** before trusting a docs sketch for ports/service names, check what's actually running on the host (`docker ps -a`, `ss -ltn`) and ask the user if something unexpected turns up — don't silently work around it (could break someone else's running stack) and don't silently follow the doc (could create a duplicate/conflicting resource). The full container/env footprint of a "fresh" repo isn't always fresh on a shared dev machine.

See project memory `mata_api_shared_postgres` for the concrete resolution.

## `userEvent.click` on an `<a>` with no `href` silently no-ops

Phase 02's header nav tabs were `<a data-nav>` elements (ported straight from mockup.html) with only an `onClick` handler, no `href`. `fireEvent.click` fired the handler fine, but `@testing-library/user-event`'s `.click()` did not — no error, no warning, the click just didn't register, and the assertion after it passed anyway because the screen hadn't changed from its already-correct default state (a false-positive pass, not a failure).

**Pattern:** any element that only acts via JS (no real navigation) should be a `<button>`, not an anchor without `href` — it's also the correct semantic/accessibility choice. If a userEvent-driven test passes suspiciously easily (e.g. the assertion would also pass in the *unclicked* state), re-check with `fireEvent` to rule out a swallowed click before trusting the test.

## Leaflet `ImageOverlay` panes paint above plain sibling `<div>`s unless the container gets an explicit `z-index`

`.leaflet-container { position:absolute; inset:0; }` with no `z-index` doesn't establish its own stacking context, so Leaflet's internal panes (tile/overlay/marker, z-index ~200-700) escaped upward and painted over sibling elements with much higher `z-index` values (e.g. `z-index:20` HUD/legend/compass), washing out the whole map. Fix: give the leaflet-container itself an explicit `z-index` (even `0`) so its children's stacking is scoped inside it.

**Pattern:** whenever DOM siblings are layered around a `react-leaflet` map (custom overlays, controls, click-catching grids), give the map container an explicit `z-index`, don't assume `position:absolute` alone contains Leaflet's internal panes. Caught by an actual browser screenshot, not by the test suite — a reminder to eyeball non-trivial visual layering even when tests are green.

## Google satellite XYZ tile URLs need bare-digit `subdomains`, and a manual center/zoom guess will misalign an `ImageOverlay`

Two bugs an independent reviewer subagent caught that self-testing (typecheck, unit tests, one manual click-through) missed:

1. `url="https://mt{s}.google.com/..."` with `subdomains={["mt0","mt1",...]}` produces `mtmt0.google.com` — Leaflet substitutes `{s}` verbatim into the literal `mt` prefix already in the URL. `subdomains` must be the bare values (`["0","1","2","3"]`); the `mt` belongs only in the URL template. Every tile 503'd silently — nothing threw, the map just rendered black, and it was invisible in my own check because the mock grid cells fully cover the map area.
2. A guessed `center`+`zoom={12}` on `MapContainer` does not reliably show the same geographic extent as an `ImageOverlay`'s `bounds` — the container's actual pixel aspect ratio vs. the bounds' geographic aspect ratio determines what's visible, and a manual zoom guess ignores that. The overlay rendered in a completely different screen region than the full-container interactive grid. Fix: pass `bounds`+`boundsOptions={{padding:[0,0]}}` to `MapContainer` instead of a guessed `center`/`zoom`, so Leaflet fits the viewport to the same bounds the overlay uses.

**Pattern:** self-testing (types, unit tests, a single click-through) does not catch broken third-party network resources (tiles 503ing) or geo-alignment issues that only show up as a visual mismatch, especially when something else in the UI happens to visually mask the failure. An independent reviewer with fresh eyes — or deliberately re-checking with network-tab / DOM-geometry inspection rather than just "does it look okay" — is worth the round trip on anything involving external tile servers or map projections.
