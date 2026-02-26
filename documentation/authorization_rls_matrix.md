# Authorization and RLS matrix

## Document Control
- Status: Review
- Owner: Backend and Database Team
- Reviewers: Security and API maintainers
- Created: 2026-02-21
- Last Updated: 2026-02-26
- Version: v0.6

## Change Log
- 2026-02-26 | v0.6 | Updated Phase 0 reality notes: `APP_USER`/`X-User-Id` now resolve by `user_acronym`; documented controlled runtime behavior changes and rollout expectations.
- 2026-02-25 | v0.5 | Added architecture review summary, gradual implementation plan, edge cases, and references.
- 2026-02-21 | v0.4 | Added local developer mode using `APP_USER` to bootstrap `app.user_id` with strict non-production guardrails.

## Purpose
Define the future-state role-based authorization and row-level security (RLS) model for Flow.

## Scope
- In scope:
  - Authorization model (capability + scope) and RLS behavior.
  - Target schema and policy structure for role-driven enforcement.
  - Role superposition and super-role behavior.
- Out of scope:
  - Full OIDC/Keycloak operational setup details.
  - UI implementation details.
  - SQL migration scripts.

## Audience
- Backend and database engineers
- Security reviewers
- API maintainers
- QA and release engineers

## Definitions
- Capability: Allowed action level for a resource (`read-only`, `read-write`).
- Scope: Allowed data slice boundaries (`PROJECT`, `AREA`, `UNIT`) with grouped AND/OR logic.
- Super-role: Role with `is_super = true`; bypasses scope checks but still requires valid capability.
- RLS: PostgreSQL Row-Level Security policies that enforce row visibility and write eligibility.
- Session context: Per-request DB settings used by authorization predicates (for example `app.user_id`).

## Design / Behavior
The target model is role-driven authorization with database-enforced row filtering:
- Identity is external (OIDC/Keycloak).
- Application sets DB session context for authorization decisions.
- PostgreSQL enforces data access isolation via RLS.
- Capability (what action) and scope (which rows) are independent and combined.

### Target authorization dimensions
- Capability:
  - Role capability is limited to:
    - `read-only`
    - `read-write`
  - Capability applies per resource (`doc`, `doc_revision`, `files`, `files_commented`).
- Scope:
  - Role is limited to data slices by project/area/unit, with grouped AND/OR logic.

### Session context contract (target)
- Required:
  - `app.user_id`
- Optional:
  - `app.role_code` (debug/trace only; not authoritative for permission decisions)
  - `app.tenant_id` (if multi-tenant is introduced)

### Local developer mode (proposed)
For local development only, application may bootstrap session context from environment variable `APP_USER`.

Contract:
- `APP_USER` contains `user_acronym`.
- API startup/request middleware validates that `APP_USER` resolves in `ref.users`.
- Middleware sets DB session:
  - `set_config('app.user_id', '<resolved_user_id>', true)`
- If `APP_USER` is missing or unresolved:
  - fail closed (`401`/`403`) by default, or
  - allow explicit fallback to predefined local user only when `APP_ENV=local`.

Restrictions:
- `APP_USER` mode must be disabled outside local environment.
- Production/stage must use trusted identity headers/JWT mapping only.
- `APP_USER` must never bypass `workflow.check_user_permission(...)` or RLS.

Example (application side pseudocode):

```text
if APP_ENV == "local" and APP_USER is set:
    v_user_id = resolve APP_USER by ref.users.user_acronym
    assert v_user_id is not null
    set local app.user_id = v_user_id
else:
    user_id = resolve from trusted auth context
    set local app.user_id = user_id
```

### RLS target behavior (conceptual)
- If role is super-role, scope checks are bypassed.
- Otherwise:
  - capability must be permitted by capability matrix.
  - row must satisfy at least one scope logic group.
- Related tables inherit scope via document lineage:
  - `doc_revision.doc_id`
  - `files.rev_id -> doc_revision.doc_id`
  - `files_commented.file_id -> files.id -> files.rev_id -> doc_revision.doc_id`

### Workflow permission-check helper (proposed)
To keep workflow functions explicit and predictable, introduce a single DB helper:

