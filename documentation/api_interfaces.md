# Flow API Interfaces

## Document Control
- Status: Approved
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-06
- Last Updated: 2026-03-25
- Version: v4.3

## Change Log
- 2026-03-25 | v4.3 | Added dedicated `POST /api/v1/documents/revisions/{rev_id}/overview-transition` for creating the next revision from a current final revision, added `POST /api/v1/documents/revisions/{rev_id}/supersede` for replacing the current non-final revision with a new row that keeps the same `rev_code_id`, made generic revision updates reject `rev_code_id`, documented initial document `rev_code_id` defaulting to the `revision_overview.start` step, and clarified that canceled revisions are hidden from standard revision-list responses.
- 2026-03-20 | v4.1 | Clarified that there is currently no dedicated overview-transition endpoint: `ref.revision_overview` remains reference configuration, while `PUT /api/v1/documents/revisions/{rev_id}` may still change `core.doc_revision.rev_code_id` through `workflow.update_revision(...)`; also defined revision back-transition semantics explicitly so `direction="back"` moves only to the unique immediate predecessor status resolved by reverse `next_rev_status_id`, and the status graph forbids ambiguous predecessor configurations.
- 2026-03-19 | v3.9 | Clarified the `GET /api/v1/documents/revision_overview` contract: path-derived ordering, `next_rev_code_id` terminal nullability, unique start/final semantics, descriptive `percentage`, and the metadata role of `revertible`/`editable`.
- 2026-03-18 | v3.8 | Removed `recipient_user_id` override from `GET /api/v1/notifications` so inbox listing always resolves to the effective current user, updated examples/contracts accordingly, and documented owner-or-superuser authorization for `DELETE /api/v1/files/commented/{id}`, including the `403`/fail-closed `404` behavior and authenticated request example.
- 2026-03-12 | v3.6 | Removed redundant create-time actor fields from commented-files, written-comments, and notifications APIs; create authorship/sender now always resolves from effective session identity while recipient targeting remains explicit.
- 2026-03-07 | v3.5 | Added API-verified bearer JWT identity resolution ahead of trusted-header and `X-User-Id` fallbacks, documented JWT auth configuration, observability, and nginx bearer-token passthrough for `/api` requests, aligned local compose/Keycloak defaults so direct-access bearer-token testing uses `aud=flow-ui`, clarified that JWKS retrieval/client failures fail closed as `401 Unauthorized` with `flow_auth_jwt_validation_failures_total{reason="jwks_fetch_failed"}`, and restricted raw `X-User-Id` fallback to non-production environments only so production-capable modes accept bearer JWT, then trusted header, then optional local `APP_USER`.
- 2026-03-06 | v3.0 | Updated auth identity resolution order so trusted header (`X-Auth-User`, configurable via `TRUSTED_IDENTITY_HEADER`) takes precedence over `X-User-Id`, documented fail-closed behavior when trusted identity is invalid, and synchronized the request-header startup banner wording.
- 2026-03-04 | v2.9 | Added `/metrics` system endpoint for in-process auth observability counters; documented auth metrics for current-user resolution failures, observable RLS denials by endpoint, and identity header parse failures; and documented structured auth-event logs with correlation IDs and auth mode.
- 2026-02-26 | v2.4 | Documented Phase 1 read authorization effects on lookup reads: `GET /lookups/projects` is scope-filtered by role project scope; `areas` and `units` remain unfiltered in this phase.
- 2026-02-25 | v2.3 | Documented `APP_USER` local/dev bootstrap behavior with non-production-only guardrails and startup validation against `ref.users`, removed the legacy default fallback variable so user context resolves from `X-User-Id` first then optional `APP_USER`, enforced `user_acronym`-only identity input for those sources, documented dual DB session context keys (`app.user`, `app.user_id`), and updated `GET /api/v1/people/users/current_user` to resolve the current user from session context instead of hardcoded `user_id=2`.
- 2026-02-21 | v1.9 | Added written comments API (`list/create/update/delete`) under `comments`, split written comments into dedicated router/schema modules with synchronized test/doc traceability, corrected file update-body `id` validation contract to `422` (extra field forbidden), added nullable `doc_id` support for distribution lists (`create/list`), documented `dl_for_each_doc=true` auto-DL creation on document create, extended people/persons and people/users payloads with duty fields (`duty_id`, `duty_name`), and added distribution-list search by `doc_id` (`GET /distribution-lists?doc_id=...`).
- 2026-02-20 | v1.8 | Renamed commented download query parameter from `file_id` to `id`.
- 2026-02-19 | v1.7 | Updated API contracts and examples for latest backend behavior.

## Purpose
Provide the current backend API surface and behavior contract for clients and maintainers.

## Scope
- In scope:
  - Endpoint methods, payloads, statuses, and conventions.
  - Error and validation behavior for the active API surface.
- Out of scope:
  - UI implementation details.
  - Database DDL internals not exposed by API contracts.

## Design / Behavior
The sections below define endpoint groups and shared conventions. This document is manually maintained and must match implemented behavior.

Current FastAPI surface (version 0.1.0). All endpoints are JSON unless noted, live under the backend root (no global prefix), and are CORS-open for any origin. Default database URL is `postgresql+psycopg://app_user:app_pass@postgres:5432/flow_db`; override via `APP_DATABASE_URL` or `APP_DB_USER/APP_DB_PASSWORD` with `POSTGRES_HOST/PORT/DB`. Object storage defaults to `MINIO_ENDPOINT=minio:9000` and `MINIO_BUCKET=flow-default`; override with `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_SECURE`.

Base URL convention used in examples:
- `API_BASE` must be set to your running API host.
- Local development default API: `http://localhost:5556`.
- Test stack API (used by automated API tests): `http://localhost:4175`.
- Example setup:
```bash
export API_BASE=http://localhost:5556
```

Update conventions (PUT/PATCH):
- `PUT` is idempotent and used for updates; this API accepts partial updates via `PUT` (fields may be omitted unless noted).
- Request bodies must not include undeclared id fields. For schemas configured with `extra="forbid"` (including file update payloads), an unexpected `id` field returns `422 Unprocessable Entity`.
- `PATCH` is currently used only for revision cancel (`PATCH /api/v1/documents/revisions/{rev_id}/cancel`).

