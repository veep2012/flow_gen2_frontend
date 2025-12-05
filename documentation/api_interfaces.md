# Flow API Interfaces

Current FastAPI surface (version 0.1.0). All endpoints are JSON, live under the backend root (no global prefix), and are CORS-open for any origin. Default database URL is `postgresql+psycopg://flow_user:flow_pass@postgres:5432/flow_db`; override via `DATABASE_URL`.

## Health and root
- `GET /` — Returns `{"message": "Flow backend is running"}`.
- `GET /health` — Returns `{"status": "ok"}`. Useful for readiness checks.

## Area lookups
All area records share the shape:
```json
{
  "area_id": 1,
  "area_name": "Newfoundland",
  "area_acronym": "NFLD"
}
```

### List areas
- `GET /api/v1/lookups/areas`
- Success: `200` with array of area objects sorted by `area_name`.
- Errors: `404` if the table is empty.
- Example:
```bash
curl -s http://localhost:8000/api/v1/lookups/areas
```

### Insert area
- `POST /api/v1/lookups/areas/insert`
- Body:
```json
{ "area_name": "Newfoundland", "area_acronym": "NFLD" }
```
- Success: `201` with the created area.
- Errors: `400` if `area_name` or `area_acronym` already exists.
- Example:
```bash
curl -X POST http://localhost:8000/api/v1/lookups/areas/insert \
  -H "Content-Type: application/json" \
  -d '{ "area_name": "Newfoundland", "area_acronym": "NFLD" }'
```

### Update area
- `POST /api/v1/lookups/areas/update`
- Body (at least one optional field required):
```json
{ "area_id": 1, "area_name": "Updated Name", "area_acronym": "UPD" }
```
- Success: `200` with the updated area.
- Errors: `400` if no fields provided or uniqueness is violated; `404` if `area_id` is not found.

### Delete area
- `POST /api/v1/lookups/areas/delete`
- Body:
```json
{ "area_id": 1 }
```
- Success: `204` with empty body.
- Errors: `404` if `area_id` is not found.

## Discipline lookups
Discipline objects mirror areas, with `discipline_id`, `discipline_name`, and `discipline_acronym`.

### List disciplines
- `GET /api/v1/lookups/disciplines`
- Success: `200` with array sorted by `discipline_name`.
- Errors: `404` if none exist.

### Insert discipline
- `POST /api/v1/lookups/disciplines/insert`
- Body:
```json
{ "discipline_name": "Structural", "discipline_acronym": "STR" }
```
- Success: `201` with created discipline.
- Errors: `400` on uniqueness conflicts.

### Update discipline
- `POST /api/v1/lookups/disciplines/update`
- Body (at least one optional field required):
```json
{ "discipline_id": 2, "discipline_name": "Piping", "discipline_acronym": "PIP" }
```
- Success: `200` with updated discipline.
- Errors: `400` if no fields or uniqueness conflict; `404` if `discipline_id` not found.

### Delete discipline
- `POST /api/v1/lookups/disciplines/delete`
- Body:
```json
{ "discipline_id": 2 }
```
- Success: `204` with empty body.
- Errors: `404` if `discipline_id` not found.

## Project lookups
Project objects include `project_id` and `project_name`.

### List projects
- `GET /api/v1/lookups/projects`
- Success: `200` sorted by `project_name`.
- Errors: `404` if none exist.

### Insert project
- `POST /api/v1/lookups/projects/insert`
- Body:
```json
{ "project_name": "Delta Expansion" }
```
- Success: `201` with created project.
- Errors: `400` on uniqueness conflicts.

### Update project
- `POST /api/v1/lookups/projects/update`
- Body:
```json
{ "project_id": 3, "project_name": "Updated Project" }
```
- Success: `200` with updated project.
- Errors: `400` if missing fields or uniqueness conflict; `404` if `project_id` not found.

### Delete project
- `POST /api/v1/lookups/projects/delete`
- Body:
```json
{ "project_id": 3 }
```
- Success: `204` with empty body.
- Errors: `404` if `project_id` not found.

## Unit lookups
Unit objects include `unit_id` and `unit_name`.

