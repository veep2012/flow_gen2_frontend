# Authentication and RLS matrix (as-is)

## Document Control
- Status: Review
- Owner: Backend and Database Team
- Reviewers: Security and API maintainers
- Created: 2026-02-25
- Last Updated: 2026-03-18
- Version: v1.7

## Change Log
- 2026-03-18 | v1.7 | Linked the current implemented auth/RLS snapshot to `application_authorization_policy.md` so implementation reviews can compare current enforcement with the authoritative business policy.
- 2026-03-07 | v1.6 | Added API-verified bearer JWT identity resolution ahead of trusted-header and `X-User-Id` fallbacks, documented JWT verification inputs and failure telemetry, clarified that JWKS client/fetch failures fail closed as `401` with `jwks_fetch_failed` observability, and restricted raw `X-User-Id` fallback to non-production environments while updating the startup identity banner accordingly.
- 2026-03-06 | v1.3 | Made trusted identity header resolution authoritative over `X-User-Id`, documented fail-closed behavior when the trusted header is unresolved, and synchronized compose/nginx trusted-header forwarding expectations.
- 2026-03-05 | v1.2 | Implemented trusted identity header mode (`X-Auth-User`) with fail-closed unknown-identity behavior, clarified that `ref.roles.external_name` is reference-only for a dedicated identity-sync module rather than a request-path/workflow authorization input, and documented current identity-header precedence limitation (`X-User-Id` evaluated before trusted header) with required proxy stripping/rewriting controls in non-local environments.
- 2026-02-27 | v0.5 | Corrected `ref.sync_user_primary_role()` behavior so mirror inserts from `ref.users.role_id` are non-destructive and preserve existing secondary `ref.user_roles` assignments, added one `EXPLAIN (ANALYZE, BUFFERS)` read-path baseline for `workflow.v_documents` with the RLS predicate active, and documented that revision mutation endpoints (`status transition`, `cancel`) now build response payloads from workflow function return rows (plus lookup enrichments) instead of re-reading through scope-filtered revision views, preventing false `Revision not found` after successful writes.
- 2026-02-26 | v0.3 | Updated as-is snapshot for Phase 1: documented implemented `workflow.check_user_permission(...)`, read-side RLS policies, project-scoped lookup behavior, and fail-closed outcomes.
- 2026-02-25 | v0.1 | Initial as-is snapshot of implemented authentication and authorization-related schema/session behavior.

## Purpose
Describe the currently implemented authentication/authorization-related behavior through Phase 1 read-path enforcement, including what is active now and what is still pending.

Comparison rule:
- `documentation/application_authorization_policy.md` is the business-policy source of truth.
- This document records the currently implemented authentication and authorization enforcement state, including temporary gaps or partial rollout phases.

## Scope
- In scope:
  - Implemented session user resolution and DB session context behavior.
  - Implemented reference schema foundation for role-based authorization.
  - Implemented read authorization predicate and read-side RLS policies.
  - Current superuser resolution behavior used by workflow functions.
  - Implemented scoped lookup behavior for projects.
- Out of scope:
  - Write-path (`read-write`) enforcement for capability/scope model.
  - Future-state rollout phases beyond currently implemented behavior.
  - Full OIDC/Keycloak runtime integration details.
  - Non-auth workflow invariants unrelated to authorization.

## Design / Behavior
Current implementation is a hybrid state: role-model foundations are active, and Phase 1 read authorization is enforced for document lineage resources.

### Session user context (implemented)
- API resolves acting user in this order:
  - Verified bearer JWT from `Authorization: Bearer <token>`.
  - Trusted identity header (`X-Auth-User`, configurable via `TRUSTED_IDENTITY_HEADER`).
  - `X-User-Id` request header only when the trusted header is absent or empty and the app environment is `local/dev/development/test/testing/ci/ci_test`.
  - `APP_USER` environment variable.
- Bearer JWT verification:
  - API validates signature, issuer, audience, expiry, and configured algorithms before resolving internal identity.
  - Verification uses either `AUTH_JWT_SHARED_SECRET` or JWKS discovery/override via `AUTH_JWT_JWKS_URL`.
  - Identity claim lookup is configurable through `AUTH_JWT_IDENTITY_CLAIMS` and defaults to `acronym`, `preferred_username`, then `sub`.
