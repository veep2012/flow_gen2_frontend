# Flow API Interfaces

Current FastAPI surface (version 0.1.0). All endpoints are JSON unless noted, live under the backend root (no global prefix), and are CORS-open for any origin. Default database URL is `postgresql+psycopg://flow_user:flow_pass@postgres:5432/flow_db`; override via `DATABASE_URL`. Object storage defaults to `MINIO_ENDPOINT=minio:9000` and `MINIO_BUCKET=flow-default`; override with `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_SECURE`.

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
- `PATCH` endpoints are not currently provided; consider adding `PATCH` for partial updates if needed.

Delete conventions:
- DELETE endpoints do not accept a request body.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/resource/{id}
```
- Success returns `204 No Content`.
- If the resource does not exist, return `404 Not Found`.
- Idempotent delete (returning `204` when the resource is already deleted) is not currently documented; implement and document if desired.

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
- `201 Created` — Successful create responses (with `Location` header).
- `204 No Content` — Successful delete responses.
- `400 Bad Request` — Domain validation, id mismatch, or duplicate/uniqueness violations.
- `401 Unauthorized` — Authentication required (not currently enforced in this API surface).
- `403 Forbidden` — Authenticated but not authorized (not currently enforced in this API surface).
- `404 Not Found` — Resource does not exist.
- `409 Conflict` — Reserved for future use; not currently returned by these endpoints.
- `422 Unprocessable Entity` — FastAPI/Pydantic request validation errors.
- `500 Internal Server Error` — Unhandled server errors.

OpenAPI/Swagger:
- Swagger UI (FastAPI): `/docs`
- OpenAPI JSON: `/openapi.json`
- OpenAPI YAML: `/openapi.yaml` (if enabled)
- This document is maintained manually; verify against the OpenAPI schema when updating endpoints.

Edge cases:
- Invalid path/query IDs: FastAPI validation returns `422 Unprocessable Entity` for non-integer values; valid-but-missing IDs return `404 Not Found`.
- Malformed JSON bodies: FastAPI returns `422 Unprocessable Entity` with a validation error payload.
- Concurrent modification: optimistic locking is not implemented; `409 Conflict` is reserved and not currently returned.

## Health and root
- `GET /` — Returns `{"message": "Flow backend is running"}`.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/
```
- Example response:
```json
{ "message": "Flow backend is running" }
```
- `GET /health` — Returns `{"status": "ok"}`.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/health
```
- Example response:
```json
{ "status": "ok" }
```

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
Schema references:
- Response: `api/schemas/lookups.py` `AreaOut`
- Create: `api/schemas/lookups.py` `AreaCreate`
- Update: `api/schemas/lookups.py` `AreaUpdate`
- Delete: `api/schemas/lookups.py` `AreaDelete`
### List
- `GET /api/v1/lookups/areas` — 200 sorted by `area_name`; empty list if no areas.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/lookups/areas
```
- Example response:
```json
[]
```
### Create
- `POST /api/v1/lookups/areas` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "area_name": "Newfoundland", "area_acronym": "NFLD" }' \
  http://localhost:4175/api/v1/lookups/areas
```
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
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "area_id": 1, "area_name": "Updated Name", "area_acronym": "UPD" }' \
  http://localhost:4175/api/v1/lookups/areas/1
```
- Body:
```json
{ "area_id": 1, "area_name": "Updated Name", "area_acronym": "UPD" }
```
- Example response:
```json
{ "area_id": 1, "area_name": "Updated Name", "area_acronym": "UPD" }
```
### Delete
- `DELETE /api/v1/lookups/areas/{area_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/lookups/areas/1
```

