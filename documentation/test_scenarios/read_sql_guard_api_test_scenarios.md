# Read SQL Guard API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-03-04
- Last Updated: 2026-03-04
- Version: v0.1

## Change Log
- 2026-03-04 | v0.1 | Initial scenario contract for static API SQL read-path guard.

## Purpose
Define the static repository guard that prevents API read SQL from bypassing `workflow.v_*` views.

## Scope
- In scope:
  - SQL string literals in `api/routers/`
  - SQL string literals in shared API read helpers under `api/utils/`
  - `FROM`/`JOIN` references to `workflow`, `core`, `ref`, and `audit`
- Out of scope:
  - SQL in migrations and seed files
  - Admin/manual scripts outside API runtime modules
  - Mutation-function calls that are explicitly allowlisted

## Design / Behavior
The API must read through `workflow.v_*` views rather than base schemas or non-view `workflow.*` objects. A static test scans API Python modules and fails when a `FROM` or `JOIN` clause targets:
- `core.*`
- `ref.*`
- `audit.*`
- `workflow.*` that does not start with `v_` and is not in the explicit allowlist for write-function result sets

## Scenario Catalog
- `TS-RSG-001` Static guard rejects API read SQL that uses non-`workflow.v_*` relations outside the approved allowlist.

## Scenario Details

### TS-RSG-001 Read SQL Uses Workflow Views Only
- Intent: Prevent regressions where API SQL reads from base tables or non-view workflow relations.
- Setup/Preconditions:
  - Repository contains API Python modules under `api/routers/` and `api/utils/`.
  - Guard test has the approved allowlist for write-function result-set references.
- Request/Action:
  - Run the static guard test against the tracked API Python files.
- Expected:
  - All `FROM`/`JOIN` reads target `workflow.v_*` views, except explicitly allowlisted workflow mutation functions.
  - Any direct read from `core.*`, `ref.*`, `audit.*`, or non-allowlisted `workflow.*` fails the test with file and object details.
- Cleanup:
  - None.

## Automated Test Mapping
- `tests/api/unit/test_read_sql_guard.py::test_api_sql_uses_workflow_views_only` -> `TS-RSG-001`

## References
- `documentation/api_db_rules.md`
- `tests/api/unit/test_read_sql_guard.py`
- `api/routers/`
- `api/utils/helpers.py`
- `api/utils/database.py`