- Bearer-token precedence:
  - When `Authorization: Bearer ...` is present, bearer-token validation is authoritative.
  - If bearer-token validation fails, the request fails closed with `401 Unauthorized` and does not fall back to trusted-header or `X-User-Id`.
- Trusted-header precedence:
  - When both headers are present, trusted identity header resolution is authoritative.
  - If the trusted identity header is present but unresolved, the request fails closed with `401 Unauthorized` and does not fall back to `X-User-Id`.
  - In non-local environments, safe operation requires proxy/network controls that strip inbound identity headers from clients and set canonical trusted identity headers after OIDC validation.
- Production-capable environments do not honor inbound `X-User-Id`:
  - `prod/production/stage/staging` ignore `X-User-Id` entirely for request identity resolution.
  - This prevents raw client-controlled header fallback if the API becomes directly reachable or edge stripping is misconfigured.
- Header/env identifier format:
  - `user_acronym` only.
  - resolved identifier is converted to internal `user_id` before session set.
- Trusted role mapping:
  - `ref.roles.external_name` exists as reference key for dedicated LDAP/IdP synchronization tooling.
  - Request/workflow authorization paths do not evaluate `external_name` directly.
  - Runtime role reconciliation is intentionally delegated to a dedicated sync module and is outside current request execution flow.
- API writes both DB session keys:
  - `app.user` (legacy/currently used by triggers/functions).
  - `app.user_id` (forward-compatible key for target model).
  - Both keys are set with transaction-local scope (`set_config(..., true)`), not pooled-connection session scope.
  - Resolved identity is stored on the SQLAlchemy request session and re-applied automatically on every transaction begin.
  - This preserves identity after endpoint-level `COMMIT` / `ROLLBACK` while preventing connection-pool bleed between requests.
  - When no identity is present, both keys are explicitly set to empty strings for the transaction so stale session-level residue cannot survive checkout reuse.
- `APP_USER` is environment-gated:
  - Allowed only for `local/dev/development/test/testing/ci/ci_test`.
  - Startup fails when `APP_USER` is set in blocked/unknown environments.
  - Explicitly, `APP_ENV=production` + `APP_USER` is a startup error.
  - `APP_USER` must match `^[A-Z]{2,12}$`.
  - Startup validates that `APP_USER` resolves to a row in `workflow.v_users`.
- Startup emits a banner describing active identity mode:
  - `startup_identity_mode=request_header_only identity_source=Authorization>X-Auth-User>X-User-Id` when `APP_USER` is not configured and non-production raw header fallback is enabled.
  - `startup_identity_mode=request_header_only identity_source=Authorization>X-Auth-User` when `APP_USER` is not configured in production-capable environments.
  - `startup_identity_mode=app_user_bootstrap` when `APP_USER` bootstrap is active.
- API-layer fail-closed guard is active for auth-sensitive routers:
  - `documents`
  - `files`
  - `files_commented`
  - `written_comments`
  - `notifications`
  - `distribution_lists`
  - Requests without effective session identity return `401 Unauthorized` instead of running with an anonymous DB session.
- Missing-identity denials are logged as security events with:
  - `X-Request-Id`
  - HTTP method
  - request path
  - no user acronym, token, cookie, or other PII
- Structured auth-event logs now carry:
  - `event`
  - `request_id`
  - `auth_mode`
  - `method`
  - `path`
  - event-specific non-PII fields such as `reason`, `status_code`, or `header_name`
- Current-user endpoint contract is explicit:
  - `GET /api/v1/people/users/current_user` returns `401` when no effective session identity exists.
  - The same endpoint returns `404` when identity exists but no current-user row resolves from the read model.
  - This `404` includes hidden/filtered and deprovisioned/inactive user states.