## Disciplines
Shape (single item):
```json
{ "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" }
```
Schema references:
- Response: `api/schemas/lookups.py` `DisciplineOut`
- Create: `api/schemas/lookups.py` `DisciplineCreate`
- Update: `api/schemas/lookups.py` `DisciplineUpdate`
- Delete: `api/schemas/lookups.py` `DisciplineDelete`
### List
- `GET /api/v1/lookups/disciplines` — 200 sorted by `discipline_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/lookups/disciplines
```
- Example response:
```json
[ { "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" } ]
```
### Create
- `POST /api/v1/lookups/disciplines` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "discipline_name": "Structural", "discipline_acronym": "STR" }' \
  http://localhost:4175/api/v1/lookups/disciplines
```
- Example response:
```json
{ "discipline_name": "Structural", "discipline_acronym": "STR" }
```
- Body:
```json
{ "discipline_name": "Structural", "discipline_acronym": "STR" }
```
### Update
- `PUT /api/v1/lookups/disciplines/{discipline_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" }' \
  http://localhost:4175/api/v1/lookups/disciplines/{discipline_id}
```
- Body:
```json
{ "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" }
```
### Delete
- `DELETE /api/v1/lookups/disciplines/{discipline_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/lookups/disciplines/{discipline_id}
```
- Example response: (empty)

## Projects
Shape (single item):
```json
{ "project_id": 3, "project_name": "Delta Expansion" }
```
Schema references:
- Response: `api/schemas/lookups.py` `ProjectOut`
- Create: `api/schemas/lookups.py` `ProjectCreate`
- Update: `api/schemas/lookups.py` `ProjectUpdate`
- Delete: `api/schemas/lookups.py` `ProjectDelete`
### List
- `GET /api/v1/lookups/projects` — 200 sorted by `project_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/lookups/projects
```
- Example response:
```json
[ { "project_id": 3, "project_name": "Delta Expansion" } ]
```
### Create
- `POST /api/v1/lookups/projects` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "project_name": "Delta Expansion" }' \
  http://localhost:4175/api/v1/lookups/projects
```
- Example response:
```json
{ "project_name": "Delta Expansion" }
```
- Body:
```json
{ "project_name": "Delta Expansion" }
```
### Update
- `PUT /api/v1/lookups/projects/{project_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "project_id": 3, "project_name": "Updated Project" }' \
  http://localhost:4175/api/v1/lookups/projects/{project_id}
```
- Body:
```json
{ "project_id": 3, "project_name": "Updated Project" }
```
### Delete
- `DELETE /api/v1/lookups/projects/{project_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/lookups/projects/{project_id}
```
- Example response: (empty)

## Units
Shape (single item):
```json
{ "unit_id": 2, "unit_name": "North Wing" }
```
Schema references:
- Response: `api/schemas/lookups.py` `UnitOut`
- Create: `api/schemas/lookups.py` `UnitCreate`
- Update: `api/schemas/lookups.py` `UnitUpdate`
- Delete: `api/schemas/lookups.py` `UnitDelete`
### List
- `GET /api/v1/lookups/units` — 200 sorted by `unit_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/lookups/units
```
- Example response:
```json
[ { "unit_id": 2, "unit_name": "North Wing" } ]
```
### Create
- `POST /api/v1/lookups/units` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "unit_name": "North Wing" }' \
  http://localhost:4175/api/v1/lookups/units
```
- Example response:
```json
{ "unit_name": "North Wing" }
```
- Body:
```json
{ "unit_name": "North Wing" }
```
### Update
- `PUT /api/v1/lookups/units/{unit_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "unit_id": 2, "unit_name": "Main Floor" }' \
  http://localhost:4175/api/v1/lookups/units/{unit_id}
```
- Body:
```json
{ "unit_id": 2, "unit_name": "Main Floor" }
```
### Delete
- `DELETE /api/v1/lookups/units/{unit_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/lookups/units/{unit_id}
```
- Example response: (empty)

## Jobpacks
Shape (single item):
```json
{ "jobpack_id": 5, "jobpack_name": "JP-01" }
```
Schema references:
- Response: `api/schemas/lookups.py` `JobpackOut`
- Create: `api/schemas/lookups.py` `JobpackCreate`
- Update: `api/schemas/lookups.py` `JobpackUpdate`
- Delete: `api/schemas/lookups.py` `JobpackDelete`
### List
- `GET /api/v1/lookups/jobpacks` — 200 sorted by `jobpack_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/lookups/jobpacks
```
- Example response:
```json
[ { "jobpack_id": 5, "jobpack_name": "JP-01" } ]
```
### Create
- `POST /api/v1/lookups/jobpacks` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "jobpack_name": "JP-01" }' \
  http://localhost:4175/api/v1/lookups/jobpacks
```
- Example response:
```json
{ "jobpack_name": "JP-01" }
```
- Body:
```json
{ "jobpack_name": "JP-01" }
```
### Update
- `PUT /api/v1/lookups/jobpacks/{jobpack_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "jobpack_id": 5, "jobpack_name": "JP-01B" }' \
  http://localhost:4175/api/v1/lookups/jobpacks/{jobpack_id}
```
- Body:
```json
{ "jobpack_id": 5, "jobpack_name": "JP-01B" }
```
### Delete
- `DELETE /api/v1/lookups/jobpacks/{jobpack_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/lookups/jobpacks/{jobpack_id}
```
- Example response: (empty)

## Doc revision milestones
Shape (single item):
```json
{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }
```
Schema references:
- Response: `api/schemas/documents.py` `DocRevMilestoneOut`
- Create: `api/schemas/documents.py` `DocRevMilestoneCreate`
- Update: `api/schemas/documents.py` `DocRevMilestoneUpdate`
- Delete: `api/schemas/documents.py` `DocRevMilestoneDelete`
### List
- `GET /api/v1/documents/doc_rev_milestones` — 200 sorted by `milestone_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/documents/doc_rev_milestones
```
- Example response:
```json
[ { "milestone_id": 4, "milestone_name": "IFC", "progress": 90 } ]
```
### Create
- `POST /api/v1/documents/doc_rev_milestones` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "milestone_name": "Issued for Construction", "progress": 80 }' \
  http://localhost:4175/api/v1/documents/doc_rev_milestones
```
- Example response:
```json
{ "milestone_name": "Issued for Construction", "progress": 80 }
```
- Body:
```json
{ "milestone_name": "Issued for Construction", "progress": 80 }
```
### Update
- `PUT /api/v1/documents/doc_rev_milestones/{milestone_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }' \
  http://localhost:4175/api/v1/documents/doc_rev_milestones/{milestone_id}
```
- Example response:
```json
{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }
```
- Body:
```json
{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }
```
### Delete
- `DELETE /api/v1/documents/doc_rev_milestones/{milestone_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/documents/doc_rev_milestones/{milestone_id}
```
- Example response: (empty)

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
- Create: `api/schemas/documents.py` `RevisionOverviewCreate`
- Update: `api/schemas/documents.py` `RevisionOverviewUpdate`
- Delete: `api/schemas/documents.py` `RevisionOverviewDelete`
### List
- `GET /api/v1/documents/revision_overview` — 200 sorted by `rev_code_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/documents/revision_overview
```
- Example response:
```json
[ { "rev_code_id": 5, "rev_code_name": "IFC", "rev_code_acronym": "E", "rev_description": "Issued for Construction", "percentage": 90 } ]
```
### Create
- `POST /api/v1/documents/revision_overview` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{
  "rev_code_name": "IFC",
  "rev_code_acronym": "E",
  "rev_description": "Issued for Construction",
  "percentage": 90
}' \
  http://localhost:4175/api/v1/documents/revision_overview
```
- Example response:
```json
{
  "rev_code_name": "IFC",
  "rev_code_acronym": "E",
  "rev_description": "Issued for Construction",
  "percentage": 90
}
```
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
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{
  "rev_code_id": 5,
  "rev_code_name": "AFC",
  "rev_code_acronym": "C",
  "rev_description": "Approved for Construction",
  "percentage": 100
}' \
  http://localhost:4175/api/v1/documents/revision_overview/{rev_code_id}
```
- Example response:
```json
{
  "rev_code_id": 5,
  "rev_code_name": "AFC",
  "rev_code_acronym": "C",
  "rev_description": "Approved for Construction",
  "percentage": 100
}
```
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
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/documents/revision_overview/{rev_code_id}
```
- Example response: (empty)

## Doc revision status UI behaviors
Shape (single item):
```json
{ "ui_behavior_id": 1, "ui_behavior_name": "Default", "ui_behavior_file": "default.json" }
```
Schema references:
- Response: `api/schemas/documents.py` `DocRevStatusUiBehaviorOut`
- Create: `api/schemas/documents.py` `DocRevStatusUiBehaviorCreate`
- Update: `api/schemas/documents.py` `DocRevStatusUiBehaviorUpdate`
- Delete: `api/schemas/documents.py` `DocRevStatusUiBehaviorDelete`
### List
- `GET /api/v1/lookups/doc_rev_status_ui_behaviors` — 200 sorted by `ui_behavior_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/lookups/doc_rev_status_ui_behaviors
```
- Example response:
```json
[ { "ui_behavior_id": 1, "ui_behavior_name": "Default", "ui_behavior_file": "default.json" } ]
```
### Create
- `POST /api/v1/lookups/doc_rev_status_ui_behaviors` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "ui_behavior_name": "Default", "ui_behavior_file": "default.json" }' \
  http://localhost:4175/api/v1/lookups/doc_rev_status_ui_behaviors
```
- Example response:
```json
{ "ui_behavior_name": "Default", "ui_behavior_file": "default.json" }
```
- Body:
```json
{ "ui_behavior_name": "Default", "ui_behavior_file": "default.json" }
```
### Update
- `PUT /api/v1/lookups/doc_rev_status_ui_behaviors/{ui_behavior_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "ui_behavior_id": 1, "ui_behavior_name": "Updated Behavior", "ui_behavior_file": "updated.json" }' \
  http://localhost:4175/api/v1/lookups/doc_rev_status_ui_behaviors/{ui_behavior_id}
```
- Body:
```json
{ "ui_behavior_id": 1, "ui_behavior_name": "Updated Behavior", "ui_behavior_file": "updated.json" }
```
### Delete
- `DELETE /api/v1/lookups/doc_rev_status_ui_behaviors/{ui_behavior_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/lookups/doc_rev_status_ui_behaviors/{ui_behavior_id}
```
- Example response: (empty)

## Doc revision statuses
Shape (single item):
```json
{ "rev_status_id": 2, "rev_status_name": "In review" }
```
Schema references:
- Response: `api/schemas/documents.py` `DocRevStatusOut`
- Create: `api/schemas/documents.py` `DocRevStatusCreate`
- Update: `api/schemas/documents.py` `DocRevStatusUpdate`
- Delete: `api/schemas/documents.py` `DocRevStatusDelete`
### List
- `GET /api/v1/lookups/doc_rev_statuses` — 200 sorted by `rev_status_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/lookups/doc_rev_statuses
```
- Example response:
```json
[ { "rev_status_id": 2, "rev_status_name": "In review" } ]
```
### Create
- `POST /api/v1/lookups/doc_rev_statuses` — 201; 400 on uniqueness or invalid state (final status with next_status, non-final without next_status, final with editable/revertible).
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "rev_status_name": "In review" }' \
  http://localhost:4175/api/v1/lookups/doc_rev_statuses
```
- Example response:
```json
{ "rev_status_name": "In review" }
```
- Body:
```json
{ "rev_status_name": "In review" }
```
### Update
- `PUT /api/v1/lookups/doc_rev_statuses/{rev_status_id}` — 200; 400 if no fields/uniqueness/ID mismatch/invalid state; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "rev_status_id": 2, "rev_status_name": "In progress" }' \
  http://localhost:4175/api/v1/lookups/doc_rev_statuses/{rev_status_id}
```
- Example response:
```json
{ "rev_status_id": 2, "rev_status_name": "In progress" }
```
- Body:
```json
{ "rev_status_id": 2, "rev_status_name": "In progress" }
```
### Delete
- `DELETE /api/v1/lookups/doc_rev_statuses/{rev_status_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/lookups/doc_rev_statuses/{rev_status_id}
```
- Example response: (empty)

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
Schema references:
- Create: `api/schemas/files.py` `FileCreate`
- Update: `api/schemas/files.py` `FileUpdate`
- Response: `api/schemas/files.py` `FileCommentedOut`
- Delete: `api/schemas/files.py` `FileCommentedDelete`

### List
- `GET /api/v1/files?rev_id=45` — 200 sorted by `filename`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/files?rev_id=45
```
- Example response:
```json
[
  {
    "id": 12,
    "filename": "report.pdf",
    "s3_uid": "Project/Doc/IFC/uuid_report.pdf",
    "mimetype": "application/pdf",
    "rev_id": 45
  }
]
```

### Create (multipart)
- `POST /api/v1/files` — 201; multipart form.
- Headers: `Accept: application/json`, `Content-Type: multipart/form-data`
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  -F "rev_id=45" \
  -F "file=@report.pdf;type=application/pdf" \
  http://localhost:4175/api/v1/files
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
  "rev_id": 45
}
```

### Update
- `PUT /api/v1/files/{id}` — 200; updates filename; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "id": 12, "filename": "new_report.pdf" }' \
  http://localhost:4175/api/v1/files/{id}
```
- Example response:
```json
{ "id": 12, "filename": "new_report.pdf" }
```
- Body:
```json
{ "id": 12, "filename": "new_report.pdf" }
```

### Delete
- `DELETE /api/v1/files/{id}` — 204; deletes MinIO object and DB row; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/files/{id}
```
- Example response: (empty)

### Download
- `GET /api/v1/files/{file_id}/download` — streams the file with `Content-Disposition: attachment` and `ETag`/`Last-Modified`.
- Headers: `Accept: application/octet-stream`
- Example request:
```bash
curl -sS -H "Accept: application/octet-stream" \
  -o report.pdf \
  http://localhost:4175/api/v1/files/{file_id}/download
```
- Example response (binary):
```
<binary>
```

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
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/files/commented/list?file_id=12
```
- Example response:
```json
[]
```

### Create (multipart)
- `POST /api/v1/files/commented` — 201; multipart form.
- Headers: `Accept: application/json`, `Content-Type: multipart/form-data`
- Example request:
```bash
curl -sS -H "Accept: application/json" \
  -F "file_id=12" \
  -F "user_id=1" \
  -F "file=@commented.pdf;type=application/pdf" \
  http://localhost:4175/api/v1/files/commented
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
  "rev_id": 45
}
```

### Delete
- `DELETE /api/v1/files/commented/{id}` — 204; deletes MinIO object and DB row; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/files/commented/{id}
```
- Example response: (empty)

### Download
- `GET /api/v1/files/commented/download?file_id=3` — streams the commented file.
- Headers: `Accept: application/octet-stream`
- Example request:
```bash
curl -sS -H "Accept: application/octet-stream" \
  -o commented.pdf \
  http://localhost:4175/api/v1/files/commented/download?file_id=3
```
- Example response (binary):
```
<binary>
```
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
Schema references:
- Response: `api/schemas/lookups.py` `RoleOut`
- Create: `api/schemas/lookups.py` `RoleCreate`
- Update: `api/schemas/lookups.py` `RoleUpdate`
- Delete: `api/schemas/lookups.py` `RoleDelete`
### List
- `GET /api/v1/people/roles` — 200 sorted by `role_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/people/roles
```
- Example response:
```json
[ { "role_id": 10, "role_name": "Coordinator" } ]
```
### Create
- `POST /api/v1/people/roles` — 201; 400 on uniqueness.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "role_name": "Coordinator" }' \
  http://localhost:4175/api/v1/people/roles
```
- Example response:
```json
{ "role_name": "Coordinator" }
```
- Body:
```json
{ "role_name": "Coordinator" }
```
### Update
- `PUT /api/v1/people/roles/{role_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "role_id": 10, "role_name": "Lead Coordinator" }' \
  http://localhost:4175/api/v1/people/roles/{role_id}
```
- Body:
```json
{ "role_id": 10, "role_name": "Lead Coordinator" }
```
### Delete
- `DELETE /api/v1/people/roles/{role_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/people/roles/{role_id}
```
- Example response: (empty)

## People
Shape (single item):
```json
{ "person_id": 12, "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" }
```
Schema references:
- Response: `api/schemas/people.py` `PersonOut`
- Create: `api/schemas/people.py` `PersonCreate`
- Update: `api/schemas/people.py` `PersonUpdate`
- Delete: `api/schemas/people.py` `PersonDelete`
### List
- `GET /api/v1/people/persons` — 200 sorted by `person_name`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/people/persons
```
- Example response:
```json
[ { "person_id": 12, "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" } ]
```
### Create
- `POST /api/v1/people/persons` — 201; 400 on insert failure.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" }' \
  http://localhost:4175/api/v1/people/persons
```
- Example response:
```json
{ "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" }
```
- Body:
```json
{ "person_name": "Ada Lovelace", "photo_s3_uid": "s3-key-123" }
```
### Update
- `PUT /api/v1/people/persons/{person_id}` — 200; 400 if no fields/ID mismatch; 404 if not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "person_id": 12, "person_name": "Grace Hopper", "photo_s3_uid": null }' \
  http://localhost:4175/api/v1/people/persons/{person_id}
