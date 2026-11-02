# Design

## Context

See `proposal.md` for motivation and `specs/` for externally observable requirements. The API is a FastAPI application with current JWT/session authorization and local database adapters. `/health` is an existing liveness endpoint; OpenAPI is currently exposed by default. The demo runs one Uvicorn process and does not have a distributed cache or external monitoring service.

## Goals / Non-Goals

**Goals:** Implement the new behavior at the application/configuration boundaries while retaining existing route contracts, role checks, JWT validation, session revocation, and frontend in-memory token handling. Keep operational state local and bounded.

**Non-Goals:** Add distributed rate limiting, external telemetry or alerting, trust proxy headers, change account/session persistence, change appointment behavior, or make the demo suitable for real patient data.

## Decisions

1. **One explicit environment setting controls documentation.** Read `ODONTOLOGIA_ENTORNO` once when constructing the app. Only the exact value `desarrollo` enables Swagger, ReDoc, and OpenAPI; `produccion`, absent, or unrecognized values leave all three routes unregistered. This is fail-closed and keeps local interactive documentation available when deliberately requested. Do not infer the mode from debug flags, hostnames, or deployment context.

2. **Request identity and logging are handled at the ASGI boundary.** Validate inbound `X-Request-ID` as a UUID, normalize accepted values to canonical form, and otherwise generate a UUID. Store it in request scope/state and set it on every response, including handled errors. Emit one structured completion event from an allowlist; obtain the route template only from the matched route object and use a fixed unmatched marker when no route matched. Never use raw URL/path or request/response content to build the event. The catch-all handler returns a fixed public 500 code/message and must not log the exception object or traceback; configure application/server error paths so unexpected failures cannot bypass the safe response/log policy.

3. **Login throttling uses short atomic reservations.** Add a bounded in-memory limiter at the authentication service boundary, before expensive password verification. Its key is the observed socket peer address plus SHA-256 of the normalized account identifier; neither raw account nor address is persisted or logged. Under a short process-wide mutex, reserve at most five active checks per key so simultaneous requests cannot all pass before a failure is recorded. Release the mutex before scrypt or database work. Convert a reservation to a failure only after invalid credentials; release it without counting on validation/database/internal errors. A valid login clears confirmed failures while preserving other active reservations. Count confirmed failures in a rolling five-minute window; after five, return 429 with `Retry-After` until the earliest failure expires. Expire entries lazily per key, cap retained keys and evict the least recently used key at capacity; each key has at most five active marks, so no per-key locks or unbounded reservation table is required. Do not consult `X-Forwarded-*`. The current single-worker execution makes this an explicitly per-process control, not a distributed guarantee.

4. **Readiness performs a read-only probe without startup side effects.** Add public `GET /ready` separate from existing `/health`. Its database adapter path must issue only `SELECT 1` against the already selected database. It must not call schema initialization, migration, create-if-missing, or backup routines. For SQLite, opening readiness must not create a missing database file (use a read-only connection mode or detect absence before opening); other adapters must use their existing configured connection without schema changes. Return a stable 503 code on any unavailable/probe failure and do not include connection strings, credentials, or exception text. Keep `/health` independent of database status.

5. **Keep local operational failures safe and actionable.** Preserve nonzero exit status for explicit backup/restore failures and provide a stable failure code at the CLI boundary. Do not print connection URLs, secrets, private paths, raw exception detail, or process output that could contain them. Keep database/backup checks local; no external telemetry dependency is needed.

6. **Retain existing bounded API inputs and authentication contracts.** Reuse the current request validation, query limits, pagination constraints, auth service, and stable domain error conventions. Add focused tests around the boundary behavior rather than changing schemas or roles. No new runtime dependency is required.

## Risks / Trade-offs

- **[A burst of more than five simultaneous logins for one key may receive 429 before outcomes finish]** → Keep `Retry-After` short while a reservation is pending, then let the client retry; successful logins clear confirmed failures.
- **[Process restart or multiple workers resets/splits login counters]** → Document the current one-process scope and do not claim distributed protection; a future multi-worker deployment requires a separately planned shared limiter.
- **[An untrusted proxy address could weaken source grouping]** → Use only the direct connection peer and do not trust forwarded headers; a future trusted-proxy topology needs explicit proxy allowlisting.
- **[Readiness accidentally initializes a missing SQLite database]** → Use a read-only probe path and test that querying readiness does not create a file or schema.
- **[Framework/server logs could emit details outside the application logger]** → Exercise unhandled failures through the ASGI app and configure relevant server loggers to preserve the allowlist and omit exception tracebacks.
- **[A configuration typo disables documentation unexpectedly]** → Keep the mode values explicit, document the local development setting, and verify absent/unknown values fail closed.

## Migration Plan

1. Add/update automated tests for request ID handling, allowlisted logs, generic 500, limiter behavior, readiness, and environment-dependent documentation.
2. Implement the middleware, error response, limiter, read-only readiness probe, and configuration wiring; preserve current `/health` behavior.
3. Update local environment/Compose documentation to set `ODONTOLOGIA_ENTORNO=desarrollo` where local Swagger is desired. Production configuration must set `produccion`; omission remains fail-closed.
4. Run the relevant tests and full backend suite. Rollback consists of reverting this change; no persistent data migration is introduced.

## Open Questions

None. The rate limit is deliberately process-local for the current single-process demo; scaling beyond that is out of scope for this change.