### Auth observability (implemented)
- `GET /metrics` exposes in-process counters in Prometheus text format.
- Current auth counters:
  - `flow_auth_current_user_resolution_failures_total{reason=missing_identity|unresolved_read_model}`
  - `flow_auth_denied_by_rls_total{endpoint=...,status_code=...,auth_mode=...}`
  - `flow_auth_identity_header_parse_failures_total{auth_mode=...}`
  - `flow_auth_jwt_validation_failures_total{reason=...}`
- JWKS URL fetch failures, JWKS client parsing failures, and equivalent bearer-token key-resolution failures must fail closed with `401` and increment `flow_auth_jwt_validation_failures_total{reason="jwks_fetch_failed"}`.
- `flow_auth_denied_by_rls_total` counts observable API-layer auth denials:
  - explicit `403` responses on auth-sensitive endpoints
  - `404` on `GET /api/v1/people/users/current_user` when an authenticated identity is filtered/unresolved
- Silent read filtering that returns `200` with an empty list remains intentionally out of metric scope because the API cannot distinguish that from “no matching rows” without changing endpoint contracts.

### Role model foundation (implemented)
- `ref.roles` now includes:
  - `role_name` (legacy/current)
  - `role_code` (new stable internal code)
  - `external_name` (new IdP/group mapping key)
  - `is_super` (new super-role marker)
- New tables exist:
  - `ref.user_roles`
  - `ref.role_permissions`
  - `ref.role_scopes`
- New constraints enforce allowed values:
  - `role_permissions.resource` in `doc`, `doc_revision`, `files`, `files_commented`
  - `role_permissions.capability` in `read-only`, `read-write`
  - `role_scopes.scope_type` in `PROJECT`, `AREA`, `UNIT`
- Required lookup indexes for these new tables are implemented.

### Compatibility behavior (implemented)
- `ref.users.role_id` is still present and used by existing API and ORM contracts.
- Trigger `ref.sync_user_primary_role()` mirrors `ref.users.role_id` into `ref.user_roles` with `INSERT ... ON CONFLICT DO NOTHING` (non-destructive sync).
- `workflow.is_superuser(...)` now checks:
  - new bridge path (`ref.user_roles` + `ref.roles.is_super`), and
  - legacy path (`ref.users.role_id` + role-name fallback).
- New read-only views are exposed:
  - `workflow.v_user_roles`
  - `workflow.v_role_permissions`
  - `workflow.v_role_scopes`

### Read authorization predicate (implemented)
- `workflow.check_user_permission(...)` is implemented and marked `STABLE`.
- Resource values currently supported:
  - `doc`
  - `doc_revision`
  - `files`
  - `files_commented`
- Capability values currently supported:
  - `read-only`
  - `read-write`
- Capability normalization is active:
  - `read-only` request accepts grants `read-only` or `read-write`.
  - `read-write` request accepts grant `read-write` only.
- Scope evaluation in this phase is project-based:
  - Non-super users are matched through `ref.role_scopes` rows where `scope_type='PROJECT'`.
  - Only `PROJECT` scope assignments are part of the supported Phase 1 operating model.
  - `AREA` and `UNIT` scope types exist in schema as forward-looking shape only and are excluded from current deployment/seed usage.
  - If unsupported `AREA` or `UNIT` scope rows are assigned anyway, read authorization fails closed in Phase 1.
  - `logic_group` is evaluated per role/group boundary in predicate grouping.
  - If no matching scope groups exist, access is denied (fail-closed).
- Super-role shortcut is active:
  - If any assigned role has `is_super=true`, scope checks are bypassed after capability check passes.
- Fail-closed rules are active:
  - Unknown/invalid user, invalid resource/capability, unresolved `p_doc_id`, missing roles, or missing capability grants return `false`.

### Read-side enforcement surfaces (implemented)
- RLS `USING` policies are active for:
  - `core.doc`
  - `core.doc_revision` (inherits via `doc_id`)
  - `core.files` (inherits via `rev_id -> doc_revision.doc_id`)
  - `core.files_commented` (inherits via `file_id -> files.rev_id -> doc_revision.doc_id`)
- Read-side workflow views call the predicate:
  - `workflow.v_documents`
  - `workflow.v_document_revisions`
  - `workflow.v_files`
  - `workflow.v_files_commented`

