# Dependency Maintenance Notes

A running log of dependency warnings observed during testing. **Do not upgrade
any dependency without first checking compatibility** (pin changes must be
verified against the full backend test suite).

## Known deprecation warnings (as of Task 1.2)

These originate from the **test tooling** (Starlette `TestClient` / httpx), not
from KHABARDAR application code. They do not affect runtime behavior and are
non-blocking. Recorded here for future maintenance.

| # | Source | Warning | Trigger | Action |
|---|--------|---------|---------|--------|
| 1 | `starlette/testclient.py:41` | `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.` | Importing/using `fastapi.testclient.TestClient` | None now. Resolves when Starlette updates the alias internally; revisit on a vetted Starlette bump. |
| 2 | `httpx/_client.py:680` | `DeprecationWarning: The 'app' shortcut is now deprecated. Use the explicit style 'transport=WSGITransport(app=...)' instead.` | `TestClient(app)` passes `app=` to httpx | None now. Internal to Starlette's TestClient; will be fixed upstream. Test-only. |
| 3 | `httpx/_content.py:202` | `DeprecationWarning: Use 'content=<...>' to upload raw bytes/text content.` | `test_malformed_json_body` posts a raw string via `data=` | Low priority test-only; could switch the test to `content=` later. Does not affect app code. |

### Current pinned versions (reference)

- fastapi 0.110.0, starlette 0.36.3 (pulled by fastapi), httpx 0.27.0,
  anyio 4.16.0, pydantic 2.6.4, uvicorn 0.29.0.

### Compatibility caution

- `fastapi==0.110.0` constrains `starlette>=0.36.3,<0.37.0`. Any Starlette bump
  must stay within FastAPI's supported range or FastAPI must be bumped in lockstep.
- Upgrading httpx/anyio may change TestClient internals; re-run the full suite
  (`pytest`) after any change.

## Property 13 (input preservation) — Phase 2 follow-up

Task 1.3 added a **contract-level / property-harness** test for Property 13
(`backend/tests/properties/test_property_13_input_preserved.py`).

Scope as of Task 1.3:
- The **error-envelope** half runs through REAL production code
  (`register_exception_handlers`, `AppError`, `envelope.success`) and the real
  middleware chain.
- The **input/state-preservation** half is a contract harness: the "safe"
  commit-on-success operation is implemented **in the test fixture**, because
  KHABARDAR has **no production state-mutating component yet** (no
  `services/`, `repositories/`, `db/`, `models/` — persistence is Phase 2).
- A non-vacuity guard (`test_property_13_assertion_is_not_vacuous`) proves the
  preservation assertion fails against a mutate-before-fail implementation.

**REQUIRED in Phase 2:** when real write operations exist (e.g. `ScanHistory`
persistence, task 2.x), extend Property 13 to exercise the ACTUAL production
service/repository and assert persisted/server-side state is preserved on
failure, using a real DB transaction rollback or equivalent. Until then, this
test must NOT be presented as verification of production operation atomicity.

## Frontend npm audit (as of Task 1.4)

First `npm install` of the frontend reported **7 vulnerabilities (4 moderate, 1
high, 2 critical)**, all in transitive dev-tooling or later-task deps. No fix
was applied because every fix requires a breaking major upgrade, which the
Task 1.4 constraints forbid (no silent upgrades/replacements).

- **esbuild <=0.24.2** (moderate) -> pulled by vite/vite-node/vitest. The
  advisory (GHSA-67mh-4wv8-2f99) concerns the esbuild **dev server**; the
  documented production build uses `vite build` and does not expose it. Fix
  would require `vite@8` (breaking).
- **react-router / react-router-dom** (moderate) -> a LATER-task dependency
  (routing, task 1.7+); not imported or used in Task 1.4. Fix would require
  `react-router-dom@7` (breaking).
- **tinypool** (critical, via vitest) -> test runner transitive; dev-only.

ACTION: deferred. Revisit when the planned stack is intentionally bumped, with a
full test + build re-run. Do not run `npm audit fix --force` (breaks pinned
versions).