```sql
workflow.check_user_permission(
    p_user_id bigint,
    p_resource text,
    p_capability text,
    p_doc_id bigint default null,
    p_project_id bigint default null,
    p_area_id bigint default null,
    p_unit_id bigint default null
) returns boolean
```

Behavior:
- Resolves all roles for `p_user_id` via `ref.user_roles`.
- Computes effective capability as union across assigned roles via `ref.role_permissions`.
- Applies super-role shortcut when any assigned role has `ref.roles.is_super = true`.
- If not super-role, evaluates scope groups from `ref.role_scopes` against:
  - explicit entity arguments (`p_project_id`, `p_area_id`, `p_unit_id`), or
  - resolved document scope when `p_doc_id` is provided.
- Returns `true` when access is allowed, else `false`.

Fail-closed rules:
- Unknown user, no roles, invalid capability, or unresolved document must return `false`.
- Workflow wrapper functions may convert `false` to `403` (for API) or explicit DB exception.

Capability normalization rule:
- If `p_capability = 'read-only'`, only `read-only` and `read-write` grants satisfy it.
- If `p_capability = 'read-write'`, only `read-write` grants satisfy it.

## Target data model
- `ref.roles`
  - `role_id` (PK)
  - `role_name`
  - `external_name` (unique external role/group key for AD/IdP mapping)
  - `role_code` (unique stable internal code)
  - `is_super` (boolean, default false)
- `ref.user_roles`
  - `(user_id, role_id)` bridge table for many-to-many user-role assignment.
  - PK/unique on `(user_id, role_id)`.
- `ref.role_permissions`
  - `(role_id, resource, capability)` PK/unique.
- `ref.role_scopes`
  - `(role_id, scope_type, entity_id, logic_group)` and indexes for lookup.
### Multi-role superposition rule (target)
- A user may have multiple roles.
- Effective capability is the union of capabilities granted by all assigned roles.
- Effective scope is the union of scope groups across all assigned roles.
- If any assigned role has `is_super = TRUE`, scope restrictions are bypassed for that user.

### Example integration with workflow functions
Example: read check before listing document revisions

```sql
if not workflow.check_user_permission(
    current_setting('app.user_id', true)::bigint,
    'doc_revision',
    'read-only',
    p_doc_id => p_doc_id
) then
    raise exception 'Forbidden' using errcode = '42501';
end if;
```

Example: write check before creating revision/file updates

```sql
if not workflow.check_user_permission(
    current_setting('app.user_id', true)::bigint,
    'doc_revision',
    'read-write',
    p_doc_id => p_doc_id
) then
    raise exception 'Forbidden' using errcode = '42501';
end if;
```

Example: create-document precheck when doc row does not yet exist

```sql
if not workflow.check_user_permission(
    current_setting('app.user_id', true)::bigint,
    'doc',
    'read-write',
    p_project_id => p_project_id,
    p_area_id => p_area_id,
    p_unit_id => p_unit_id
) then
    raise exception 'Forbidden' using errcode = '42501';
end if;
```

### Example integration with RLS policies
`core.doc` policy sketch:

```sql
using (
  workflow.check_user_permission(
    current_setting('app.user_id', true)::bigint,
    'doc',
    'read-only',
    doc_id
  )
)
```

`core.doc` write policy sketch:

```sql
with check (
  workflow.check_user_permission(
    current_setting('app.user_id', true)::bigint,
    'doc',
    'read-write',
    doc_id
  )
)
```

Guideline:
- Keep this function as the single authorization predicate to avoid drift between workflow code and RLS policies.

## Proposed matrix baseline (initial draft)

### Capability baseline
| Role code | doc | doc_revision | files | files_commented |
| --- | --- | --- | --- | --- |
| `SUPERUSER` | read-write | read-write | read-write | read-write |
| `DCC_USER` | read-write | read-write | read-write | read-write |
| `AUTHOR` | read-write | read-write | read-write | read-write |
| `REVIEWER` | read-only | read-only | read-only | read-only |

Note:
- This table is a baseline and must be finalized by business policy.