### Write endpoint response behavior (implemented)
- Revision mutation handlers for transition/cancel return the mutated revision from workflow function outputs and then enrich lookup names (`revision_overview`, `milestones`, `statuses`).
- This avoids coupling write success responses to read-scope view visibility and prevents false 404 responses (`Revision not found`) after a successful mutation.

### Lookup scope behavior (implemented)
- Project lookup is scope-filtered:
  - `workflow.v_projects` uses `workflow.check_lookup_scope_permission(...)` with `scope_type='PROJECT'`.
- `areas` and `units` are not scope-filtered in this phase:
  - `workflow.v_areas` and `workflow.v_units` remain unfiltered lookup views.
- `AREA` and `UNIT` entries in `ref.role_scopes` are out of current supported scope:
  - they are reserved for later phases and must not be treated as active read-path authorization inputs in Phase 1 operations/documentation.
- `workflow.check_lookup_scope_permission(...)` is fail-closed for invalid/unknown context and non-super users without matching scope rows.

### Seed baseline (implemented)
- Baseline roles are seeded with stable codes:
  - `SUPERUSER`, `DCC_USER`, `AUTHOR`, `REVIEWER`
- Baseline capability matrix is seeded in `ref.role_permissions` for:
  - `doc`, `doc_revision`, `files`, `files_commented`
- `ref.user_roles` is seeded for current seeded users.

### Integration test coverage (implemented)
- Multi-role union read behavior is covered.
- Missing/unknown session user fail-closed behavior is covered.
- Predicate fail-closed behavior for invalid inputs is covered.
- Rapid alternating-user API requests are covered to assert no cross-user identity leakage through pooled connections.
- Scenario source of truth:
  - `documentation/test_scenarios/authorization_read_rls_api_test_scenarios.md`
- Automated tests:
  - `tests/api/api/test_authorization_read_rls.py`

### Read-path performance sample (observed)
- Context:
  - Local seeded test database (`make test-db-up`, PostgreSQL 18.1 image).
  - Transaction context set to non-super user: `set_config('app.user_id', '3', true)`.
  - Query:
    - `EXPLAIN (ANALYZE, BUFFERS) SELECT doc_id, project_id, title FROM workflow.v_documents ORDER BY doc_id LIMIT 25;`
- Observed plan summary:
  - `Index Scan using doc_pkey on doc`
  - Filter includes `workflow.check_user_permission(...)` RLS predicate.
  - Buffers: `shared hit=864 read=4`
  - Planning time: `0.522 ms`
  - Execution time: `2.540 ms`

## Edge Cases
- `APP_USER` set in production/staging:
  - API startup must fail closed.
- `APP_USER` configured with numeric id:
  - API startup must fail because only `user_acronym` is accepted.
- `APP_USER` configured but user does not exist in `workflow.v_users`:
  - API startup must fail closed.
- User-role divergence risk:
  - `ref.sync_user_primary_role()` adds/ensures the primary role binding from `ref.users.role_id`; it does not remove secondary `ref.user_roles` assignments. Divergence can still occur if external role management does not keep legacy `ref.users.role_id` aligned with intended primary role.
- Scope rows absent for non-super user:
  - Current implementation denies reads (fail-closed), because no scope-group match exists.
- `AREA`/`UNIT` role scopes assigned during Phase 1:
  - This is outside the supported operating model. Phase 1 documentation, seeds, and tests assume only `PROJECT` scope assignments are active.
- Mixed legacy/new superuser checks:
  - `workflow.is_superuser(...)` accepts both `is_super=true` and legacy role-name matching.

## References
- `documentation/application_authorization_policy.md`
- `documentation/authorization_rls_matrix.md`
- `documentation/auth_architecture.md`
- `documentation/api_interfaces.md`
- `documentation/test_scenarios/authorization_read_rls_api_test_scenarios.md`
- `ci/init/02_ref.sql`
- `ci/init/07_workflow.sql`
- `ci/init/08_views.sql`
- `ci/init/09_security.sql`
- `ci/init/flow_seed.sql`
- `api/utils/database.py`
