# Flow API Interfaces

Current FastAPI surface (version 0.1.0). All endpoints are JSON unless noted, live under the backend root (no global prefix), and are CORS-open for any origin. Default database URL is `postgresql+psycopg://flow_user:flow_pass@postgres:5432/flow_db`; override via `DATABASE_URL`. Object storage defaults to `MINIO_ENDPOINT=minio:9000` and `MINIO_BUCKET=flow-default`; override with `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_SECURE`.

## Health and root
- `GET /` — Returns `{"message": "Flow backend is running"}`.
- `GET /health` — Returns `{"status": "ok"}`.

# Lookups

## Areas
Shape (single item):
```json
{ "area_id": 1, "area_name": "Newfoundland", "area_acronym": "NFLD" }
```
### List
- `GET /api/v1/lookups/areas` — 200 sorted by `area_name`; 404 if empty.
- Example response:
```json
[ { "area_id": 1, "area_name": "Newfoundland", "area_acronym": "NFLD" } ]
```
### Insert
- `POST /api/v1/lookups/areas/insert` — 201; 400 on uniqueness.
- Body:
```json
{ "area_name": "Newfoundland", "area_acronym": "NFLD" }
```
- Response:
```json
{ "area_id": 1, "area_name": "Newfoundland", "area_acronym": "NFLD" }
```
### Update
- `PUT /api/v1/lookups/areas/update` — 200; 400 if no fields/uniqueness; 404 if not found.
- Body (at least one optional field):
```json
{ "area_id": 1, "area_name": "Updated Name", "area_acronym": "UPD" }
```
### Delete
- `DELETE /api/v1/lookups/areas/delete` — 204; 404 if not found.
- Body:
```json
{ "area_id": 1 }
```

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
### Insert
- `POST /api/v1/lookups/disciplines/insert` — 201; 400 on uniqueness.
- Body:
```json
{ "discipline_name": "Structural", "discipline_acronym": "STR" }
```
### Update
- `PUT /api/v1/lookups/disciplines/update` — 200; 400 if no fields/uniqueness; 404 if not found.
- Body:
```json
{ "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" }
```
### Delete
- `DELETE /api/v1/lookups/disciplines/delete` — 204; 404 if not found.
- Body:
```json
{ "discipline_id": 2 }
```

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
### Insert
- `POST /api/v1/lookups/projects/insert` — 201; 400 on uniqueness.
- Body:
```json
{ "project_name": "Delta Expansion" }
```
### Update
- `PUT /api/v1/lookups/projects/update` — 200; 400 if missing fields/uniqueness; 404 if not found.
- Body:
```json
{ "project_id": 3, "project_name": "Updated Project" }
```
### Delete
- `DELETE /api/v1/lookups/projects/delete` — 204; 404 if not found.
- Body:
```json
{ "project_id": 3 }
```

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
### Insert
- `POST /api/v1/lookups/units/insert` — 201; 400 on uniqueness.
- Body:
```json
{ "unit_name": "North Wing" }
```
### Update
- `PUT /api/v1/lookups/units/update` — 200; 400 if missing fields/uniqueness; 404 if not found.
- Body:
```json
{ "unit_id": 2, "unit_name": "Main Floor" }
```
### Delete
- `DELETE /api/v1/lookups/units/delete` — 204; 404 if not found.
- Body:
```json
{ "unit_id": 2 }
```

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
### Insert
- `POST /api/v1/lookups/jobpacks/insert` — 201; 400 on uniqueness.
- Body:
```json
{ "jobpack_name": "JP-01" }
```
### Update
- `PUT /api/v1/lookups/jobpacks/update` — 200; 400 if missing fields/uniqueness; 404 if not found.
- Body:
```json
{ "jobpack_id": 5, "jobpack_name": "JP-01B" }
```
### Delete
- `DELETE /api/v1/lookups/jobpacks/delete` — 204; 404 if not found.
- Body:
```json
{ "jobpack_id": 5 }
```

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
### Insert
- `POST /api/v1/documents/doc_rev_milestones/insert` — 201; 400 on uniqueness.
- Body:
```json
{ "milestone_name": "Issued for Construction", "progress": 80 }
```
### Update
- `PUT /api/v1/documents/doc_rev_milestones/update` — 200; 400 if no fields/uniqueness; 404 if not found.
- Body:
```json
{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }
```
### Delete
- `DELETE /api/v1/documents/doc_rev_milestones/delete` — 204; 404 if not found.
- Body:
```json
{ "milestone_id": 4 }
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
### List
- `GET /api/v1/documents/revision_overview` — 200 sorted by `rev_code_name`; 404 if empty.
- Example response:
```json
[ { "rev_code_id": 5, "rev_code_name": "IFC", "rev_code_acronym": "E", "rev_description": "Issued for Construction", "percentage": 90 } ]
```
### Insert
- `POST /api/v1/documents/revision_overview/insert` — 201; 400 on uniqueness.
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
- `PUT /api/v1/documents/revision_overview/update` — 200; 400 if no fields/uniqueness; 404 if not found.
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
- `DELETE /api/v1/documents/revision_overview/delete` — 204; 404 if not found.
- Body:
```json
{ "rev_code_id": 5 }
```

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
### Insert
- `POST /api/v1/lookups/doc_rev_statuses/insert` — 201; 400 on uniqueness.
- Body:
```json
{ "rev_status_name": "In review" }
```
### Update
- `PUT /api/v1/lookups/doc_rev_statuses/update` — 200; 400 if missing fields/uniqueness; 404 if not found.

# Files

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
- `GET /api/v1/files/list?rev_id=45` — 200 sorted by `filename`; empty list if none.

### Insert (multipart)
- `POST /api/v1/files/insert` — 201; multipart form.
- Form fields: `rev_id` (int), `file` (binary).
- Response: file shape.

### Delete
- `DELETE /api/v1/files/delete` — 204; deletes MinIO object and DB row.
- Body:
```json
{ "id": 12 }
```

### Download
- `GET /api/v1/files/download?file_id=12` — streams the file with `Content-Disposition: attachment` and `ETag`/`Last-Modified`.
- Body:
```json
{ "rev_status_id": 2, "rev_status_name": "In progress" }
```

# Files (commented)

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

### Insert (multipart)
- `POST /api/v1/files/commented/insert` — 201; multipart form.
- Form fields: `file_id` (int), `user_id` (int), `file` (binary).
- Validates mimetype against the original file; rejects duplicates per `(file_id, user_id)`.

### Delete
- `DELETE /api/v1/files/commented/delete` — 204; deletes MinIO object and DB row.
- Body:
```json
{ "id": 3 }
```

### Download
- `GET /api/v1/files/commented/download?file_id=3` — streams the commented file.
- `Content-Disposition` filename is `<original>_commented_by_<user_acronym>`.
### Delete
- `DELETE /api/v1/lookups/doc_rev_statuses/delete` — 204; 404 if not found.
- Body:
```json
{ "rev_status_id": 2 }
```

# Persons/users/permissions

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
### Insert
- `POST /api/v1/people/roles/insert` — 201; 400 on uniqueness.
- Body:
```json
{ "role_name": "Coordinator" }
```
### Update
- `PUT /api/v1/people/roles/update` — 200; 400 if missing fields/uniqueness; 404 if not found.
- Body:
```json
{ "role_id": 10, "role_name": "Lead Coordinator" }
```
### Delete
- `DELETE /api/v1/people/roles/delete` — 204; 404 if not found.
- Body:
```json
{ "role_id": 10 }
```

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
### Insert
- `POST /api/v1/people/persons/insert` — 201; 400 on insert failure.
- Body:
```json
{ "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" }
```
### Update
- `PUT /api/v1/people/persons/update` — 200; 400 if no fields; 404 if not found.
- Body:
```json
{ "person_id": 12, "person_name": "Grace Hopper", "photo_s3_uid": null }
```
### Delete
- `DELETE /api/v1/people/persons/delete` — 204; 404 if not found.
- Body:
```json
{ "person_id": 12 }
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
### List
- `GET /api/v1/people/users` — 200 sorted by `user_acronym`; 404 if empty.
- Example response:
```json
[ { "user_id": 7, "person_id": 12, "user_acronym": "ALV", "role_id": 3, "person_name": "Ada Lovelace", "role_name": "Coordinator" } ]
```
### Insert
- `POST /api/v1/people/users/insert` — 201; 400 on insert failure; 404 if person/role missing.
- Body:
```json
{ "person_id": 12, "user_acronym": "ALV", "role_id": 3 }
```
### Update
- `PUT /api/v1/people/users/update` — 200; 400 if no fields/update fails; 404 if user/person/role missing.
- Body:
```json
{ "user_id": 7, "person_id": 12, "user_acronym": "ALV2", "role_id": 4 }
```
### Delete
- `DELETE /api/v1/people/users/delete` — 204; 404 if not found.
- Body:
```json
{ "user_id": 7 }
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
At least one of `project_id` or `discipline_id` is required.
### List
- `GET /api/v1/people/permissions` — 200 sorted by `user_id`; 404 if empty.
- Example response:
```json
[ { "permission_id": 42, "user_id": 7, "project_id": 3, "discipline_id": 2, "user_acronym": "ALV", "person_name": "Ada Lovelace", "project_name": "Delta Expansion", "discipline_name": "Piping" } ]
```
### Insert
- `POST /api/v1/people/permissions/insert` — 201; 400 if duplicate or scope missing; 404 if user/project/discipline missing.
- Body (at least one scope):
```json
{ "user_id": 7, "project_id": 3, "discipline_id": 2 }
```
### Update
- `PUT /api/v1/people/permissions/update` — 200; 400 if no new scope/duplicate; 404 if missing references or permission.
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
- `DELETE /api/v1/people/permissions/delete` — 204; 400 if scope missing; 404 if not found.
- Body (permission_id or scope):
```json
{ "permission_id": 42, "user_id": 7, "project_id": 3, "discipline_id": 2 }
```

# Docs

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
### Insert
- `POST /api/v1/documents/doc_types/insert` — 201; 400 on uniqueness; 404 if discipline missing.
- Body:
```json
{ "doc_type_name": "Piping Iso", "ref_discipline_id": 2, "doc_type_acronym": "ISO" }
```
### Update
- `PUT /api/v1/documents/doc_types/update` — 200; 400 if no fields/uniqueness; 404 if doc type or discipline missing.
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
- `DELETE /api/v1/documents/doc_types/delete` — 204; 404 if not found.
- Body:
```json
{ "type_id": 7 }
```

## Documents
Shape (single item) includes doc, linked names, and discipline/progress pointers:
`doc_id`, `doc_name_unique`, `title`, `project_id`/`project_name`, `jobpack_id`/`jobpack_name`, `type_id`/`doc_type_name`/`doc_type_acronym`, `area_id`/`area_name`/`area_acronym`, `unit_id`/`unit_name`, `rev_actual_id`, `rev_current_id`, `rev_seq_num`, `discipline_id`/`discipline_name`/`discipline_acronym`, `rev_code_name`, `rev_code_acronym`, `percentage`.
- `GET /api/v1/documents/list?project_id=` — 200 ordered by `doc_name_unique`; 404 if none for the project. Requires `project_id` query param.
- `PUT /api/v1/documents/update` — updates a document; body includes `doc_id` plus any of: `doc_name_unique`, `title`, `project_id`, `jobpack_id`, `type_id`, `area_id`, `unit_id`, `rev_actual_id`, `rev_current_id`. Requires at least one updatable field. Validates references (project, jobpack, type, area, unit, revisions) and uniqueness of `doc_name_unique`. Returns the updated document.
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

## Error responses
- `400` — Validation failed (missing required fields, duplicate/uniqueness, duplicate permissions, etc.).
- `404` — Resource not found or empty table.
- All errors follow FastAPI's standard shape:
```json
{ "detail": "Reason for failure" }
```
