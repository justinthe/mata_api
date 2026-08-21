# Phase 12 — Security Audit · MATA Hazard Command

> Run in a fresh Claude Code session (or /clear) with the PRD (PRD.md),
> architecture.md, storyboard.md, and CLAUDE.md in the workspace. Read
> CLAUDE.md first, enter plan mode before implementing, and verify
> ponytail is active. Portable: outside Claude Code, load and run this
> prompt via Caveman.

## Context Initialization
This session executes a full post-build security audit of the whole app
built across Phases 01–10, and nothing else — no new features. MATA
Hazard Command has no authentication in v1 (PRD.md §8, explicit
assumption), so the riskiest flows are: unauthenticated access to every
route, unvalidated query/path parameters reaching SQL or the filesystem,
the PDF endpoint accepting a client-supplied image payload, and static
file serving of `generated/overlays/`.
Reference: architecture.md §7 (Security Posture), PRD.md §8
(Non-Functional Requirements), §Assumptions (no auth in v1).

## Scope Boundary
- In scope: auditing and hardening every route built in Phases 04–09, the
  static overlay mount, the ingest CLI's handling of untrusted filenames
  under `data/`, and CORS/secrets configuration.
- Out of scope — do NOT touch: adding authentication itself (explicitly
  deferred past v1 per PRD.md) — flag it as a known gap instead of
  building it; do not add rate limiting beyond what architecture.md §7
  already calls for (no public/cost-sensitive routes exist, since Google
  tiles are fetched client-side).

## Guardrails (mandatory in EVERY phase — never drop or abbreviate)
- **Containerization & Structure:** All code adheres to isolated
  environment principles. All fixes apply inside the existing
  `docker compose` services; no new services introduced.
- **Graphify (required, start AND end of this phase):**
  - At the start, run `graphify` to map the existing architecture of the
    module(s) this phase touches plus the proposed changes, before writing
    any code.
  - Use the graph to find hidden dependencies that this phase could break.
  - At the end, run `graphify` again to verify the resulting "after" state
    matches the intended design — if the graph looks like spaghetti, the
    solution is not elegant; simplify before closing the phase.
- **Recall (required, throughout):** Use `recall` to cross-reference prior
  state and context — CLAUDE.md, tasks/todo.md, tasks/lessons.md, and
  earlier phases' code and tests — before and during implementation, so
  this phase does not regress or contradict work already approved.
- **TDD:** Write automated tests alongside or prior to the implementation.
  All tests from previous phases must still pass.
- **Ponytail (required, level: ultra):** Verify the ponytail plugin is
  active at this level before writing code (`/ponytail` reports the
  current level; set it with `/ponytail ultra` if needed). Apply its
  ladder to every change: does this need to exist → reuse what's in the
  codebase → stdlib → native platform feature → installed dependency → one
  line → only then the minimum that works. Never cut validation, error
  handling, security, or accessibility in its name.
- **Multi-Agent Execution (required):**
  1. Scout first: spawn a subagent to run graphify + recall on the
     modules this phase touches and report back the dependency map plus
     relevant prior context, before any implementation starts.
  2. Parallelize research: independent exploration/analysis tasks each go
     to their own subagent — one task per subagent — fed the scout's
     graphify output.
  3. Implement in the main thread: a single writer avoids file conflicts
     between agents.
  4. Review before close: a separate reviewer subagent independently
     verifies the phase — tests pass, the storyboard/walkthrough contract
     is met — before the phase is marked done.
- **State Management:** Before finishing, update CLAUDE.md: build
  commands, test commands, and current development state.
- **Tooling Protocol:** Primary runner is Claude Code — enter plan mode
  before implementing, per CLAUDE.md. For portability, when running
  outside Claude Code, load and execute this prompt via Caveman.

## Deliverables
Execute, not merely describe, the following against the actual codebase:

- **Riskiest-flow edge cases (no-auth substitute for login edge cases):**
  - Every route (`/weeks`, `/boundaries`, `/fire/*`, `/landslide/*`,
    `/alerts`, `/cells/*`, `/ingest-status`, `/reports/pdf`) confirmed
    reachable with zero credentials — confirm this is the *intended*
    posture (documented in CLAUDE.md as an internal-network-only
    deployment requirement), not an oversight.
  - Invalid `week`/`hazard`/`layer`/`spatial_id` values (SQL-meta
    characters, path-traversal sequences like `../`, empty/oversized
    strings) rejected with a 400, never reaching a raw SQL string or a
    filesystem path unsanitized.
  - `POST /reports/pdf` with an oversized or malformed
    `map_image_base64` payload fails cleanly (size cap + validation), does
    not crash the process or write outside `generated/`.
  - `generated/overlays/` static mount confirmed to serve only files
    inside that directory (no `..` traversal to arbitrary host paths).
- **Zero-trust checks:** server-side re-validation on every endpoint
  (never trust client-sent `week`/`hazard` without checking against real
  DB state); `.env` values (`DATABASE_URL`, `POSTGRES_*`) confirmed absent
  from the frontend build output; no over-fetching (API responses contain
  only documented fields, not raw DB rows); no secrets in log lines
  (Phase 11's structured logs checked for this); error responses to the
  client are opaque (`{"detail": "..."}`), full tracebacks server-log-only.
- **CORS:** locked to the configured frontend origin(s) only, per
  architecture.md §7 — confirm no wildcard `*` in the actual FastAPI CORS
  middleware config.
- Run the three audit prompts against the codebase and resolve or
  explicitly accept (with rationale recorded in CLAUDE.md) every finding:
  1. "Review my app as a security specialist and ensure I have strong
     security headers and a solid baseline security posture."
  2. "Review my app against OWASP standards and highlight vulnerabilities,
     specifically looking for SQL injection, XSS, and authentication
     flaws."
  3. "Check my app for credential or sensitive data leaks in frontend
     components or API routes."
- `scripts/run-phase-12.sh` — one-command launcher for manual eyeball
  checking (see below).

## Run Script (for manual checking — not an automated test)
Create `scripts/run-phase-12.sh`, executable, no arguments. It must:
- `docker compose up -d`, wait until all containers are healthy.
- Print a ready-to-paste list of the riskiest-flow `curl` commands from
  Deliverables above (malicious `week`/`spatial_id` values, an oversized
  `/reports/pdf` payload, a `../`-style overlay path) so the user can fire
  each one and read the response themselves.
It only starts the stack and prints the commands to try — it does NOT
assert pass/fail itself; the user reads each response and judges whether
it was rejected cleanly.

## Validation Verification
Before closing this phase, in order:
1. Run `/ponytail-review` on this phase's diff and resolve everything it
   flags (delete over-built code, simplify where the ladder says so).
2. Reviewer subagent sign-off (Multi-Agent Execution step 4).
3. Conclude by providing explicit manual testing steps for the newly
   generated code, plus the exact automated test command to run.
   - Manual: run `./scripts/run-phase-12.sh`, fire each printed `curl`
     command by hand and confirm each riskiest-flow case above is
     rejected cleanly.
4. Close with: **do not deploy to production until every vector above
   passes** — and until authentication is added, since v1 has none by
   design; document that constraint prominently in CLAUDE.md and any
   deployment notes.

Are you clear on these instructions? Please ask any clarifying questions
before we begin.