```
- Example response:
```json
{ "person_id": 12, "person_name": "Grace Hopper", "photo_s3_uid": null }
```
- Body:
```json
{ "person_id": 12, "person_name": "Grace Hopper", "photo_s3_uid": null }
```
### Delete
- `DELETE /api/v1/people/persons/{person_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/people/persons/{person_id}
```
- Example response: (empty)

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
- Create: `api/schemas/people.py` `UserCreate`
- Update: `api/schemas/people.py` `UserUpdate`
- Delete: `api/schemas/people.py` `UserDelete`
### List
- `GET /api/v1/people/users` — 200 sorted by `user_acronym`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/people/users
```
- Example response:
```json
[ { "user_id": 7, "person_id": 12, "user_acronym": "ALV", "role_id": 3, "person_name": "Ada Lovelace", "role_name": "Coordinator" } ]
```
### Create
- `POST /api/v1/people/users` — 201; 400 on insert failure; 404 if person/role missing.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "person_id": 12, "user_acronym": "ALV", "role_id": 3 }' \
  http://localhost:4175/api/v1/people/users
```
- Example response:
```json
{ "person_id": 12, "user_acronym": "ALV", "role_id": 3 }
```
- Body:
```json
{ "person_id": 12, "user_acronym": "ALV", "role_id": 3 }
```
### Update
- `PUT /api/v1/people/users/{user_id}` — 200; 400 if no fields/update fails/ID mismatch; 404 if user/person/role missing.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "user_id": 7, "person_id": 12, "user_acronym": "ALV2", "role_id": 4 }' \
  http://localhost:4175/api/v1/people/users/{user_id}
```
- Example response:
```json
{ "user_id": 7, "person_id": 12, "user_acronym": "ALV2", "role_id": 4 }
```
- Body:
```json
{ "user_id": 7, "person_id": 12, "user_acronym": "ALV2", "role_id": 4 }
```
### Delete
- `DELETE /api/v1/people/users/{user_id}` — 204; 404 if not found.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/people/users/{user_id}
```
- Example response: (empty)

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
- Create: `api/schemas/people.py` `PermissionCreate`
- Update: `api/schemas/people.py` `PermissionUpdate`
- Delete: `api/schemas/people.py` `PermissionDelete`
At least one of `project_id` or `discipline_id` is required.
### List
- `GET /api/v1/people/permissions` — 200 sorted by `user_id`; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/people/permissions
```
- Example response:
```json
[ { "permission_id": 42, "user_id": 7, "project_id": 3, "discipline_id": 2, "user_acronym": "ALV", "person_name": "Ada Lovelace", "project_name": "Delta Expansion", "discipline_name": "Piping" } ]
```
### Create
- `POST /api/v1/people/permissions` — 201; 400 if duplicate or scope missing; 404 if user/project/discipline missing.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "user_id": 7, "project_id": 3, "discipline_id": 2 }' \
  http://localhost:4175/api/v1/people/permissions
