# Authorization and RLS matrix

## Document Control
- Status: Review
- Owner: Backend and Database Team
- Reviewers: Security and API maintainers
- Created: 2026-02-21
- Last Updated: 2026-02-21
- Version: v0.4

## Change Log
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
- `APP_USER` contains internal `user_id` value.
- API startup/request middleware validates that `APP_USER` exists in `ref.users`.
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
    v_user_id = cast(APP_USER as bigint)
    assert exists(select 1 from ref.users where user_id = v_user_id)
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

## Edge Cases
- Role exists but has no capabilities for a requested action.
- Role has capabilities but no scope rows.
- Multiple scope groups with partial matches.
- Super-role with explicit deny requirement (if deny semantics are introduced later).
- Missing `app.user_id` session value.
- `p_doc_id` provided but document row does not exist.
- User has one super-role and one limited role (super-role must win).
- `APP_USER` points to unknown external identity in local mode.

## References
- `documentation/auth_architecture.md`
- `documentation/api_db_rules.md`
- `documentation/document_flow.md`