Delete conventions:
- DELETE endpoints do not accept a request body.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE $API_BASE/resource/{id}
```
- Success may return `204 No Content` (files endpoints) or `200 OK` with a JSON result body (documents and distribution lists).
- If the resource does not exist, return `404 Not Found`.

List conventions:
- List endpoints return `200 OK` with an empty list when no records match.

Error response schema:
- Unless noted, errors return a JSON object with a `detail` field.
- FastAPI validation errors use a `detail` array with `loc`, `msg`, and `type` entries.

Example error responses:
```json
{ "detail": "Not Found" }
```
```json
{ "detail": "Discipline name or acronym already exists" }
```
```json
{
  "detail": [
    { "loc": ["body", "field"], "msg": "Field required", "type": "missing" }
  ]
}
```

Common status codes (by endpoint and context):
- `200 OK` — Successful read/update responses.
- `201 Created` — Successful create responses.
- `204 No Content` — Successful delete responses.
- `400 Bad Request` — Domain validation or duplicate/uniqueness violations.
- `401 Unauthorized` — Authentication required for auth-sensitive routers when effective session identity is missing.
- `403 Forbidden` — Authenticated but not authorized (enforced for notification replace/drop actions).
- `404 Not Found` — Resource does not exist.
- `409 Conflict` — Returned when workflow/business rules reject the action (for example: revision status transition/cancel constraints, distribution list in use).
- `422 Unprocessable Entity` — FastAPI/Pydantic request validation errors.
- `500 Internal Server Error` — Unhandled server errors.

OpenAPI/Swagger:
- Swagger UI (FastAPI): `/docs`
- OpenAPI JSON: `/openapi.json`
- OpenAPI YAML: `/openapi.yaml` (if enabled)
- This document is maintained manually; verify against the OpenAPI schema when updating endpoints.

## Edge Cases
- Invalid path/query IDs: FastAPI validation returns `422 Unprocessable Entity` for non-integer values; valid-but-missing IDs return `404 Not Found`.
- Malformed JSON bodies: FastAPI returns `422 Unprocessable Entity` with a validation error payload.
- Concurrent modification: optimistic locking is not implemented.

Audit fields (created_by / updated_by):
- `created_by` and `updated_by` are set by the application or by DB triggers when NULL.
- DB triggers read session setting `app.user` (SMALLINT user id). The API sets both `app.user` (current) and `app.user_id` (forward-compatible auth context) per request.
- The API stores the resolved user id on the SQLAlchemy request session and writes both DB keys with transaction-local scope (`set_config(..., true)`) whenever a DB transaction begins.
- This transaction-local re-application is required because many endpoints issue mid-request `COMMIT` / `ROLLBACK`; after each new transaction begins, identity is pushed again before business queries run.
- When effective identity is absent, the API still writes both keys as empty strings at transaction scope so reused pooled connections cannot inherit a previous request's session-level residue.
- User resolution order:
  - verified bearer JWT from `Authorization: Bearer <token>` when present
  - trusted identity header (`X-Auth-User` by default; configurable via `TRUSTED_IDENTITY_HEADER`) when present and non-empty
  - `X-User-Id` header only when trusted identity header is absent or empty and `APP_ENV`/`ENV` is one of `local/dev/development/test/testing/ci/ci_test`
  - `APP_USER` environment fallback when both request headers are absent
- Bearer JWT verification contract:
  - API validates signature, issuer, audience, expiry, and configured algorithms before resolving internal identity.
  - JWT identity claim search order is configurable through `AUTH_JWT_IDENTITY_CLAIMS` and defaults to `acronym,preferred_username,sub`.
- JWT verification requires `AUTH_JWT_ISSUER_URL` and `AUTH_JWT_AUDIENCE`, plus either `AUTH_JWT_SHARED_SECRET` or JWKS discovery/override via `AUTH_JWT_JWKS_URL`.
  - Local compose defaults expect `aud=flow-ui`; the bundled local Keycloak realm is configured to emit that audience for `flow-ui` direct-access tokens.
  - JWKS discovery, fetch, and client-parsing failures must fail closed as `401 Unauthorized` and increment `flow_auth_jwt_validation_failures_total{reason="jwks_fetch_failed"}`.
- Request-header identity values must be existing `user_acronym`; API resolves them to internal `user_id` before setting DB session context.
- If bearer-token validation fails, the API returns `401 Unauthorized` and does not fall back to trusted-header or `X-User-Id` identity sources for that request.
- When both trusted and less-trusted headers are present, the trusted header is authoritative.
- If the trusted identity header is present but unresolved, the API fails closed with `401 Unauthorized` instead of falling back to `X-User-Id`.
- In production-capable environments (`prod/production/stage/staging`), the API ignores inbound `X-User-Id` and requires bearer JWT or the trusted identity header for request-sourced identity.
- `APP_USER` is guarded: it must be used only in non-production environments (`local/dev/test/ci/ci_test`), and startup validation must confirm that configured value resolves to a row in `workflow.v_users`.
- `APP_USER` format is validated at startup with a strict uppercase acronym regex: `^[A-Z]{2,12}$`.
- `APP_ENV=production` (or other blocked/unknown non-allowed envs) plus `APP_USER` causes startup failure before the API begins serving requests.
- Startup logs emit a clear identity banner:
  - `startup_identity_mode=request_header_only ... identity_source=Authorization>X-Auth-User>X-User-Id` in non-production environments where raw header fallback is enabled.
  - `startup_identity_mode=request_header_only ... identity_source=Authorization>X-Auth-User` in production-capable environments where raw header fallback is disabled.
  - `startup_identity_mode=app_user_bootstrap ...` when `APP_USER` bootstrap mode is active.
- Auth-sensitive routers fail closed with `401 Unauthorized` when no supported identity source resolves to an effective session identity. The API logs a security event with `X-Request-Id`, HTTP method, and path only.
- Local nginx ingress behavior:
  - `/api` requests with `Authorization: Bearer ...` are passed directly to the API so bearer-token validation can occur in FastAPI.
  - `/api` requests without bearer tokens continue through `oauth2-proxy` and use trusted `X-Auth-User` forwarding.
- Auth observability counters are exposed at `GET /metrics` in Prometheus text format:
  - `flow_auth_current_user_resolution_failures_total{reason=...}`
  - `flow_auth_denied_by_rls_total{endpoint=...,status_code=...,auth_mode=...}`
  - `flow_auth_identity_header_parse_failures_total{auth_mode=...}`
  - `flow_auth_jwt_validation_failures_total{reason=...}`
- Auth-event logs are structured as key-value fields and include:
  - `event`
  - `request_id`
  - `auth_mode`
  - `method`
  - `path`
  - reason-specific fields such as `reason` or `header_name`

## Health and root
- `GET /` — Returns `{"message": "Flow backend is running"}`.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/
```
- Example response:
```json
{ "message": "Flow backend is running" }
```
- `GET /health` — Returns `{"status": "ok"}`.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/health
```
- Example response:
```json
{ "status": "ok" }
```
- `GET /metrics` — Returns Prometheus text-format counters for in-process API observability.
- Headers: `Accept: text/plain`
- Example request:
```bash
curl -sS -H "Accept: text/plain" $API_BASE/metrics
```
- Example response:
```text
# HELP flow_auth_current_user_resolution_failures_total Current-user resolution failures by reason.
# TYPE flow_auth_current_user_resolution_failures_total counter
flow_auth_current_user_resolution_failures_total{reason="missing_identity"} 3
# HELP flow_auth_jwt_validation_failures_total JWT validation failures by reason.
# TYPE flow_auth_jwt_validation_failures_total counter
flow_auth_jwt_validation_failures_total{reason="invalid_token"} 1
```

## Lookups

These endpoints are read-only via API; create/update/delete is handled via seed/admin workflows.

## Areas
Shape (single item):
```json
{ "area_id": 1, "area_name": "Newfoundland", "area_acronym": "NFLD" }
```
Schema references:
- Response: `api/schemas/lookups.py` `AreaOut`
### List
- `GET /api/v1/lookups/areas` — 200 sorted by `area_name`; empty list if no areas.
- Current phase note: areas are not scope-filtered yet (project-only lookup scoping is implemented).
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/lookups/areas
```
- Example response:
```json
[
  { "area_id": 1, "area_name": "Newfoundland", "area_acronym": "NFLD" }
]
```
## Disciplines
Shape (single item):
```json
{ "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" }
```
Schema references:
- Response: `api/schemas/lookups.py` `DisciplineOut`
### List
- `GET /api/v1/lookups/disciplines` — 200 sorted by `discipline_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/lookups/disciplines
```
- Example response:
```json
[ { "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" } ]
```
## Projects
Shape (single item):
```json
{ "project_id": 3, "project_name": "Delta Expansion" }
```
Schema references:
- Response: `api/schemas/lookups.py` `ProjectOut`
### List
- `GET /api/v1/lookups/projects` — 200 sorted by `project_name`; empty list if none.
- Visibility is authorization-scoped in current implementation:
  - result includes only projects allowed by the caller's `role_scopes` (`scope_type='PROJECT'`) and capability checks.
  - when caller has no matching project scopes and is not superuser, response is an empty list.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/lookups/projects
