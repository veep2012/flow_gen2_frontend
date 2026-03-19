# GET Endpoints API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-07
- Last Updated: 2026-03-19
- Version: v1.5

## Change Log
- 2026-03-19 | v1.5 | Added explicit traceability for revision overview lifecycle-path and invalid-update constraint checks.
- 2026-03-18 | v1.4 | Added revision overview lifecycle ordering and invariant checks for the redesigned lifecycle response.
- 2026-03-04 | v1.3 | Added `/metrics` to the baseline GET smoke sweep and documented the observability endpoint contract.
- 2026-02-20 | v1.2 | Added Change Log section for standards compliance

## Purpose
Provide repeatable curl-based smoke validation for baseline GET endpoints.

## Scope
- In scope:
  - service health/root checks
  - system observability endpoint
  - lookup and people endpoints
  - documents list with resolved project
- Out of scope:
  - POST/PUT/PATCH/DELETE routes

## Design / Behavior
All baseline GET endpoints must return success in seeded environments.

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:4175
export API_PREFIX=/api/v1
```

## 2. TS-GET-001 Run GET Smoke Sweep

```bash
curl -i "$API_BASE/health"
curl -i "$API_BASE/"
curl -i "$API_BASE/metrics"

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

## 3. TS-GET-002 Validate revision overview lifecycle order

```bash
curl -s "$API_BASE$API_PREFIX/documents/revision_overview" | jq '
  {
    step_count: length,
    start_count: map(select(.start == true)) | length,
    final_count: map(select(.final == true)) | length,
    first_is_start: (.[0].start == true),
    last_is_final: (.[-1].final == true),
    chain_ok: (
      . as $steps
      | [range(0; ($steps | length) - 1) | $steps[.].next_rev_code_id == $steps[. + 1].rev_code_id]
      | all
    )
  }'
```

## 4. TS-GET-003 Reject invalid revision overview lifecycle updates

- Intent: database constraints must reject invalid lifecycle mutations that would break the ordered revision path.
- Setup/preconditions:
  - a seeded `ref.revision_overview` table exists
  - exactly one `start=true` row exists
  - exactly one `final=true` row exists
  - at least one intermediate lifecycle row exists
- Request/action:
  - attempt to update an intermediate row so `next_rev_code_id = rev_code_id`
  - attempt to mark a second row as `start=true`
  - attempt to make the final row both `final=true` and point to a next step
  - attempt to make the final row non-final while still pointing to a next step
- Expected response/assertions:
  - each invalid update must fail with a database error
  - the transaction must roll back without persisting the invalid state
- Cleanup:
  - no cleanup required because the verification runs inside rolled-back nested transactions

## Edge Cases
- If no project exists, `/documents?project_id=...` cannot be validated.
- In empty seeds, some endpoints may return `404`; treat as environment limitation.
- `/metrics` may return zero-valued or sparse counters before auth-related failures are exercised; the endpoint must still return `200`.
- The lifecycle assertion depends on a configured `start=true` row in `revision_overview`.

## Scenario Catalog
- `TS-GET-001`: baseline GET endpoint set responds with success codes.
- `TS-GET-002`: revision overview returns a single ordered lifecycle from `start=true` to `final=true`.
- `TS-GET-003`: revision overview lifecycle constraints reject invalid state mutations that would break the single ordered path.

## Automated Test Mapping
- `tests/api/api/test_get_endpoints.py::test_all_get_endpoints` -> `TS-GET-001`
- `tests/api/api/test_get_endpoints.py::test_revision_overview_represents_single_lifecycle_path` -> `TS-GET-002`
- `tests/api/api/test_get_endpoints.py::test_revision_overview_constraints_reject_invalid_lifecycle_updates` -> `TS-GET-003`

## References
- `tests/api/api/test_get_endpoints.py`
- `api/routers/lookups.py`
