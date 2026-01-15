# Flow API Interfaces

Current FastAPI surface (version 0.1.0). All endpoints are JSON unless noted, live under the backend root (no global prefix), and are CORS-open for any origin. Default database URL is `postgresql+psycopg://flow_user:flow_pass@postgres:5432/flow_db`; override via `DATABASE_URL`. Object storage defaults to `MINIO_ENDPOINT=minio:9000` and `MINIO_BUCKET=flow-default`; override with `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_SECURE`.

Update conventions (PUT/PATCH):
- `PUT` is idempotent and used for updates; this API accepts partial updates via `PUT` (fields may be omitted unless noted).
- If the request body includes an id field, it must match the path id; on mismatch return `400 Bad Request` with body:
```json
{ "detail": "<id_field> mismatch" }
```
- `PATCH` endpoints are not currently provided; consider adding `PATCH` for partial updates if needed.

Delete conventions:
- `DELETE /resource/{id}` does not accept a request body.
- Success returns `204 No Content`.
- If the resource does not exist, return `404 Not Found`.
- Idempotent delete (returning `204` when the resource is already deleted) is not currently documented; implement and document if desired.

## Health and root
- `GET /` — Returns `{"message": "Flow backend is running"}`.
- `GET /health` — Returns `{"status": "ok"}`.

# Lookups

Create conventions:
- `POST` (Create) returns `201 Created`.
- Response body includes the created resource (or at least the new id).
- `Location` header points to the new resource, e.g. `Location: /api/v1/lookups/areas/{area_id}`.