```
- Example response:
```json
[ { "project_id": 3, "project_name": "Delta Expansion" } ]
```
## Units
Shape (single item):
```json
{ "unit_id": 2, "unit_name": "North Wing" }
```
Schema references:
- Response: `api/schemas/lookups.py` `UnitOut`
### List
- `GET /api/v1/lookups/units` — 200 sorted by `unit_name`; empty list if none.
- Current phase note: units are not scope-filtered yet (project-only lookup scoping is implemented).
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/lookups/units
```
- Example response:
```json
[ { "unit_id": 2, "unit_name": "North Wing" } ]
```
## Jobpacks
Shape (single item):
```json
{ "jobpack_id": 5, "jobpack_name": "JP-01" }
```
Schema references:
- Response: `api/schemas/lookups.py` `JobpackOut`
### List
- `GET /api/v1/lookups/jobpacks` — 200 sorted by `jobpack_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/lookups/jobpacks
```
- Example response:
```json
[ { "jobpack_id": 5, "jobpack_name": "JP-01" } ]
```
## Doc revision milestones
Shape (single item):
```json
{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }
```
Schema references:
- Response: `api/schemas/documents.py` `DocRevMilestoneOut`
### List
- `GET /api/v1/documents/doc_rev_milestones` — 200 sorted by `milestone_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/documents/doc_rev_milestones
```
- Example response:
```json
[ { "milestone_id": 4, "milestone_name": "IFC", "progress": 90 } ]
```
## Revision overview
Shape (single item):
```json
{
  "rev_code_id": 6,
  "rev_code_name": "INDESIGN",
  "rev_code_acronym": "A",
  "rev_description": "In-design",
  "next_rev_code_id": 1,
  "revertible": false,
  "editable": true,
  "final": false,
  "start": true,
  "percentage": 10
}
```
Schema references:
- Response: `api/schemas/documents.py` `RevisionOverviewOut`
### List
- `GET /api/v1/documents/revision_overview` — 200 ordered from the single `start=true` step to the single `final=true` step; empty list if no start step is configured.
- Contract notes:
  - Response order is guaranteed to follow the lifecycle path starting at the single reachable `start=true` row and recursively following `next_rev_code_id` until the terminal row.
  - The endpoint does not sort by `rev_code_name`, `rev_code_id`, or `percentage`.
  - In a valid lifecycle configuration, exactly one returned item has `start=true` and exactly one returned item has `final=true`.
  - `next_rev_code_id` is null only for the terminal row returned by this endpoint; non-terminal rows expose the immediate successor ID.
  - `revertible` is lifecycle metadata that indicates whether the configured step allows backward movement to its predecessor in the modeled chain.
  - `editable` is lifecycle metadata exposed to clients; this endpoint does not itself enforce write authorization rules based on `editable`.
  - `percentage` is descriptive progress metadata only. Clients must not infer response order from it or assume monotonicity as an API guarantee.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/documents/revision_overview
```
- Example response:
```json
[
  {
    "rev_code_id": 6,
    "rev_code_name": "INDESIGN",
    "rev_code_acronym": "A",
    "rev_description": "In-design",
    "next_rev_code_id": 1,
    "revertible": false,
    "editable": true,
    "final": false,
    "start": true,
    "percentage": 10
  },
  {
    "rev_code_id": 1,
    "rev_code_name": "IDC",
    "rev_code_acronym": "B",
    "rev_description": "Interdiscipline check",
    "next_rev_code_id": 2,
    "revertible": true,
    "editable": true,
    "final": false,
    "start": false,
    "percentage": 30
  }
]
```
## Doc revision status UI behaviors
Shape (single item):
```json
{ "ui_behavior_id": 1, "ui_behavior_name": "Default", "ui_behavior_file": "default.json" }
```
Schema references:
- Response: `api/schemas/documents.py` `DocRevStatusUiBehaviorOut`
### List
- `GET /api/v1/lookups/doc_rev_status_ui_behaviors` — 200 sorted by `ui_behavior_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/lookups/doc_rev_status_ui_behaviors
```
- Example response:
```json
[ { "ui_behavior_id": 1, "ui_behavior_name": "Default", "ui_behavior_file": "default.json" } ]
```
## Doc revision statuses
Shape (single item):
```json
{
  "rev_status_id": 2,
  "rev_status_name": "IDC",
  "ui_behavior_id": 3,
  "next_rev_status_id": 4,
  "revertible": true,
  "editable": true,
  "final": false,
  "start": false
}
```
Schema references:
- Response: `api/schemas/documents.py` `DocRevStatusOut`
### List
- `GET /api/v1/lookups/doc_rev_statuses` — 200 sorted by `rev_status_name`; empty list if none.
- Contract notes:
  - `next_rev_status_id` identifies the immediate forward successor status; `null` is allowed only on the unique terminal/final status.
  - The status graph allows at most one immediate predecessor for any status, so reverse traversal is unambiguous.
  - `revertible` means the current status may move back only to that unique immediate predecessor; it does not permit arbitrary jumps to older statuses.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/lookups/doc_rev_statuses
```
- Example response:
```json
[
  {
    "rev_status_id": 2,
    "rev_status_name": "IDC",
    "ui_behavior_id": 3,
    "next_rev_status_id": 4,
    "revertible": true,
    "editable": true,
    "final": false,
    "start": false
  }
]
```
## Files

Create conventions:
- `POST` (Create) returns `201 Created`.
- Response body includes the created resource (or at least the new id).

Shape (single item):
```json
{
  "id": 12,
  "filename": "report.pdf",
  "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
  "mimetype": "application/pdf",
  "rev_id": 45,
  "created_at": "2026-01-23T17:45:08.294332Z",
  "updated_at": "2026-01-23T17:45:08.294332Z",
  "created_by": 1,
  "updated_by": 1
}
```
Schema references:
- Create: `api/schemas/files.py` `FileCreate`
- Update: `api/schemas/files.py` `FileUpdate`
- Response: `api/schemas/files.py` `FileOut`
- Delete: `api/schemas/files.py` `FileDelete`

### List
- `GET /api/v1/files?rev_id=45` — 200 sorted by `filename`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/files?rev_id=45
```
- Example response:
```json
[
  {
    "id": 12,
    "filename": "report.pdf",
    "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
    "mimetype": "application/pdf",
    "rev_id": 45,
    "created_at": "2026-01-23T17:45:08.294332Z",
    "updated_at": "2026-01-23T17:45:08.294332Z",
    "created_by": 1,
    "updated_by": 1
  }
]
```

### Create (multipart)
- `POST /api/v1/files/` — 201; multipart form.
- Headers: `Accept: application/json`, `Content-Type: multipart/form-data`
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  -F "rev_id=45" \
  -F "file=@report.pdf;type=application/pdf" \
  $API_BASE/api/v1/files/
```
- Form fields: `rev_id` (int), `file` (binary).
- Default stored filename is generated from `workflow.v_instance_parameters.parameter='file_name_conv'` template (`<DOCNO>-<BODY>_<UACR>_<TIMEST>.<EXT>`), where:
  - `<DOCNO>` = document name (`doc_name_unique`)
  - `<BODY>` = uploaded filename body
  - `<UACR>` = uploader acronym from current `app.user` (from `X-User-Id` or optional `APP_USER`)
  - `<TIMEST>` = current UTC timestamp
  - `<EXT>` = uploaded extension
- Fallback behavior: if the parameter/user context/template rendering is unavailable or invalid, API keeps the uploaded filename unchanged.
- Response: file shape.
- Example response:
```json
{
  "id": 12,
  "filename": "report.pdf",
  "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
  "mimetype": "application/pdf",
  "rev_id": 45,
  "created_at": "2026-01-23T17:45:08.294332Z",
  "updated_at": "2026-01-23T17:45:08.294332Z",
  "created_by": 1,
  "updated_by": 1
}
```

### Update
- `PUT /api/v1/files/{id}` — 200; updates filename; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "filename": "new_report.pdf" }' \
  $API_BASE/api/v1/files/{id}
```
- Example response:
```json
{
  "id": 12,
  "filename": "new_report.pdf",
  "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
  "mimetype": "application/pdf",
  "rev_id": 45,
  "created_at": "2026-01-23T17:45:08.294332Z",
  "updated_at": "2026-01-23T17:45:08.294332Z",
  "created_by": 1,
  "updated_by": 1
}
```
- Body:
```json
{ "filename": "new_report.pdf" }
```

### Delete
- `DELETE /api/v1/files/{id}` — 204; deletes MinIO object and DB row; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE $API_BASE/api/v1/files/{id}
```
- Example response: (empty)

