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

## Error responses
- `400` — Validation failed (e.g., missing update fields, unique constraint violations).
- `404` — Resource not found or empty table.
- All errors follow FastAPI's standard shape:
```json
{ "detail": "Reason for failure" }
```
