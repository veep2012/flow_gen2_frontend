# Endpoint Contract API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-03-04
- Last Updated: 2026-03-04
- Version: v0.1

## Change Log
- 2026-03-04 | v0.1 | Initial contract/snapshot scenarios for critical list and detail endpoints.

## Purpose
Define runtime contract checks that compare live API payloads with the response-model field sets for critical list and detail endpoints.

## Scope
- In scope:
  - critical list endpoint payload keys
  - current-user detail payload keys
  - seeded-environment contract checks against response models
- Out of scope:
  - value-level business assertions already covered by endpoint-specific tests
  - binary download responses

## Design / Behavior
The contract gate uses seeded smoke requests and compares live JSON object keys to the expected Pydantic response-model field sets. This acts as a lightweight snapshot guard for response shape drift.

## Scenario Catalog
- `TS-CTR-001`: critical list endpoints return item shapes matching response models.
- `TS-CTR-002`: current-user detail returns a shape matching the `UserOut` response model.

## Scenario Details

### TS-CTR-001 Critical List Contracts
- Intent: Detect accidental shape drift on critical list payloads.
- Setup/Preconditions:
  - Seeded API test stack is running.
  - A readable project/document/revision lineage exists.
- Request/Action:
  - Call representative list endpoints:
    - `GET /api/v1/documents?project_id=...`
    - `GET /api/v1/documents/{doc_id}/revisions`
    - `GET /api/v1/files?rev_id=...`
    - `GET /api/v1/notifications?recipient_user_id=...`
    - `GET /api/v1/distribution-lists`
- Expected:
  - Each response returns `200`.
  - Each non-empty list item has exactly the same keys as its declared response model.
- Cleanup:
  - None.

### TS-CTR-002 Current User Detail Contract
- Intent: Detect accidental shape drift on the current-user detail payload.
- Setup/Preconditions:
  - Seeded API test stack is running with a resolvable default user.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user`.
- Expected:
  - Response returns `200`.
  - Response object has exactly the same keys as `UserOut`.
- Cleanup:
  - None.

## Automated Test Mapping
- `tests/api/api/test_endpoint_contracts.py::test_critical_list_endpoints_match_response_models` -> `TS-CTR-001`
- `tests/api/api/test_endpoint_contracts.py::test_current_user_detail_matches_response_model` -> `TS-CTR-002`

## References
- `tests/api/api/test_endpoint_contracts.py`
- `api/schemas/documents.py`
- `api/schemas/files.py`
- `api/schemas/notifications.py`
- `api/schemas/distribution_lists.py`
- `api/schemas/people.py`