### Download
- `GET /api/v1/files/{file_id}/download` — streams the file with `Content-Disposition: attachment` and `ETag`/`Last-Modified`.
- Returns `416` when a `Range` header is provided (range requests are not supported).
- Headers: `Accept: application/octet-stream`
- Example request:
```bash
curl -sS -H "Accept: application/octet-stream" \
  -o report.pdf \
  $API_BASE/api/v1/files/{file_id}/download
```
- Example response (binary):
```
<binary>
```

## Files (commented)

Create conventions:
- `POST` (Create) returns `201 Created`.
- Response body includes the created resource (or at least the new id).

Shape (single item):
```json
{
  "id": 3,
  "file_id": 12,
  "user_id": 1,
  "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
  "filename": "report.pdf",
  "mimetype": "application/pdf",
  "rev_id": 45,
  "created_at": "2026-01-23T17:45:08.294332Z",
  "updated_at": "2026-01-23T17:45:08.294332Z",
  "created_by": 1,
  "updated_by": 1
}
```
Schema references:
- Response: `api/schemas/files.py` `FileCommentedOut`
- Create: `api/schemas/files.py` `FileCommentedOut`
- Update: `api/schemas/files.py` `FileCommentedOut`
- Delete: `api/schemas/files.py` `FileCommentedDelete`

### List
- `GET /api/v1/files/commented/list?file_id=12` — 200; optional `user_id` filter.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/files/commented/list?file_id=12
```
- Example response:
```json
[
  {
    "id": 3,
    "file_id": 12,
    "user_id": 1,
    "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
    "filename": "report.pdf",
    "mimetype": "application/pdf",
    "rev_id": 45,
    "created_at": "2026-01-23T17:45:08.294332Z",
    "updated_at": "2026-01-23T17:45:08.294332Z",
    "created_by": 1,
    "updated_by": 1
  }
]
```

### Create (multipart)
- `POST /api/v1/files/commented/` — 201; multipart form.
- Headers: `Accept: application/json`, `Content-Type: multipart/form-data`
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  -F "file_id=12" \
  -H "X-User-Id: FDQC" \
  -F "file=@commented.pdf;type=application/pdf" \
  $API_BASE/api/v1/files/commented/
```
- Form fields: `file_id` (int), `file` (binary, optional).
- Authorship: uploader `user_id` is derived from effective session identity (`X-User-Id` / trusted auth context), not from form data.
- If `file` is omitted, API copies source file bytes from `file_id` into a new commented file object.
- If `file` is provided, API validates mimetype against the original file.
- Commented-file object naming uses `workflow.v_instance_parameters.parameter='file_name_com_conv'` (`<BODY>_commented_<UACR>_<TIMEST>.<EXT>`), where `<BODY>` is taken from the source file linked by `file_id` (applies both when uploading manually and when copying without `file`), with the same fallback behavior (original name unchanged when template resolution fails).
- Response `filename` for commented files reflects the commented object name (derived from commented `s3_uid`), not the original source file name.
- Rejects duplicates per `(file_id, user_id)`.
- Example response:
```json
{
  "id": 3,
  "file_id": 12,
  "user_id": 1,
  "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
  "filename": "report.pdf",
  "mimetype": "application/pdf",
  "rev_id": 45,
  "created_at": "2026-01-23T17:45:08.294332Z",
  "updated_at": "2026-01-23T17:45:08.294332Z",
  "created_by": 1,
  "updated_by": 1
}
```

### Replace (multipart)
- `POST /api/v1/files/commented/{id}/replace` — 200; replaces the stored commented-file object while preserving the same commented-file record.
- Headers: `Accept: application/json`, `Content-Type: multipart/form-data`
- Form fields: `file` (binary, required).
- Authorization: allowed only for the commented-file owner or a superuser. Actor is derived from effective session identity for audit metadata; existing commented file `user_id` is preserved.
- Validation: filename is required, file must be non-empty, accepted file type/mimetype must match the original source file.
- Errors: unauthorized actors do not succeed; they may receive `403` when the commented file is visible to them, or fail-closed `404` when read-side RLS hides the row.
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  -H "X-User-Id: FDQC" \
  -F "file=@commented-revised.pdf;type=application/pdf" \
  "$API_BASE/api/v1/files/commented/3/replace"
```
- Example response:
```json
{
  "id": 3,
  "file_id": 12,
  "user_id": 1,
  "s3_uid": "Project/Doc/IFC/uuid_report_replaced.pdf",
  "filename": "report_replaced.pdf",
  "mimetype": "application/pdf",
  "rev_id": 45,
  "created_at": "2026-01-23T17:45:08.294332Z",
  "updated_at": "2026-01-23T18:10:00.000000Z",
  "created_by": 1,
  "updated_by": 1
}
```

### Delete
- `DELETE /api/v1/files/commented/{id}` — 204; owner or superuser only; deletes MinIO object and DB row; `403` for a visible but unauthorized actor, fail-closed `404` if not found or hidden by RLS.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -H "X-User-Id: FDQC" -X DELETE $API_BASE/api/v1/files/commented/{id}
```
- Example response: (empty)

### Download
- `GET /api/v1/files/commented/download?id=3` — streams the commented file.
- Returns `416` when a `Range` header is provided (range requests are not supported).
- Headers: `Accept: application/octet-stream`
- Example request:
```bash
curl -sS -H "Accept: application/octet-stream" \
  -o commented.pdf \
  $API_BASE/api/v1/files/commented/download?id=3
```
- Example response (binary):
```
<binary>
```
- `Content-Disposition` filename is the commented object filename.

### Written comments
Shape (single item):
```json
{
  "id": 11,
  "rev_id": 45,
  "user_id": 1,
  "comment_text": "Please verify section B-B.",
  "created_at": "2026-02-21T09:12:34.000000Z",
  "updated_at": "2026-02-21T09:12:34.000000Z",
  "created_by": 1,
  "updated_by": 1
}
```
Schema references:
- Response: `api/schemas/written_comments.py` `WrittenCommentOut`
- Create: `api/schemas/written_comments.py` `WrittenCommentCreate`

#### List
- `GET /api/v1/documents/revisions/45/comments` — 200; optional `user_id` filter.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  "$API_BASE/api/v1/documents/revisions/45/comments?user_id=1"
```

#### Create
- `POST /api/v1/documents/revisions/45/comments` — 201; creates written comment for revision by the effective session user.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" -H "X-User-Id: FDQC" \
  -d '{"comment_text":"Please verify section B-B."}' \
  "$API_BASE/api/v1/documents/revisions/45/comments"
```
- Validation: blank text is rejected (`400`), missing fields rejected (`422`), extra `user_id` field rejected (`422`).

#### Delete
- `DELETE /api/v1/documents/revisions/comments/{id}` — 204.
- Authorization actor is resolved from `X-User-Id` (or configured default app user). Only author or superuser can delete.
- Headers: `Accept: application/json`, `X-User-Id: <user_id>`
- Example request:
```bash
curl -i -H "Accept: application/json" -H "X-User-Id: 1" \
  -X DELETE "$API_BASE/api/v1/documents/revisions/comments/11"
```

#### Update
- `PUT /api/v1/documents/revisions/comments/{id}` — 200; updates `comment_text`.
- Authorization actor is resolved from `X-User-Id` (or configured default app user). Only author or superuser can update.
- Headers: `Accept: application/json`, `Content-Type: application/json`, `X-User-Id: <user_id>`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" -H "X-User-Id: 1" \
  -d '{"comment_text":"Updated note for this revision."}' \
  "$API_BASE/api/v1/documents/revisions/comments/11"