### List units
- `GET /api/v1/lookups/units`
- Success: `200` sorted by `unit_name`.
- Errors: `404` if none exist.

### Insert unit
- `POST /api/v1/lookups/units/insert`
- Body:
```json
{ "unit_name": "North Wing" }
```
- Success: `201` with created unit.
- Errors: `400` on uniqueness conflicts.

### Update unit
- `POST /api/v1/lookups/units/update`
- Body:
```json
{ "unit_id": 2, "unit_name": "Main Floor" }
```
- Success: `200` with updated unit.
- Errors: `400` if missing fields or uniqueness conflict; `404` if `unit_id` not found.

### Delete unit
- `POST /api/v1/lookups/units/delete`
- Body:
```json
{ "unit_id": 2 }
```
- Success: `204` with empty body.
- Errors: `404` if `unit_id` not found.

## Jobpack lookups
Jobpacks include `jobpack_id` and `jobpack_name`.

### List jobpacks
- `GET /api/v1/lookups/jobpacks`
- Success: `200` sorted by `jobpack_name`.
- Errors: `404` if none exist.

### Insert jobpack
- `POST /api/v1/lookups/jobpacks/insert`
- Body:
```json
{ "jobpack_name": "JP-01" }
```
- Success: `201` with created jobpack.
- Errors: `400` on uniqueness conflicts.

### Update jobpack
- `POST /api/v1/lookups/jobpacks/update`
- Body:
```json
{ "jobpack_id": 5, "jobpack_name": "JP-01B" }
```
- Success: `200` with updated jobpack.
- Errors: `400` if missing fields or uniqueness conflict; `404` if `jobpack_id` not found.

### Delete jobpack
- `POST /api/v1/lookups/jobpacks/delete`
- Body:
```json
{ "jobpack_id": 5 }
```
- Success: `204` with empty body.
- Errors: `404` if `jobpack_id` not found.

## Role lookups
Roles include auto-generated `role_id` and `role_name`.

### List roles
- `GET /api/v1/lookups/roles`
- Success: `200` sorted by `role_name`.
- Errors: `404` if none exist.

### Insert role
- `POST /api/v1/lookups/roles/insert`
- Body:
```json
{ "role_name": "Coordinator" }
```
- Success: `201` with created role.
- Errors: `400` on name conflicts.

### Update role
- `POST /api/v1/lookups/roles/update`
- Body:
```json
{ "role_id": 10, "role_name": "Lead Coordinator" }
```
- Success: `200` with updated role.
- Errors: `400` if missing fields or uniqueness conflict; `404` if `role_id` not found.

### Delete role
- `POST /api/v1/lookups/roles/delete`
- Body:
```json
{ "role_id": 10 }
```
- Success: `204` with empty body.
- Errors: `404` if `role_id` not found.

## Doc revision milestone lookups
Milestones include `milestone_id`, `milestone_name`, and optional integer `progress`.

### List milestones
- `GET /api/v1/lookups/doc_rev_milestones`
- Success: `200` sorted by `milestone_name`.
- Errors: `404` if none exist.

### Insert milestone
- `POST /api/v1/lookups/doc_rev_milestones/insert`
- Body:
```json
{ "milestone_name": "Issued for Construction", "progress": 80 }
```
- `progress` is optional (null if omitted).
- Success: `201` with created milestone.
- Errors: `400` on uniqueness conflicts.

### Update milestone
- `POST /api/v1/lookups/doc_rev_milestones/update`
- Body (at least one optional field required):
```json
{ "milestone_id": 4, "milestone_name": "IFC", "progress": 90 }
```
- Success: `200` with updated milestone.
- Errors: `400` if no fields or uniqueness conflict; `404` if `milestone_id` not found.

### Delete milestone
- `POST /api/v1/lookups/doc_rev_milestones/delete`
- Body:
```json
{ "milestone_id": 4 }
```
- Success: `204` with empty body.
- Errors: `404` if `milestone_id` not found.

## Error responses
- `400` — Validation failed (e.g., missing update fields, unique constraint violations).
- `404` — Resource not found or empty table.
- All errors follow FastAPI's standard shape:
```json
{ "detail": "Reason for failure" }
```
