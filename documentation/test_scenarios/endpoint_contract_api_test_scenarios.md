# Endpoint Contract API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-03-04
- Last Updated: 2026-03-06
- Version: v0.2

## Change Log
- 2026-03-06 | v0.2 | Added current-user trusted-header precedence and fail-closed trusted-header scenarios for end-to-end auth contract coverage.
- 2026-03-04 | v0.1 | Initial contract/snapshot scenarios for critical list and detail endpoints.

## Purpose
Define runtime contract checks that compare live API payloads with the response-model field sets for critical list and detail endpoints.

## Scope
- In scope:
  - critical list endpoint payload keys
  - current-user detail payload keys
  - trusted-header precedence for current-user resolution
  - seeded-environment contract checks against response models
- Out of scope:
  - value-level business assertions already covered by endpoint-specific tests
  - binary download responses

## Design / Behavior
The contract gate uses seeded smoke requests and compares live JSON object keys to the expected Pydantic response-model field sets. This acts as a lightweight snapshot guard for response shape drift.

## Scenario Catalog
- `TS-CTR-001`: critical list endpoints return item shapes matching response models.
- `TS-CTR-002`: current-user detail returns a shape matching the `UserOut` response model.
- `TS-CTR-003`: current-user resolution prefers trusted identity header over `X-User-Id` when both are present.
- `TS-CTR-004`: invalid trusted identity header fails closed even when `X-User-Id` is otherwise valid.

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

### TS-CTR-003 Trusted Header Precedence
- Intent: Prove that trusted identity resolution is authoritative when both headers are present.
- Setup/Preconditions:
  - Seeded API test stack is running.
  - At least two resolvable users with distinct `user_acronym` values exist.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user` with both:
    - `X-Auth-User: <trusted user acronym>`
    - `X-User-Id: <different less-trusted user acronym>`
- Expected:
  - Response returns `200`.
  - Response object has exactly the same keys as `UserOut`.
  - Returned user matches `X-Auth-User`, not `X-User-Id`.
- Cleanup:
  - None.

### TS-CTR-004 Invalid Trusted Header Fails Closed
- Intent: Prove that the trusted identity path fails closed instead of falling back to less-trusted header input.
- Setup/Preconditions:
  - Seeded API test stack is running.
  - A resolvable user acronym exists for `X-User-Id`.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user` with both:
    - `X-Auth-User: NOTREAL`
    - `X-User-Id: <valid user acronym>`
- Expected:
  - Response returns `401`.
  - Body is `{ "detail": "Authentication required" }`.
- Cleanup:
  - None.

## Automated Test Mapping
- `tests/api/api/test_endpoint_contracts.py::test_critical_list_endpoints_match_response_models` -> `TS-CTR-001`
- `tests/api/api/test_endpoint_contracts.py::test_current_user_detail_matches_response_model` -> `TS-CTR-002`
- `tests/api/api/test_endpoint_contracts.py::test_current_user_trusted_header_takes_precedence_over_x_user_id` -> `TS-CTR-003`
- `tests/api/api/test_endpoint_contracts.py::test_current_user_invalid_trusted_header_fails_closed_even_with_valid_x_user_id` -> `TS-CTR-004`

## References
- `tests/api/api/test_endpoint_contracts.py`
- `api/schemas/documents.py`
- `api/schemas/files.py`
- `api/schemas/notifications.py`
- `api/schemas/distribution_lists.py`
- `api/schemas/people.py`