```

## Persons/users/permissions

These endpoints are read-only via API; create/update/delete is handled via seed/admin workflows.

## Roles
Shape (single item):
```json
{ "role_id": 10, "role_name": "Coordinator" }
```
Schema references:
- Response: `api/schemas/lookups.py` `RoleOut`
### List
- `GET /api/v1/people/roles` — 200 sorted by `role_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/people/roles
```
- Example response:
```json
[ { "role_id": 10, "role_name": "Coordinator" } ]
```
## People
Shape (single item):
```json
{
  "person_id": 12,
  "person_name": "Ada Lovelace",
  "photo_s3_uid": "s3-key-123",
  "duty_id": 1,
  "duty_name": "Engineer"
}
```
Schema references:
- Response: `api/schemas/people.py` `PersonOut`
### List
- `GET /api/v1/people/persons` — 200 sorted by `person_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/people/persons
```
- Example response:
```json
[
  {
    "person_id": 12,
    "person_name": "Ada Lovelace",
    "photo_s3_uid": "s3-key-123",
    "duty_id": 1,
    "duty_name": "Engineer"
  }
]
```
## Users
Shape (single item):
```json
{
  "user_id": 7,
  "person_id": 12,
  "user_acronym": "ALV",
  "role_id": 3,
  "person_name": "Ada Lovelace",
  "role_name": "Coordinator",
  "duty_id": 1,
  "duty_name": "Engineer"
}
```
Schema references:
- Response: `api/schemas/people.py` `UserOut`
### List
- `GET /api/v1/people/users` — 200 sorted by `user_acronym`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/people/users
```
- Example response:
```json
[
  {
    "user_id": 7,
    "person_id": 12,
    "user_acronym": "ALV",
    "role_id": 3,
    "person_name": "Ada Lovelace",
    "role_name": "Coordinator",
    "duty_id": 1,
    "duty_name": "Engineer"
  }
]
```
### Current user
- `GET /api/v1/people/users/current_user` — 200; returns current user from DB session context (`app.user`).
- `401 Unauthorized` when no effective session identity exists.
- `404 Not Found` when a session identity exists but the current-user read model cannot resolve it.
  - Includes users filtered/hidden from the visible read model.
  - Includes inactive/disabled/deprovisioned users that no longer resolve in the active user dataset.
- Headers:
  - `Accept: application/json`
  - optional `Authorization: Bearer <jwt>`
  - optional `X-Auth-User: <user_acronym>`
  - optional `X-User-Id: <user_acronym>`
- Identity precedence for this endpoint follows the shared auth convention above: bearer JWT, then trusted header, then `X-User-Id`, then local `APP_USER`.
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Authorization: Bearer $ACCESS_TOKEN" \
  $API_BASE/api/v1/people/users/current_user
```
- Example response:
```json
{
  "user_id": 2,
  "person_id": 1,
  "user_acronym": "FDQC",
  "role_id": 4,
  "person_name": "Flow DCC",
  "role_name": "DCC User",
  "duty_id": 1,
  "duty_name": "Engineer"
}
```
- Example `401` response:
```json
{ "detail": "Authentication required" }
```
- Example `404` response:
```json
{ "detail": "Current user not found" }
```
## Permissions
Shape (single item):
```json
{
  "permission_id": 42,
  "user_id": 7,
  "project_id": 3,
  "discipline_id": 2,
  "user_acronym": "ALV",
  "person_name": "Ada Lovelace",
  "project_name": "Delta Expansion",
  "discipline_name": "Piping"
}
```
Schema references:
- Response: `api/schemas/people.py` `PermissionOut`
At least one of `project_id` or `discipline_id` is required.
### List
- `GET /api/v1/people/permissions` — 200 sorted by `user_id`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/people/permissions
```
- Example response:
```json
[ { "permission_id": 42, "user_id": 7, "project_id": 3, "discipline_id": 2, "user_acronym": "ALV", "person_name": "Ada Lovelace", "project_name": "Delta Expansion", "discipline_name": "Piping" } ]
```
## Docs

Create conventions:
- `POST` (Create) returns `201 Created`.
- Response body includes the created resource (or at least the new id).

## Doc types
Shape (single item):
```json
{
  "type_id": 7,
  "doc_type_name": "Piping Iso",
  "ref_discipline_id": 2,
  "doc_type_acronym": "ISO",
  "discipline_name": "Piping",
  "discipline_acronym": "PIP"
}
```
Schema references:
- Response: `api/schemas/documents.py` `DocTypeOut`
Read-only via API; create/update/delete is handled via seed/admin workflows.
### List
- `GET /api/v1/documents/doc_types` — 200 sorted by `doc_type_name`; includes discipline info; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/documents/doc_types
```
- Example response:
```json
[ { "type_id": 7, "doc_type_name": "Piping Iso", "ref_discipline_id": 2, "doc_type_acronym": "ISO", "discipline_name": "Piping", "discipline_acronym": "PIP" } ]
```
## Documents
Shape (single item) includes doc, linked names, and discipline/progress pointers:
`doc_id`, `doc_name_unique`, `title`, `project_id`/`project_name`, `jobpack_id`/`jobpack_name`, `type_id`/`doc_type_name`/`doc_type_acronym`, `area_id`/`area_name`/`area_acronym`, `unit_id`/`unit_name`, `rev_actual_id`, `rev_current_id`, `rev_seq_num`, `discipline_id`/`discipline_name`/`discipline_acronym`, `rev_code_name`, `rev_code_acronym`, `rev_status_id`, `rev_status_name`, `percentage`, `voided`, `created_at`, `updated_at`, `created_by`, `updated_by`.
Schema references:
- Response: `api/schemas/documents.py` `DocOut`
- Create: `api/schemas/documents.py` `DocCreate`
- Update: `api/schemas/documents.py` `DocUpdate`
### List
- `GET /api/v1/documents?project_id=3` — 200 ordered by `doc_name_unique`; empty list if none for the project. Excludes voided documents by default. Requires `project_id` query param.
- Optional query param: `show_voided=true` to include voided documents in the response.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/documents?project_id=3
```
- Example response:
```json
[
  {
    "doc_id": 11,
    "doc_name_unique": "PRJ-ISO-001",
    "title": "Piping Iso 001",
    "project_id": 3,
    "project_name": "Delta Expansion",
    "jobpack_id": 5,
    "jobpack_name": "JP-01",
    "type_id": 7,
    "doc_type_name": "Piping Iso",
    "doc_type_acronym": "ISO",
    "area_id": 1,
    "area_name": "Newfoundland",
    "area_acronym": "NFLD",
    "unit_id": 2,
    "unit_name": "North Wing",
    "rev_actual_id": null,
    "rev_current_id": null,
    "rev_seq_num": 2,
    "discipline_id": 2,
    "discipline_name": "Piping",
    "discipline_acronym": "PIP",
    "rev_code_name": "IFC",
    "rev_code_acronym": "E",
    "rev_status_id": 2,
    "rev_status_name": "IDC",
    "percentage": 90,
    "voided": false,
    "created_at": "2026-01-23T17:45:08.294332Z",
    "updated_at": "2026-01-23T17:45:08.294332Z",
    "created_by": 1,
    "updated_by": 1
  }
]
```
### Create
- `POST /api/v1/documents` — 201; creates a new document with an initial revision using the start status from doc_rev_statuses; 400 on uniqueness or no start status; 404 if referenced entities not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{
  "doc_name_unique": "PRJ-ISO-002",
  "title": "Piping Iso 002",
  "project_id": 3,
  "jobpack_id": 5,
  "type_id": 7,
  "area_id": 1,
  "unit_id": 2,
  "rev_code_id": 6,
  "rev_author_id": 1,
  "rev_originator_id": 1,
  "rev_modifier_id": 1,
  "transmital_current_revision": "TR-002",
  "milestone_id": 1,
  "planned_start_date": "2024-01-02T12:00:00Z",
  "planned_finish_date": "2024-01-05T12:00:00Z"
}' \
  $API_BASE/api/v1/documents
