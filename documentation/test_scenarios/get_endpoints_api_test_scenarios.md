# GET Endpoints API Test Plan (Curl, Port 5556)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-07
- Last Updated: 2026-02-07
- Version: v1.1

## Purpose
Provide repeatable curl-based smoke validation for baseline GET endpoints.

## Scope
- In scope:
  - service health/root checks
  - lookup and people endpoints
  - documents list with resolved project
- Out of scope:
  - POST/PUT/PATCH/DELETE routes

## Design / Behavior
All baseline GET endpoints must return success in seeded environments.

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:5556
export API_PREFIX=/api/v1
```

## 2. TS-GET-001 Run GET Smoke Sweep

```bash
curl -i "$API_BASE/health"
curl -i "$API_BASE/"

for ep in \
  /lookups/areas \
  /lookups/disciplines \
  /lookups/projects \
  /lookups/units \
  /lookups/jobpacks \
  /documents/doc_types \
  /documents/doc_rev_milestones \
  /documents/revision_overview \
  /lookups/doc_rev_status_ui_behaviors \
  /lookups/doc_rev_statuses \
  /people/roles \
  /people/persons \
  /people/users \
  /people/permissions
  do
    echo "=== GET $ep ==="
    curl -i "$API_BASE$API_PREFIX$ep"
  done

PROJECT_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/projects" | jq -r '.[0].project_id')
curl -i "$API_BASE$API_PREFIX/documents?project_id=$PROJECT_ID"
```

## Edge Cases
- If no project exists, `/documents?project_id=...` cannot be validated.
- In empty seeds, some endpoints may return `404`; treat as environment limitation.

## Scenario Catalog
- `TS-GET-001`: baseline GET endpoint set responds with success codes.

## Automated Test Mapping
- `tests/api/api/test_get_endpoints.py::test_all_get_endpoints` -> `TS-GET-001`

## References
- `tests/api/api/test_get_endpoints.py`
- `api/routers/lookups.py`