```
- Example response:
```json
{ "user_id": 7, "project_id": 3, "discipline_id": 2 }
```
- Body (at least one scope):
```json
{ "user_id": 7, "project_id": 3, "discipline_id": 2 }
```
### Update
- `PUT /api/v1/people/permissions/{permission_id}` — 200; 400 if no new scope/duplicate/ID mismatch; 404 if missing references or permission.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{
  "permission_id": 42,
  "user_id": 7,
  "project_id": 3,
  "discipline_id": 2,
  "new_project_id": 4,
  "new_discipline_id": null
}' \
  http://localhost:4175/api/v1/people/permissions/{permission_id}
```
- Example response:
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
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/people/permissions/{permission_id}
```
- Example response: (empty)
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
Schema references:
- Response: `api/schemas/documents.py` `DocTypeOut`
- Create: `api/schemas/documents.py` `DocTypeCreate`
- Update: `api/schemas/documents.py` `DocTypeUpdate`
- Delete: `api/schemas/documents.py` `DocTypeDelete`
### List
- `GET /api/v1/documents/doc_types` — 200 sorted by `doc_type_name`; includes discipline info; empty list if none.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/documents/doc_types
```
- Example response:
```json
[ { "type_id": 7, "doc_type_name": "Piping Iso", "ref_discipline_id": 2, "doc_type_acronym": "ISO", "discipline_name": "Piping", "discipline_acronym": "PIP" } ]
```
### Create
- `POST /api/v1/documents/doc_types` — 201; 400 on uniqueness; 404 if discipline missing.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "doc_type_name": "Piping Iso", "ref_discipline_id": 2, "doc_type_acronym": "ISO" }' \
  http://localhost:4175/api/v1/documents/doc_types