```
- Example response:
```json
{
  "doc_id": 12,
  "doc_name_unique": "PRJ-ISO-002",
  "title": "Piping Iso 002",
  "project_id": 3,
  "project_name": "Delta Expansion",
  "jobpack_id": 5,
  "jobpack_name": "JP-01",
  "type_id": 7,
  "doc_type_name": "Piping Iso",
  "doc_type_acronym": "ISO",
  "area_id": 1,
  "area_name": "Newfoundland",
  "area_acronym": "NFLD",
  "unit_id": 2,
  "unit_name": "North Wing",
  "rev_actual_id": null,
  "rev_current_id": 1,
  "rev_seq_num": 1,
  "discipline_id": 2,
  "discipline_name": "Piping",
  "discipline_acronym": "PIP",
  "rev_code_name": "INDESIGN",
  "rev_code_acronym": "A",
  "rev_status_id": 1,
  "rev_status_name": "InDesign",
  "percentage": 0
}
```
- Body:
  - Required fields: `doc_name_unique`, `title`, `type_id`, `area_id`, `unit_id`, `rev_author_id`, `rev_originator_id`, `rev_modifier_id`, `transmital_current_revision`, `planned_start_date`, `planned_finish_date`
  - Optional fields: `project_id`, `jobpack_id`, `milestone_id`, `rev_code_id`
  - Note: The initial revision automatically uses the status with `start=true` from `doc_rev_statuses`.
  - Note: When `rev_code_id` is omitted, the backend uses the `revision_overview` row where `start=true`.
  - Note: When `rev_code_id` is provided, it must reference an allowed initial revision-overview step.
  - Note: If `workflow.v_instance_parameters.parameter='dl_for_each_doc'` has value `true` (case-insensitive), create also auto-creates a `distribution_list` row linked by `doc_id` with name pattern `DL_<doc_name_unique>`.
  - Note: Auto-DL creation is idempotent by name; if `DL_<doc_name_unique>` already exists, document creation still succeeds and no duplicate DL row is inserted.
### Revisions
- `GET /api/v1/documents/{doc_id}/revisions` — 200 ordered by `seq_num`; empty list if none. 404 if document not found or voided.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/documents/11/revisions
```
- Schema references:
  - Response: `api/schemas/documents.py` `DocRevisionOut`
  - Update: `api/schemas/documents.py` `DocRevisionUpdate`
- Example response:
```json
[
  {
    "rev_id": 1,
    "doc_id": 11,
    "seq_num": 1,
    "rev_code_id": 6,
    "rev_code_name": "INDESIGN",
    "rev_code_acronym": "A",
    "rev_description": "IN-DESIGN",
    "rev_author_id": 1,
    "rev_originator_id": 1,
    "rev_modifier_id": 1,
    "transmital_current_revision": "TR-001",
    "milestone_id": 1,
    "milestone_name": "Issued for Construction",
    "planned_start_date": "2024-01-02T12:00:00Z",
    "planned_finish_date": "2024-01-05T12:00:00Z",
    "actual_start_date": null,
    "actual_finish_date": null,
    "canceled_date": null,
    "rev_status_id": 1,
    "rev_status_name": "InDesign",
    "as_built": false,
    "superseded": false,
    "modified_doc_date": "2024-01-05T12:00:00Z",
    "created_at": "2026-01-23T17:45:08.294332Z",
    "updated_at": "2026-01-23T17:45:08.294332Z",
    "created_by": 1,
    "updated_by": 1
  }
]
```
### Revision create
- `POST /api/v1/documents/{doc_id}/revisions` — 201; 404 if document or references not found.
- Note: `rev_status_id` is set to the global start status by the database; it is not accepted in the request body.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "rev_code_id": 6, "rev_author_id": 1, "rev_originator_id": 1, "rev_modifier_id": 1, "transmital_current_revision": "TR-NEW-001", "milestone_id": 1, "planned_start_date": "2024-01-02T12:00:00Z", "planned_finish_date": "2024-01-05T12:00:00Z", "actual_start_date": null, "actual_finish_date": null, "as_built": false, "modified_doc_date": "2024-01-05T12:00:00Z" }' \
  $API_BASE/api/v1/documents/11/revisions
```
- Example response:
```json
{
  "rev_id": 2,
  "doc_id": 11,
  "seq_num": 2,
  "rev_code_id": 6,
  "rev_code_name": "INDESIGN",
  "rev_code_acronym": "A",
  "rev_description": "IN-DESIGN",
  "rev_author_id": 1,
  "rev_originator_id": 1,
  "rev_modifier_id": 1,
  "transmital_current_revision": "TR-NEW-001",
  "milestone_id": 1,
  "milestone_name": "Issued for Construction",
  "planned_start_date": "2024-01-02T12:00:00Z",
  "planned_finish_date": "2024-01-05T12:00:00Z",
  "actual_start_date": null,
  "actual_finish_date": null,
  "canceled_date": null,
  "rev_status_id": 1,
  "rev_status_name": "InDesign",
  "as_built": false,
  "superseded": false,
  "modified_doc_date": "2024-01-05T12:00:00Z"
}
```
### Revision update
- `PUT /api/v1/documents/revisions/{rev_id}` — 200; 400 if no fields; 404 if revision not found.
- Note: `rev_status_id` is not supported by this endpoint. Use the status transition endpoint below.
- Note: `rev_code_id` is not supported by this endpoint after revision creation. Use the overview-transition endpoint below when progressing from a current final revision.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "transmital_current_revision": "TR-UPDATED-001" }' \
  $API_BASE/api/v1/documents/revisions/1
```
- Example response:
```json
{
  "rev_id": 1,
  "doc_id": 11,
  "seq_num": 1,
  "rev_code_id": 1,
  "rev_code_name": "IDC",
  "rev_code_acronym": "B",
  "rev_description": "INTERDISCIPLINE CHECK",
  "rev_author_id": 1,
  "rev_originator_id": 1,
  "rev_modifier_id": 1,
  "transmital_current_revision": "TR-UPDATED-001",
  "milestone_id": 1,
  "milestone_name": "Issued for Construction",
  "planned_start_date": "2024-01-02T12:00:00Z",
  "planned_finish_date": "2024-01-05T12:00:00Z",
  "actual_start_date": null,
  "actual_finish_date": null,
  "canceled_date": null,
  "rev_status_id": 1,
  "rev_status_name": "InDesign",
  "as_built": false,
  "superseded": false,
  "modified_doc_date": "2024-01-05T12:00:00Z"
}
```
### Revision overview transition
- `POST /api/v1/documents/revisions/{rev_id}/overview-transition` — 200; 404 if revision/document not found; 409 if the source revision is not the current final revision, no next revision-overview step can be resolved, or another active revision already uses the target `rev_code_id`; 422 for validation errors.
- Contract notes:
  - The request body is the empty JSON object `{}`.
  - The source revision row remains unchanged.
  - The backend resolves the new revision’s `rev_code_id` from `ref.revision_overview.next_rev_code_id`.
  - The new revision is inserted with the workflow start status from `doc_rev_statuses`.
  - `core.doc.rev_actual_id` is set to the source final revision and `core.doc.rev_current_id` is set to the newly created revision.
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{}' \
  $API_BASE/api/v1/documents/revisions/1/overview-transition
