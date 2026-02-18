# Flow API Interfaces

## Document Control
- Status: Approved
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-11
- Version: v1.3

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
- If the request body includes an id field, it must match the path id; on mismatch return `400 Bad Request` with body:
```json
{ "detail": "<id_field> mismatch" }
```
- Example (id mismatch):
```json
{ "detail": "area_id mismatch" }
```
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
- `400 Bad Request` — Domain validation, id mismatch, or duplicate/uniqueness violations.
- `401 Unauthorized` — Authentication required (not currently enforced in this API surface).
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
- DB triggers read the session setting `app.user` (a SMALLINT user id). The API sets it per request (via `set_config('app.user', ...)`) from the `X-User-Id` header when provided; otherwise it uses `DEFAULT_APP_USER` when configured (or leaves it empty).

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
  "rev_code_id": 5,
  "rev_code_name": "IFC",
  "rev_code_acronym": "E",
  "rev_description": "Issued for Construction",
  "percentage": 90
}
```
Schema references:
- Response: `api/schemas/documents.py` `RevisionOverviewOut`
### List
- `GET /api/v1/documents/revision_overview` — 200 sorted by `rev_code_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/documents/revision_overview
```
- Example response:
```json
[ { "rev_code_id": 5, "rev_code_name": "IFC", "rev_code_acronym": "E", "rev_description": "Issued for Construction", "percentage": 90 } ]
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
  -F "user_id=1" \
  -F "file=@commented.pdf;type=application/pdf" \
  $API_BASE/api/v1/files/commented/
```
- Form fields: `file_id` (int), `user_id` (int), `file` (binary).
- Validates mimetype against the original file; rejects duplicates per `(file_id, user_id)`.
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

### Delete
- `DELETE /api/v1/files/commented/{id}` — 204; deletes MinIO object and DB row; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE $API_BASE/api/v1/files/commented/{id}
```
- Example response: (empty)

### Download
- `GET /api/v1/files/commented/download?file_id=3` — streams the commented file.
- Returns `416` when a `Range` header is provided (range requests are not supported).
- Headers: `Accept: application/octet-stream`
- Example request:
```bash
curl -sS -H "Accept: application/octet-stream" \
  -o commented.pdf \
  $API_BASE/api/v1/files/commented/download?file_id=3
```
- Example response (binary):
```
<binary>
```
- `Content-Disposition` filename is `<original>_commented_by_<user_acronym>`.

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
{ "person_id": 12, "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" }
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
[ { "person_id": 12, "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" } ]
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
  "role_name": "Coordinator"
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
[ { "user_id": 7, "person_id": 12, "user_acronym": "ALV", "role_id": 3, "person_name": "Ada Lovelace", "role_name": "Coordinator" } ]
```
### Current user
- `GET /api/v1/people/users/current_user` — 200; returns current user (currently hardcoded to `user_id=2`); 404 if user not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" $API_BASE/api/v1/people/users/current_user
```
- Example response:
```json
{ "user_id": 2, "person_id": 1, "user_acronym": "USR", "role_id": 1, "person_name": "User", "role_name": "Viewer" }
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
  - Required fields: `doc_name_unique`, `title`, `type_id`, `area_id`, `unit_id`, `rev_code_id`, `rev_author_id`, `rev_originator_id`, `rev_modifier_id`, `transmital_current_revision`, `planned_start_date`, `planned_finish_date`
  - Optional fields: `project_id`, `jobpack_id`, `milestone_id`
  - Note: The initial revision automatically uses the status with `start=true` from `doc_rev_statuses`.
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
  "rev_status_id": 1,
  "rev_status_name": "InDesign",
  "as_built": false,
  "superseded": false,
  "modified_doc_date": "2024-01-05T12:00:00Z"
}
```
### Revision status transition
- `POST /api/v1/documents/revisions/{rev_id}/status-transitions` — 200; 422 for invalid direction/validation errors; 404 if revision/document not found; 409 if start/final/revertible rules block the transition.
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
### Revision cancel
- `PATCH /api/v1/documents/revisions/{rev_id}/cancel` — 200; 404 if revision/document not found (or voided); 409 if revision status is final. Idempotent: if already canceled, returns existing state.
- Permissions: none enforced by API (auth TBD).
- Side effects: sets `canceled_date` on the revision.
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
  "distribution_list_name": "Review Team"
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
- `GET /api/v1/distribution-lists` — 200; returns all distribution lists ordered by name and id.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  $API_BASE/api/v1/distribution-lists
```
- Example response:
```json
[
  { "dist_id": 1, "distribution_list_name": "Review Team" },
  { "dist_id": 2, "distribution_list_name": "Construction Team" }
]
```

### Create
- `POST /api/v1/distribution-lists` — 201; creates a global distribution list.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "distribution_list_name": "Review Team" }' \
  $API_BASE/api/v1/distribution-lists
```
- Example response:
```json
{ "dist_id": 1, "distribution_list_name": "Review Team" }
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
- Optional header/body sender resolution:
  - `sender_user_id` may be provided in body.
  - If omitted, API uses `X-User-Id` session user.
  - If neither is available, returns `400`.
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
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
  - Query `recipient_user_id` is optional.
  - If omitted, API uses `X-User-Id`.
  - If neither is available, returns `400`.
- Query params:
  - `recipient_user_id` (int, optional)
  - `unread_only` (bool, optional)
  - `sender_user_id` (int, optional)
  - `date_from` / `date_to` (ISO datetime, optional)
- Validation:
  - `date_from > date_to` returns `400`.
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  "$API_BASE/api/v1/notifications?recipient_user_id=2&unread_only=true"
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