```
- Example response:
```json
{ "doc_type_name": "Piping Iso", "ref_discipline_id": 2, "doc_type_acronym": "ISO" }
```
- Body:
```json
{ "doc_type_name": "Piping Iso", "ref_discipline_id": 2, "doc_type_acronym": "ISO" }
```
### Update
- `PUT /api/v1/documents/doc_types/{type_id}` — 200; 400 if no fields/uniqueness/ID mismatch; 404 if doc type or discipline missing.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{
  "type_id": 7,
  "doc_type_name": "Piping Iso Updated",
  "ref_discipline_id": 3,
  "doc_type_acronym": "ISO-U"
}' \
  http://localhost:4175/api/v1/documents/doc_types/{type_id}
```
- Example response:
```json
{
  "type_id": 7,
  "doc_type_name": "Piping Iso Updated",
  "ref_discipline_id": 3,
  "doc_type_acronym": "ISO-U"
}
```
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
- Headers: `Accept: application/json`
- Example request:
```bash
curl -i -H "Accept: application/json" -X DELETE http://localhost:4175/api/v1/documents/doc_types/{type_id}
```
- Example response: (empty)

## Documents
Shape (single item) includes doc, linked names, and discipline/progress pointers:
`doc_id`, `doc_name_unique`, `title`, `project_id`/`project_name`, `jobpack_id`/`jobpack_name`, `type_id`/`doc_type_name`/`doc_type_acronym`, `area_id`/`area_name`/`area_acronym`, `unit_id`/`unit_name`, `rev_actual_id`, `rev_current_id`, `rev_seq_num`, `discipline_id`/`discipline_name`/`discipline_acronym`, `rev_code_name`, `rev_code_acronym`, `percentage`.
Schema references:
- Response: `api/schemas/documents.py` `DocOut`
- Create: `api/schemas/documents.py` `DocCreate`
- Update: `api/schemas/documents.py` `DocUpdate`
### List
- `GET /api/v1/documents?project_id=` — 200 ordered by `doc_name_unique`; empty list if none for the project. Excludes voided documents by default. Requires `project_id` query param.
- Optional query param: `show_voided=true` to include voided documents in the response.
- Headers: `Accept: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/documents?project_id=
```
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
  http://localhost:4175/api/v1/documents
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
curl -sS -H "Accept: application/json" http://localhost:4175/api/v1/documents/11/revisions
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
    "rev_date": "2024-01-01T12:00:00Z",
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
    "voided": false,
    "modified_doc_date": "2024-01-05T12:00:00Z"
  }
]
```
### Revision create
- `POST /api/v1/documents/{doc_id}/revisions` — 201; 404 if document or references not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "rev_code_id": 6, "rev_date": "2024-01-01T12:00:00Z", "rev_author_id": 1, "rev_originator_id": 1, "rev_modifier_id": 1, "transmital_current_revision": "TR-NEW-001", "milestone_id": 1, "planned_start_date": "2024-01-02T12:00:00Z", "planned_finish_date": "2024-01-05T12:00:00Z", "actual_start_date": null, "actual_finish_date": null, "canceled_date": null, "rev_status_id": 1, "as_built": false, "superseded": false, "voided": false, "modified_doc_date": "2024-01-05T12:00:00Z" }' \
  http://localhost:4175/api/v1/documents/11/revisions
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
  "rev_date": "2024-01-01T12:00:00Z",
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
  "voided": false,
  "modified_doc_date": "2024-01-05T12:00:00Z"
}
```
### Revision update
- `PUT /api/v1/documents/revisions/{rev_id}` — 200; 400 if no fields/ID mismatch; 404 if revision not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "rev_id": 1, "transmital_current_revision": "TR-UPDATED-001" }' \
  http://localhost:4175/api/v1/documents/revisions/1
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
  "rev_date": "2024-01-01T12:00:00Z",
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
  "voided": false,
  "modified_doc_date": "2024-01-05T12:00:00Z"
}
```
### Update
- `PUT /api/v1/documents/{doc_id}` — 200; updates a document; 400 if no fields/uniqueness/ID mismatch; 404 if doc or references not found.
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Example request:
```bash
curl -sS -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{ "detail": "Reason for failure" }' \
  http://localhost:4175/api/v1/documents/{doc_id}
```
- Example response:
```json
{ "detail": "Reason for failure" }
```
- Body includes `doc_id` plus any of: `doc_name_unique`, `title`, `project_id`, `jobpack_id`, `type_id`, `area_id`, `unit_id`, `rev_actual_id`, `rev_current_id`. 
- Requires at least one updatable field. Validates references (project, jobpack, type, area, unit, revisions) and uniqueness of `doc_name_unique`. Returns the updated document.

## Error responses
- `400` — Validation failed (missing required fields, duplicate/uniqueness, duplicate permissions, etc.).
- `404` — Resource not found or empty table.
- All errors follow FastAPI's standard shape:
```json
{ "detail": "Reason for failure" }
```