```
- Example response:
```json
{
  "rev_id": 12,
  "doc_id": 11,
  "seq_num": 2,
  "rev_code_id": 1,
  "rev_code_name": "IDC",
  "rev_code_acronym": "B",
  "rev_description": "INTERDISCIPLINE CHECK",
  "rev_author_id": 1,
  "rev_originator_id": 1,
  "rev_modifier_id": 1,
  "transmital_current_revision": "TR-001",
  "milestone_id": null,
  "milestone_name": null,
  "planned_start_date": "2024-01-02T12:00:00Z",
  "planned_finish_date": "2024-01-05T12:00:00Z",
  "actual_start_date": null,
  "actual_finish_date": null,
  "canceled_date": null,
  "rev_status_id": 1,
  "rev_status_name": "InDesign",
  "as_built": false,
  "superseded": false,
  "modified_doc_date": "2026-03-25T11:00:00Z",
  "created_at": "2026-03-25T11:00:00Z",
  "updated_at": "2026-03-25T11:00:00Z",
  "created_by": 2,
  "updated_by": 2
}
```
### Revision status transition
- `POST /api/v1/documents/revisions/{rev_id}/status-transitions` — 200; 422 for invalid direction/validation errors; 404 if revision/document not found; 409 if start/final/revertible rules block the transition.
- Contract notes:
  - `direction="forward"` moves only to the current status row's `next_rev_status_id`.
  - `direction="back"` moves only to the unique immediate predecessor status whose `next_rev_status_id` equals the current status.
  - `direction="back"` is rejected when the current status is `start=true`.
  - `direction="back"` is rejected when the current status has `revertible=false`.
  - The status graph forbids ambiguous predecessor configurations; if a predecessor were absent for a non-start revertible status, the transition would fail.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "direction": "forward" }' \
  $API_BASE/api/v1/documents/revisions/1/status-transitions
```
- Example response:
```json
{
  "rev_id": 1,
  "doc_id": 11,
  "seq_num": 1,
  "rev_code_id": 6,
  "rev_code_name": "INDESIGN",
  "rev_code_acronym": "A",
  "rev_description": "IN-DESIGN",
  "rev_author_id": 1,
  "rev_originator_id": 1,
  "rev_modifier_id": 1,
  "transmital_current_revision": "TR-UPDATED-001",
  "milestone_id": 1,
  "milestone_name": "Issued for Construction",
  "planned_start_date": "2024-01-02T12:00:00Z",
  "planned_finish_date": "2024-01-05T12:00:00Z",
  "actual_start_date": null,
  "actual_finish_date": null,
  "canceled_date": null,
  "rev_status_id": 2,
  "rev_status_name": "IDC",
  "as_built": false,
  "superseded": false,
  "modified_doc_date": "2024-01-05T12:00:00Z"
}
```
### Revision supersede
- `POST /api/v1/documents/revisions/{rev_id}/supersede` — 200; creates a replacement revision with the same `rev_code_id` and marks the source revision `superseded=true`; 404 if revision not found; 409 if the source revision is not current, is canceled, is already superseded, or is final.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" -X POST \
  -d '{ "rev_author_id": 1, "rev_originator_id": 1, "rev_modifier_id": 1, "transmital_current_revision": "TR-SUP-001", "planned_start_date": "2024-01-02T12:00:00Z", "planned_finish_date": "2024-01-05T12:00:00Z" }' \
  $API_BASE/api/v1/documents/revisions/1/supersede
```
- Example response:
```json
{
  "rev_id": 2,
  "doc_id": 11,
  "seq_num": 2,
  "rev_code_id": 6,
  "rev_code_name": "INDESIGN",
  "rev_code_acronym": "A",
  "rev_description": "IN-DESIGN",
  "rev_author_id": 1,
  "rev_originator_id": 1,
  "rev_modifier_id": 1,
  "transmital_current_revision": "TR-SUP-001",
  "milestone_id": 1,
  "milestone_name": "Issued for Construction",
  "planned_start_date": "2024-01-02T12:00:00Z",
  "planned_finish_date": "2024-01-05T12:00:00Z",
  "actual_start_date": null,
  "actual_finish_date": null,
  "canceled_date": null,
  "rev_status_id": 1,
  "rev_status_name": "INDESIGN",
  "as_built": false,
  "superseded": false,
  "modified_doc_date": "2024-01-05T12:00:00Z"
}
```
### Revision cancel
- `PATCH /api/v1/documents/revisions/{rev_id}/cancel` — 200; 404 if revision/document not found (or voided); 409 if revision status is final. Idempotent: if already canceled, returns existing state.
- Permissions: none enforced by API (auth TBD).
- Side effects: sets `canceled_date` on the revision.
- Visibility: canceled revisions are excluded from standard `GET /api/v1/documents/{doc_id}/revisions` responses.
- Example request:
```bash
curl -sS -H "Accept: application/json" -X PATCH \
  $API_BASE/api/v1/documents/revisions/1/cancel
```
- Example response:
```json
{
  "rev_id": 1,
  "doc_id": 11,
  "seq_num": 1,
  "rev_code_id": 6,
  "rev_code_name": "INDESIGN",
  "rev_code_acronym": "A",
  "rev_description": "IN-DESIGN",
  "rev_author_id": 1,
  "rev_originator_id": 1,
  "rev_modifier_id": 1,
  "transmital_current_revision": "TR-UPDATED-001",
  "milestone_id": 1,
  "milestone_name": "Issued for Construction",
  "planned_start_date": "2024-01-02T12:00:00Z",
  "planned_finish_date": "2024-01-05T12:00:00Z",
  "actual_start_date": null,
  "actual_finish_date": null,
  "canceled_date": "2026-02-06T18:30:00Z",
  "rev_status_id": 2,
  "rev_status_name": "IDC",
  "as_built": false,
  "superseded": false,
  "modified_doc_date": "2024-01-05T12:00:00Z"
}
```
### Update
- `PUT /api/v1/documents/{doc_id}` — 200; updates a document; 400 if no fields/uniqueness/null required field; 404 if document not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "title": "Piping Iso 001 (Updated)" }' \
  $API_BASE/api/v1/documents/11
```
- Example response:
```json
{
  "doc_id": 11,
  "doc_name_unique": "PRJ-ISO-001",
  "title": "Piping Iso 001 (Updated)",
  "project_id": 3,
  "project_name": "Delta Expansion",
  "jobpack_id": 5,
  "jobpack_name": "JP-01",
  "type_id": 7,
  "doc_type_name": "Piping Iso",
  "doc_type_acronym": "ISO",
  "area_id": 1,
  "area_name": "Newfoundland",
  "area_acronym": "NFLD",
  "unit_id": 2,
  "unit_name": "North Wing",
  "rev_actual_id": null,
  "rev_current_id": 1,
  "rev_seq_num": 1,
  "discipline_id": 2,
  "discipline_name": "Piping",
  "discipline_acronym": "PIP",
  "rev_code_name": "INDESIGN",
  "rev_code_acronym": "A",
  "rev_status_id": 1,
  "rev_status_name": "InDesign",
  "percentage": 0,
  "voided": false,
  "created_at": "2026-01-23T17:45:08.294332Z",
  "updated_at": "2026-02-11T09:15:00Z",
  "created_by": 1,
  "updated_by": 1
}
```
- Body includes any of: `doc_name_unique`, `title`, `project_id`, `jobpack_id`, `type_id`, `area_id`, `unit_id`, `rev_actual_id`, `rev_current_id`. 
- Requires at least one updatable field. Validates references (project, jobpack, type, area, unit, revisions) and uniqueness of `doc_name_unique`. Returns the updated document.
### Delete
- `DELETE /api/v1/documents/{doc_id}` — 200 with `{ "result": "deleted" }` or `{ "result": "voided" }`; deletes a document if only one revision in start status, otherwise voids. 404 if not found.
- Permissions: none enforced by API (auth TBD).
- Side effects: hard delete cascades to revisions/files/comments; voiding updates the document only.

## Distribution Lists
Shape (distribution list):
```json
{
  "dist_id": 1,
  "distribution_list_name": "Review Team",
  "doc_id": null
}
```
Shape (distribution list member):
```json
{
  "dist_id": 1,
  "user_id": 2,
  "person_id": 2,
  "user_acronym": "FDQC",
  "person_name": "Aleksey Krutskih"
}
```
Schema references:
- Create list: `api/schemas/distribution_lists.py` `DistributionListCreate`
- List row: `api/schemas/distribution_lists.py` `DistributionListOut`
- Add member: `api/schemas/distribution_lists.py` `DistributionListMemberCreate`
- Member row: `api/schemas/distribution_lists.py` `DistributionListMemberOut`
Backend implementation:
- Router: `api/routers/distribution_lists.py`
- DB functions: `workflow.create_distribution_list`, `workflow.delete_distribution_list`, `workflow.add_distribution_list_member`, `workflow.remove_distribution_list_member`