### Scope baseline
- Scope types expected in v1:
  - `PROJECT`
  - `AREA`
  - `UNIT`
- Group evaluation:
  - same `logic_group` => AND
  - different `logic_group` => OR

## Performance considerations
- Required indexes for target model:
  - `ref.roles(role_code)`
  - `ref.roles(external_name)`
  - `ref.user_roles(user_id, role_id)`
  - `ref.role_permissions(role_id, resource, capability)`
  - `ref.role_scopes(role_id, scope_type, entity_id, logic_group)`
- Policy predicates should rely on indexed document scope fields:
  - `core.doc(project_id, area_id, unit_id)` (composite or targeted indexes as needed).

## Requirements
### Functional Requirements
- FR-1: All authorization decisions must be role-driven through `user_roles`, `role_permissions`, and `role_scopes`.
- FR-2: Capability levels must be limited to `read-only` and `read-write`.
- FR-3: RLS policies must enforce scope on `core.doc` and inherited scope on `doc_revision`, `files`, and `files_commented`.
- FR-4: Super-role behavior must be explicit through `roles.is_super`.
- FR-5: Workflow mutations and sensitive reads must call `workflow.check_user_permission(...)` before business logic execution.
- FR-6: RLS policy predicates should reuse `workflow.check_user_permission(...)` to keep authorization semantics consistent.
- FR-7: Local developer mode may use `APP_USER` only to set `app.user_id`, without bypassing permission checks.

### Non-Functional Requirements
- NFR-1: Missing or invalid session role context must fail closed.
- NFR-2: Authorization policy evaluation must be index-supported on role/scope tables and document scope fields.
- NFR-3: Authorization and workflow business logic must stay separated.
- NFR-4: Permission-check function should be `STABLE` and optimized to avoid repeated expensive joins in hot query paths.
- NFR-5: `APP_USER` local mode must be environment-gated and impossible to enable in production deployments.

## Architecture review summary
This architecture is directionally strong and aligned with least-privilege and fail-closed design. It correctly separates identity resolution (application side) from authorization enforcement (database side), and proposes one authorization predicate for both workflow checks and RLS policies, which should reduce drift.

Primary strengths:
- Single permission-check contract centralizes authorization semantics.
- Capability and scope are independent and composable.
- Super-role behavior is explicit and auditable (`is_super`).
- Local `APP_USER` mode is explicitly constrained to local-only usage.

Gaps to resolve before implementation:
- Ownership for authoritative role assignment source is not specified (DB-managed vs IdP-managed sync).
- Scope precedence/conflict rules across many roles need explicit deterministic behavior documentation.
- Audit requirements for authorization decisions are not yet defined (what to log, where, retention).
- Performance target/SLO for authorization predicate latency is not yet defined.

Decision needed before build start:
- Confirm whether `SUPERUSER` must bypass both scope and capability, or only scope. Current document assumes scope bypass only.

## Gradual implementation plan
### Phase 0 - Foundations and guardrails
Objective:
- Prepare schema and environment guardrails, accepting controlled runtime hardening where required for fail-closed identity resolution.

Tasks:
- Create `ref.roles`, `ref.user_roles`, `ref.role_permissions`, `ref.role_scopes` tables and required indexes.
- Add strict `APP_USER` environment gating and startup validation for non-production only.
- Introduce capability/resource enums or constrained check rules to prevent invalid values.
- Add migration rollback scripts and seed minimal baseline roles.

Implementation reality (as of v0.6):
- Implemented:
  - New role-model tables and indexes.
  - `APP_USER` non-production gating with startup validation.
  - Constrained check rules for resource/capability/scope values.
  - Baseline role and capability seed data.
- Changed runtime behavior:
  - `X-User-Id` and `APP_USER` are resolved by `user_acronym` (not numeric `user_id`) and fail closed when unresolved.
- Not implemented:
  - Dedicated migration rollback scripts are not currently present in this repository; initialization is driven by `ci/init/*.sql`.

Exit criteria:
- Migrations or init scripts apply cleanly in local and CI databases.
- Production configuration hard-blocks `APP_USER`.
- Baseline role/capability records are present and validated.

