# Authentication and RLS matrix (as-is)

## Document Control
- Status: Review
- Owner: Backend and Database Team
- Reviewers: Security and API maintainers
- Created: 2026-02-25
- Last Updated: 2026-02-25
- Version: v0.1

## Change Log
- 2026-02-25 | v0.1 | Initial as-is snapshot of implemented authentication and authorization-related schema/session behavior.

## Purpose
Describe the currently implemented authentication/authorization-related behavior as of Phase 0 foundation work, including what is already in place and what is not yet enforced.

## Scope
- In scope:
  - Implemented session user resolution and DB session context behavior.
  - Implemented reference schema foundation for role-based authorization.
  - Current superuser resolution behavior used by workflow functions.
- Out of scope:
  - Future-state RLS policy model described in `authorization_rls_matrix.md`.
  - Full OIDC/Keycloak runtime integration details.
  - Non-auth workflow invariants unrelated to authorization.

## Design / Behavior
Current implementation is a hybrid state: legacy behavior remains active, and new Phase 0 role-model foundations are introduced.

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
- `APP_USER` is environment-gated:
  - Allowed only for `local/dev/development/test/testing/ci/ci_test`.
  - Startup fails when `APP_USER` is set in blocked/unknown environments.
  - Startup validates that `APP_USER` resolves to a row in `workflow.users`.

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
- Trigger `ref.sync_user_primary_role()` keeps `ref.user_roles` synchronized with `ref.users.role_id`.
- `workflow.is_superuser(...)` now checks:
  - new bridge path (`ref.user_roles` + `ref.roles.is_super`), and
  - legacy path (`ref.users.role_id` + role-name fallback).
- New read-only views are exposed:
  - `workflow.user_roles`
  - `workflow.role_permissions`
  - `workflow.role_scopes`

### Seed baseline (implemented)
- Baseline roles are seeded with stable codes:
  - `SUPERUSER`, `DCC_USER`, `AUTHOR`, `REVIEWER`
- Baseline capability matrix is seeded in `ref.role_permissions` for:
  - `doc`, `doc_revision`, `files`, `files_commented`
- `ref.user_roles` is seeded for current seeded users.

### RLS status (as-is)
- Authorization-specific RLS policies from the future matrix are not implemented yet.
- Existing policy/triggers currently enforce workflow invariants (revision lifecycle rules), not the future capability + scope authorization model.
- Single predicate `workflow.check_user_permission(...)` is not implemented yet.

## Edge Cases
- `APP_USER` set in production/staging:
  - API startup must fail closed.
- `APP_USER` configured with numeric id:
  - API startup must fail because only `user_acronym` is accepted.
- `APP_USER` configured but user does not exist in `workflow.users`:
  - API startup must fail closed.
- User-role divergence risk:
  - `ref.sync_user_primary_role()` currently rewrites `ref.user_roles` from `ref.users.role_id`; multi-role semantics are not active yet.
- Mixed legacy/new superuser checks:
  - `workflow.is_superuser(...)` accepts both `is_super=true` and legacy role-name matching.

## References
- `documentation/authorization_rls_matrix.md`
- `documentation/auth_architecture.md`
- `documentation/api_interfaces.md`
- `ci/init/02_ref.sql`
- `ci/init/07_workflow.sql`
- `ci/init/08_views.sql`
- `ci/init/flow_seed.sql`
- `api/utils/database.py`