### List
- `GET /api/v1/distribution-lists` — 200; returns distribution lists ordered by name and id.
- Optional query param: `doc_id` to return only lists linked to that document.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  "$API_BASE/api/v1/distribution-lists?doc_id=101"
```
- Example response:
```json
[
  { "dist_id": 1, "distribution_list_name": "Review Team", "doc_id": null },
  { "dist_id": 2, "distribution_list_name": "Construction Team", "doc_id": 101 }
]
```

### Create
- `POST /api/v1/distribution-lists` — 201; creates a distribution list (global when `doc_id` is omitted/null).
- Returns `404` when `doc_id` is provided but the document does not exist.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "distribution_list_name": "Review Team", "doc_id": 101 }' \
  $API_BASE/api/v1/distribution-lists
```
- Example response:
```json
{ "dist_id": 1, "distribution_list_name": "Review Team", "doc_id": 101 }
```

### Delete
- `DELETE /api/v1/distribution-lists/{dist_id}` — 200 with `{ "result": "ok" }`; removes the list and membership rows.
- Returns `409` if the list is referenced by notifications.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -X DELETE -H "Accept: application/json" \
  $API_BASE/api/v1/distribution-lists/1
```
- Example response:
```json
{ "result": "ok" }
```

### List members
- `GET /api/v1/distribution-lists/{dist_id}/members` — 200; returns users in the list.
- Returns `404` if distribution list does not exist.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  $API_BASE/api/v1/distribution-lists/1/members
```
- Example response:
```json
[
  {
    "dist_id": 1,
    "user_id": 2,
    "person_id": 2,
    "user_acronym": "FDQC",
    "person_name": "Aleksey Krutskih"
  }
]
```

### Add member
- `POST /api/v1/distribution-lists/{dist_id}/members` — 201; adds user membership.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "user_id": 2 }' \
  $API_BASE/api/v1/distribution-lists/1/members
```
- Example response:
```json
{
  "dist_id": 1,
  "user_id": 2,
  "person_id": 2,
  "user_acronym": "FDQC",
  "person_name": "Aleksey Krutskih"
}
```

### Remove member
- `DELETE /api/v1/distribution-lists/{dist_id}/members/{user_id}` — 200 with `{ "result": "ok" }`; removes user membership.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -X DELETE -H "Accept: application/json" \
  $API_BASE/api/v1/distribution-lists/1/members/2
```
- Example response:
```json
{ "result": "ok" }
```

## Notifications
Shape (inbox item):
```json
{
  "notification_id": 10,
  "sender_user_id": 1,
  "event_type": "regular",
  "title": "Review update",
  "body": "Please review the latest revision.",
  "remark": "manual send",
  "rev_id": 51,
  "commented_file_id": null,
  "created_at": "2026-02-06T18:20:00Z",
  "dropped_at": null,
  "dropped_by_user_id": null,
  "superseded_by_notification_id": null,
  "recipient_user_id": 2,
  "delivered_at": "2026-02-06T18:20:00Z",
  "read_at": null
}
```
Schema references:
- Create: `api/schemas/notifications.py` `NotificationCreate`
- Replace: `api/schemas/notifications.py` `NotificationReplace`
- Delete: `api/schemas/notifications.py` `NotificationDelete`
- Read mark: `api/schemas/notifications.py` `NotificationMarkRead`
- Inbox rows: `api/schemas/notifications.py` `NotificationOut`
- Action result: `api/schemas/notifications.py` `NotificationActionResult`
Backend implementation:
- Router: `api/routers/notifications.py`
- DB functions: `workflow.create_notification`, `workflow.replace_notification`, `workflow.delete_notification`, `workflow.mark_notification_read`

### Create
- `POST /api/v1/notifications` — 201; creates notification, resolves recipients, stores unread delivery rows.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Sender resolution:
  - sender always resolves from effective session identity (`X-User-Id` / trusted auth context).
  - request-body `sender_user_id` is not accepted.
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -H "X-User-Id: FDQC" \
  -d '{
    "title": "Review update",
    "body": "Please review revision 51",
    "rev_id": 51,
    "recipient_user_ids": [2],
    "recipient_dist_ids": [1],
    "remark": "manual send"
  }' \
  $API_BASE/api/v1/notifications
```
- Example response:
```json
{ "notification_id": 10, "recipient_count": 3 }
```

### List (recipient inbox)
- `GET /api/v1/notifications` — 200; returns recipient inbox rows ordered by `delivered_at DESC, notification_id DESC`.
- Recipient resolution:
  - Inbox rows are always resolved from the effective session identity (`Authorization` / trusted auth context / allowed `X-User-Id` fallback).
  - Cross-user recipient override is not supported on this endpoint.
  - Router authentication still requires an effective identity for the request; missing identity returns `401`.
- Query params:
  - `unread_only` (bool, optional)
  - `sender_user_id` (int, optional)
  - `date_from` / `date_to` (ISO datetime, optional)
- Validation:
  - `date_from > date_to` returns `400`.
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  -H "X-User-Id: FDQC" \
  "$API_BASE/api/v1/notifications?unread_only=true"
```
- Example response:
```json
[
  {
    "notification_id": 10,
    "sender_user_id": 1,
    "event_type": "regular",
    "title": "Review update",
    "body": "Please review revision 51",
    "remark": "manual send",
    "rev_id": 51,
    "commented_file_id": null,
    "created_at": "2026-02-06T18:20:00Z",
    "dropped_at": null,
    "dropped_by_user_id": null,
    "superseded_by_notification_id": null,
    "recipient_user_id": 2,
    "delivered_at": "2026-02-06T18:20:00Z",
    "read_at": null
  }
]
```

### Replace
- `POST /api/v1/notifications/{notification_id}/replace` — 200; drops original notification and creates linked `changed_notice`.
- Headers: `Accept: application/json`, `Content-Type: application/json`, `X-User-Id` (required)
- Permissions: sender or superuser only.
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{ "title": "Review update (changed)", "body": "Updated message", "remark": "changed" }' \
  $API_BASE/api/v1/notifications/10/replace
```
- Example response:
```json
{ "notification_id": 11, "recipient_count": 3 }
```

### Drop
- `POST /api/v1/notifications/{notification_id}/delete` — 200; drops original notification and creates linked `dropped_notice`.
- Headers: `Accept: application/json`, `Content-Type: application/json`, `X-User-Id` (required)
- Permissions: sender or superuser only.
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{ "remark": "no longer valid" }' \
  $API_BASE/api/v1/notifications/10/delete
```
- Example response:
```json
{ "notification_id": 12, "recipient_count": 3 }
```

### Mark as read
- `POST /api/v1/notifications/{notification_id}/read` — 200; marks current recipient delivery row as read (idempotent).
- Headers: `Accept: application/json`, `Content-Type: application/json`, `X-User-Id` (required)
- Request body: empty JSON `{}`.
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -H "X-User-Id: 2" \
  -d '{}' \
  $API_BASE/api/v1/notifications/10/read
```
- Example response:
```json
{
  "notification_id": 10,
  "recipient_user_id": 2,
  "delivered_at": "2026-02-06T18:20:00Z",
  "read_at": "2026-02-06T18:30:00Z"
}
```

## Error responses
- `400` — Validation failed (missing required fields, duplicate/uniqueness, duplicate permissions, etc.).
- `404` — Resource not found (including missing parent resources for nested lists).
- All errors follow FastAPI's standard shape:
```json
{ "detail": "Reason for failure" }
```

## References
- `api/routers/`
- `api/schemas/`
- `documentation/api_db_rules.md`