## Areas
Shape (single item):
```json
{ "area_id": 1, "area_name": "Newfoundland", "area_acronym": "NFLD" }
```
### List
- `GET /api/v1/lookups/areas` — 200 sorted by `area_name`; empty list if no areas.
- Example response:
```json
[ { "area_id": 1, "area_name": "Newfoundland", "area_acronym": "NFLD" } ]
```
### Create
- `POST /api/v1/lookups/areas` — 201; 400 on uniqueness.
- Body:
```json
{ "area_name": "Newfoundland", "area_acronym": "NFLD" }
```
- Response:
```json
{ "area_id": 1, "area_name": "Newfoundland", "area_acronym": "NFLD" }
```
### Update
- `PUT /api/v1/lookups/areas/{area_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body (at least one optional field):
```json
{ "area_id": 1, "area_name": "Updated Name", "area_acronym": "UPD" }
```
### Delete
- `DELETE /api/v1/lookups/areas/{area_id}` — 204; 404 if not found.

## Disciplines
Shape (single item):
```json
{ "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" }
```
### List
- `GET /api/v1/lookups/disciplines` — 200 sorted by `discipline_name`; 404 if empty.
- Example response:
```json
[ { "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" } ]
```
### Create
- `POST /api/v1/lookups/disciplines` — 201; 400 on uniqueness.
- Body:
```json
{ "discipline_name": "Structural", "discipline_acronym": "STR" }
```
### Update
- `PUT /api/v1/lookups/disciplines/{discipline_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body:
```json
{ "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" }
```
### Delete
- `DELETE /api/v1/lookups/disciplines/{discipline_id}` — 204; 404 if not found.

## Projects
Shape (single item):
```json
{ "project_id": 3, "project_name": "Delta Expansion" }
```
### List
- `GET /api/v1/lookups/projects` — 200 sorted by `project_name`; 404 if empty.
- Example response:
```json
[ { "project_id": 3, "project_name": "Delta Expansion" } ]
```
### Create
- `POST /api/v1/lookups/projects` — 201; 400 on uniqueness.
- Body:
```json
{ "project_name": "Delta Expansion" }
```
### Update
- `PUT /api/v1/lookups/projects/{project_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body:
```json
{ "project_id": 3, "project_name": "Updated Project" }
```
### Delete
- `DELETE /api/v1/lookups/projects/{project_id}` — 204; 404 if not found.

## Units
Shape (single item):
```json
{ "unit_id": 2, "unit_name": "North Wing" }
```
### List
- `GET /api/v1/lookups/units` — 200 sorted by `unit_name`; 404 if empty.
- Example response:
```json
[ { "unit_id": 2, "unit_name": "North Wing" } ]
```
### Create
- `POST /api/v1/lookups/units` — 201; 400 on uniqueness.
- Body:
```json
{ "unit_name": "North Wing" }
```
### Update
- `PUT /api/v1/lookups/units/{unit_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body:
```json
{ "unit_id": 2, "unit_name": "Main Floor" }
```
### Delete
- `DELETE /api/v1/lookups/units/{unit_id}` — 204; 404 if not found.

## Jobpacks
Shape (single item):
```json
{ "jobpack_id": 5, "jobpack_name": "JP-01" }
```
### List
- `GET /api/v1/lookups/jobpacks` — 200 sorted by `jobpack_name`; 404 if empty.
- Example response:
```json
[ { "jobpack_id": 5, "jobpack_name": "JP-01" } ]
```
### Create
- `POST /api/v1/lookups/jobpacks` — 201; 400 on uniqueness.
- Body:
```json
{ "jobpack_name": "JP-01" }
```
### Update
- `PUT /api/v1/lookups/jobpacks/{jobpack_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body:
```json
{ "jobpack_id": 5, "jobpack_name": "JP-01B" }
```
### Delete
- `DELETE /api/v1/lookups/jobpacks/{jobpack_id}` — 204; 404 if not found.

## Doc revision milestones
Shape (single item):
```json
{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }
```
### List
- `GET /api/v1/documents/doc_rev_milestones` — 200 sorted by `milestone_name`; 404 if empty.
- Example response:
```json
[ { "milestone_id": 4, "milestone_name": "IFC", "progress": 90 } ]
```
### Create
- `POST /api/v1/documents/doc_rev_milestones` — 201; 400 on uniqueness.
- Body:
```json
{ "milestone_name": "Issued for Construction", "progress": 80 }
```
### Update
- `PUT /api/v1/documents/doc_rev_milestones/{milestone_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body:
```json
{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }
```
### Delete
- `DELETE /api/v1/documents/doc_rev_milestones/{milestone_id}` — 204; 404 if not found.

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
### List
- `GET /api/v1/documents/revision_overview` — 200 sorted by `rev_code_name`; 404 if empty.
- Example response:
```json
[ { "rev_code_id": 5, "rev_code_name": "IFC", "rev_code_acronym": "E", "rev_description": "Issued for Construction", "percentage": 90 } ]
```
### Create
- `POST /api/v1/documents/revision_overview` — 201; 400 on uniqueness.
- Body:
```json
{
  "rev_code_name": "IFC",
  "rev_code_acronym": "E",
  "rev_description": "Issued for Construction",
  "percentage": 90
}
```
### Update
- `PUT /api/v1/documents/revision_overview/{rev_code_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body:
```json
{
  "rev_code_id": 5,
  "rev_code_name": "AFC",
  "rev_code_acronym": "C",
  "rev_description": "Approved for Construction",
  "percentage": 100
}
```
### Delete
- `DELETE /api/v1/documents/revision_overview/{rev_code_id}` — 204; 404 if not found.

## Doc revision status UI behaviors
Shape (single item):
```json
{ "ui_behavior_id": 1, "ui_behavior_name": "Default", "ui_behavior_file": "default.json" }
```
### List
- `GET /api/v1/lookups/doc_rev_status_ui_behaviors` — 200 sorted by `ui_behavior_name`; 404 if empty.
- Example response:
```json
[ { "ui_behavior_id": 1, "ui_behavior_name": "Default", "ui_behavior_file": "default.json" } ]
```
### Create
- `POST /api/v1/lookups/doc_rev_status_ui_behaviors` — 201; 400 on uniqueness.
- Body:
```json
{ "ui_behavior_name": "Default", "ui_behavior_file": "default.json" }
```
### Update
- `PUT /api/v1/lookups/doc_rev_status_ui_behaviors/{ui_behavior_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body:
```json
{ "ui_behavior_id": 1, "ui_behavior_name": "Updated Behavior", "ui_behavior_file": "updated.json" }
```
### Delete
- `DELETE /api/v1/lookups/doc_rev_status_ui_behaviors/{ui_behavior_id}` — 204; 404 if not found.

## Doc revision statuses
Shape (single item):
```json
{ "rev_status_id": 2, "rev_status_name": "In review" }
```
### List
- `GET /api/v1/lookups/doc_rev_statuses` — 200 sorted by `rev_status_name`; 404 if empty.
- Example response:
```json
[ { "rev_status_id": 2, "rev_status_name": "In review" } ]
```
### Create
- `POST /api/v1/lookups/doc_rev_statuses` — 201; 400 on uniqueness or invalid state (final status with next_status, non-final without next_status, final with editable/revertible).
- Body:
```json
{ "rev_status_name": "In review" }
```
### Update
- `PUT /api/v1/lookups/doc_rev_statuses/{rev_status_id}` — 200; 400 if no fields/uniqueness/ID mismatch/invalid state; 404 if not found.
- Body:
```json
{ "rev_status_id": 2, "rev_status_name": "In progress" }
```
### Delete
- `DELETE /api/v1/lookups/doc_rev_statuses/{rev_status_id}` — 204; 404 if not found.

# Files

Create conventions:
- `POST` (Create) returns `201 Created`.
- Response body includes the created resource (or at least the new id).
- `Location` header points to the new resource, e.g. `Location: /api/v1/files/{id}`.

Shape (single item):
```json
{
  "id": 12,
  "filename": "report.pdf",
  "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
  "mimetype": "application/pdf",
  "rev_id": 45
}
```

### List
- `GET /api/v1/files?rev_id=45` — 200 sorted by `filename`; empty list if none.

### Create (multipart)
- `POST /api/v1/files` — 201; multipart form.
- Form fields: `rev_id` (int), `file` (binary).
- Response: file shape.

### Update
- `PUT /api/v1/files/{id}` — 200; updates filename; 404 if not found.
- Body:
```json
{ "id": 12, "filename": "new_report.pdf" }
```

### Delete
- `DELETE /api/v1/files/{id}` — 204; deletes MinIO object and DB row; 404 if not found.

### Download
- `GET /api/v1/files/{file_id}/download` — streams the file with `Content-Disposition: attachment` and `ETag`/`Last-Modified`.

# Files (commented)

Create conventions:
- `POST` (Create) returns `201 Created`.
- Response body includes the created resource (or at least the new id).
- `Location` header points to the new resource, e.g. `Location: /api/v1/files/commented/{id}`.

Shape (single item):
```json
{
  "id": 3,
  "file_id": 12,
  "user_id": 1,
  "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
  "filename": "report.pdf",
  "mimetype": "application/pdf",
  "rev_id": 45
}
```

### List
- `GET /api/v1/files/commented/list?file_id=12` — 200; optional `user_id` filter.

### Create (multipart)
- `POST /api/v1/files/commented` — 201; multipart form.
- Form fields: `file_id` (int), `user_id` (int), `file` (binary).
- Validates mimetype against the original file; rejects duplicates per `(file_id, user_id)`.

### Delete
- `DELETE /api/v1/files/commented/{id}` — 204; deletes MinIO object and DB row; 404 if not found.

### Download
- `GET /api/v1/files/commented/download?file_id=3` — streams the commented file.
- `Content-Disposition` filename is `<original>_commented_by_<user_acronym>`.

# Persons/users/permissions

Create conventions:
- `POST` (Create) returns `201 Created`.
- Response body includes the created resource (or at least the new id).
- `Location` header points to the new resource, e.g. `Location: /api/v1/people/users/{user_id}`.

## Roles
Shape (single item):
```json
{ "role_id": 10, "role_name": "Coordinator" }
```
### List
- `GET /api/v1/people/roles` — 200 sorted by `role_name`; 404 if empty.
- Example response:
```json
[ { "role_id": 10, "role_name": "Coordinator" } ]
```
### Create
- `POST /api/v1/people/roles` — 201; 400 on uniqueness.
- Body:
```json
{ "role_name": "Coordinator" }
```
### Update
- `PUT /api/v1/people/roles/{role_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Body:
```json
{ "role_id": 10, "role_name": "Lead Coordinator" }
```
### Delete
- `DELETE /api/v1/people/roles/{role_id}` — 204; 404 if not found.

## People
Shape (single item):
```json
{ "person_id": 12, "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" }
```
### List
- `GET /api/v1/people/persons` — 200 sorted by `person_name`; 404 if empty.
- Example response:
```json
[ { "person_id": 12, "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" } ]
```
### Create
- `POST /api/v1/people/persons` — 201; 400 on insert failure.
- Body:
```json
{ "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" }
```
### Update
- `PUT /api/v1/people/persons/{person_id}` — 200; 400 if no fields/ID mismatch; 404 if not found.
- Body:
```json
{ "person_id": 12, "person_name": "Grace Hopper", "photo_s3_uid": null }
```
### Delete
- `DELETE /api/v1/people/persons/{person_id}` — 204; 404 if not found.

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
### List
- `GET /api/v1/people/users` — 200 sorted by `user_acronym`; 404 if empty.
- Example response:
```json
[ { "user_id": 7, "person_id": 12, "user_acronym": "ALV", "role_id": 3, "person_name": "Ada Lovelace", "role_name": "Coordinator" } ]
```
### Create
- `POST /api/v1/people/users` — 201; 400 on insert failure; 404 if person/role missing.
- Body:
```json
{ "person_id": 12, "user_acronym": "ALV", "role_id": 3 }
```
### Update
- `PUT /api/v1/people/users/{user_id}` — 200; 400 if no fields/update fails/ID mismatch; 404 if user/person/role missing.
- Body:
```json
{ "user_id": 7, "person_id": 12, "user_acronym": "ALV2", "role_id": 4 }
```
### Delete
- `DELETE /api/v1/people/users/{user_id}` — 204; 404 if not found.

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
At least one of `project_id` or `discipline_id` is required.
### List
- `GET /api/v1/people/permissions` — 200 sorted by `user_id`; 404 if empty.
- Example response:
```json
[ { "permission_id": 42, "user_id": 7, "project_id": 3, "discipline_id": 2, "user_acronym": "ALV", "person_name": "Ada Lovelace", "project_name": "Delta Expansion", "discipline_name": "Piping" } ]
```
### Create
- `POST /api/v1/people/permissions` — 201; 400 if duplicate or scope missing; 404 if user/project/discipline missing.
- Body (at least one scope):
```json
{ "user_id": 7, "project_id": 3, "discipline_id": 2 }
```
### Update
- `PUT /api/v1/people/permissions/{permission_id}` — 200; 400 if no new scope/duplicate/ID mismatch; 404 if missing references or permission.
- Body (permission_id or current scope plus new scope):
```json
{
  "permission_id": 42,
  "user_id": 7,
  "project_id": 3,
  "discipline_id": 2,
  "new_project_id": 4,
  "new_discipline_id": null
}
```
### Delete
- `DELETE /api/v1/people/permissions/{permission_id}` — 204; 400 if scope missing; 404 if not found.
- Body (permission_id or scope):
```json
{ "permission_id": 42, "user_id": 7, "project_id": 3, "discipline_id": 2 }
```

# Docs

Create conventions:
- `POST` (Create) returns `201 Created`.
- Response body includes the created resource (or at least the new id).
- `Location` header points to the new resource, e.g. `Location: /api/v1/documents/{doc_id}`.

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
### List
- `GET /api/v1/documents/doc_types` — 200 sorted by `doc_type_name`; includes discipline info; 404 if empty.
- Example response:
```json
[ { "type_id": 7, "doc_type_name": "Piping Iso", "ref_discipline_id": 2, "doc_type_acronym": "ISO", "discipline_name": "Piping", "discipline_acronym": "PIP" } ]
```
### Create
- `POST /api/v1/documents/doc_types` — 201; 400 on uniqueness; 404 if discipline missing.
- Body:
```json
{ "doc_type_name": "Piping Iso", "ref_discipline_id": 2, "doc_type_acronym": "ISO" }
```
### Update
- `PUT /api/v1/documents/doc_types/{type_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if doc type or discipline missing.
- Body:
```json
{
  "type_id": 7,
  "doc_type_name": "Piping Iso Updated",
  "ref_discipline_id": 3,
  "doc_type_acronym": "ISO-U"
}
```
### Delete
- `DELETE /api/v1/documents/doc_types/{type_id}` — 204; 404 if not found.

## Documents
Shape (single item) includes doc, linked names, and discipline/progress pointers:
`doc_id`, `doc_name_unique`, `title`, `project_id`/`project_name`, `jobpack_id`/`jobpack_name`, `type_id`/`doc_type_name`/`doc_type_acronym`, `area_id`/`area_name`/`area_acronym`, `unit_id`/`unit_name`, `rev_actual_id`, `rev_current_id`, `rev_seq_num`, `discipline_id`/`discipline_name`/`discipline_acronym`, `rev_code_name`, `rev_code_acronym`, `percentage`.
### List
- `GET /api/v1/documents?project_id=` — 200 ordered by `doc_name_unique`; 404 if none for the project. Requires `project_id` query param.
- Example response:
```json
[
  {
    "doc_id": 11,
    "doc_name_unique": "PRJ-ISO-001",
    "doc_name_uq": "PRJ-ISO-001",
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
    "percentage": 90
  }
]
```
### Update
- `PUT /api/v1/documents/{doc_id}` — 200; updates a document; 400 if no fields/uniqueness/ID mismatch; 404 if doc or references not found.
- Body includes `doc_id` plus any of: `doc_name_unique`, `title`, `project_id`, `jobpack_id`, `type_id`, `area_id`, `unit_id`, `rev_actual_id`, `rev_current_id`. 
- Requires at least one updatable field. Validates references (project, jobpack, type, area, unit, revisions) and uniqueness of `doc_name_unique`. Returns the updated document.

## Error responses
- `400` — Validation failed (missing required fields, duplicate/uniqueness, duplicate permissions, etc.).
- `404` — Resource not found or empty table.
- All errors follow FastAPI's standard shape:
```json
{ "detail": "Reason for failure" }
```