### Phase 1 - Read-path authorization predicate
Objective:
- Implement and validate read authorization logic before write-path enforcement.

Tasks:
- Implement `workflow.check_user_permission(...)` for `read-only` capability first.
- Integrate predicate into read-side workflow functions.
- Add RLS `USING` policies for `core.doc` and inherited read policies for related entities.
- Add integration tests for multi-role union behavior and fail-closed outcomes.

Exit criteria:
- Read endpoints respect capability + scope model with no unauthorized data exposure.
- Super-role and non-super-role read cases pass test scenarios.
- Explain plans show index usage for hot authorization queries.

### Phase 2 - Write-path enforcement
Objective:
- Extend model to enforce mutation permissions with consistent semantics.

Tasks:
- Extend predicate logic to full `read-write` support.
- Add workflow prechecks for create/update/delete-sensitive paths.
- Add RLS `WITH CHECK` write policies for protected tables.
- Add negative tests for forbidden write operations by scope/capability.

Exit criteria:
- Unauthorized writes are blocked at both workflow and RLS layers.
- Authorized writes succeed for all matrix-defined role/resource combinations.
- No regression in existing mutation API behavior outside authorization semantics.

### Phase 3 - Identity and role mapping integration
Objective:
- Replace local/dev identity assumptions with trusted identity mapping flow.

Tasks:
- Implement trusted auth context resolver (JWT/header to internal user mapping).
- Add IdP role/group to `ref.roles.external_name` mapping job or synchronization path.
- Add stale mapping handling and fail-closed behavior for unknown external roles.
- Add observability around mapping errors and authorization denials.

Exit criteria:
- End-to-end auth flow works without `APP_USER` outside local environment.
- Role sync/mapping is deterministic and monitored.
- Unknown identity/role inputs fail closed with traceable audit evidence.

### Phase 4 - Hardening, performance, and rollout
Objective:
- Validate production readiness and roll out with controlled blast radius.

Tasks:
- Run load tests focused on authorization predicate overhead.
- Add audit logging for authorization allow/deny decisions and policy path.
- Run staged rollout: shadow mode metrics, then enforced mode by environment.
- Conduct security review and finalize role matrix sign-off with business owners.

Exit criteria:
- Authorization path meets agreed latency/error SLOs.
- Security review findings are resolved or formally accepted.
- Production rollout completed with monitored deny-rate and no data isolation incidents.

## Rollout / Migration
- Backward compatibility:
  - During Phase 1 and Phase 2, keep legacy checks in place until RLS + workflow checks are validated in parallel.
- Data migration steps:
  - Seed roles, permissions, and scope records before enabling enforcement.
  - Backfill `user_roles` assignments from current source-of-truth mapping.
- Deployment notes:
  - Enable enforcement progressively by environment: local -> integration -> staging -> production.
  - Add feature flag for auth enforcement mode (`observe`, `enforce`) during rollout.

## Edge Cases
- User has no roles:
  - Authorization must return `false`; API must surface `403`.
- User has multiple roles with mixed capabilities:
  - Effective capability is union; `read-write` implies `read-only`.
- User has valid capability but no matching scope group:
  - Access must be denied unless any assigned role has `is_super = true`.
- Invalid or missing `app.user_id` session context:
  - Authorization must fail closed and not default to anonymous access.
- Orphaned lineage (`files` or `doc_revision` references missing parent scope context):
  - Permission check must return `false` and write path must reject operation.
- `APP_USER` accidentally set in non-local environment:
  - Startup or request middleware must hard-fail and emit security alert.

## Open Questions
- Should super-role bypass capability checks or only scope checks?
- What is the required audit schema for authorization decisions (fields, retention, PII policy)?
- Should scope model support explicit deny rules in addition to grant rules?
- What SLO must be enforced for `workflow.check_user_permission(...)` at p95/p99?

## References
- `documentation/auth_architecture.md`
- `documentation/api_db_rules.md`
- `documentation/er_diagram.md`
- `documentation/_documentation_template.md`
- `documentation/_documentation_standards.md`
- `documentation/_naming_convention.md`
