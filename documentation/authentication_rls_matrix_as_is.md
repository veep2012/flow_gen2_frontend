# Authentication and RLS matrix (as-is)

## Document Control
- Status: Review
- Owner: Backend and Database Team
- Reviewers: Security and API maintainers
- Created: 2026-02-25
- Last Updated: 2026-02-27
- Version: v0.5

## Change Log
- 2026-02-27 | v0.5 | Revision mutation endpoints (`status transition`, `cancel`) now build response payloads from workflow function return rows (plus lookup enrichments) instead of re-reading through scope-filtered revision views, preventing false `Revision not found` after successful writes.
- 2026-02-27 | v0.4 | Corrected `ref.sync_user_primary_role()` behavior: mirror insert from `ref.users.role_id` is non-destructive and preserves existing secondary `ref.user_roles` assignments; added one `EXPLAIN (ANALYZE, BUFFERS)` read-path baseline for `workflow.v_documents` with RLS predicate active.
- 2026-02-26 | v0.3 | Updated as-is snapshot for Phase 1: documented implemented `workflow.check_user_permission(...)`, read-side RLS policies, project-scoped lookup behavior, and fail-closed outcomes.
- 2026-02-25 | v0.1 | Initial as-is snapshot of implemented authentication and authorization-related schema/session behavior.

## Purpose
Describe the currently implemented authentication/authorization-related behavior through Phase 1 read-path enforcement, including what is active now and what is still pending.

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
  - `X-User-Id` request header.
  - `APP_USER` environment variable.
- Header/env identifier format:
  - `user_acronym` only.
  - resolved identifier is converted to internal `user_id` before session set.
- API writes both DB session keys:
  - `app.user` (legacy/currently used by triggers/functions).
  - `app.user_id` (forward-compatible key for target model).
  - Both keys are set at session scope, so they remain available after endpoint-level `COMMIT` statements inside the same request.
- `APP_USER` is environment-gated:
  - Allowed only for `local/dev/development/test/testing/ci/ci_test`.
  - Startup fails when `APP_USER` is set in blocked/unknown environments.
  - Startup validates that `APP_USER` resolves to a row in `workflow.v_users`.

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
- Scenario source of truth:
  - `documentation/test_scenarios/authorization_read_rls_api_test_scenarios.md`
- Automated tests:
  - `tests/api/api/test_authorization_read_rls.py`

### Read-path performance sample (observed)
- Context:
  - Local seeded test database (`make test-db-up`, PostgreSQL 18.1 image).
  - Session context set to non-super user: `set_config('app.user_id', '3', false)`.
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
- Mixed legacy/new superuser checks:
  - `workflow.is_superuser(...)` accepts both `is_super=true` and legacy role-name matching.

## References
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
