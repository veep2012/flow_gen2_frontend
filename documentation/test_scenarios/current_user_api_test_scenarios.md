# Current User API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-03-04
- Last Updated: 2026-03-04
- Version: v0.1

## Change Log
- 2026-03-04 | v0.1 | Initial scenario contract for `GET /api/v1/people/users/current_user`.

## Purpose
Define the HTTP contract for resolving the current user from session identity.

## Scope
- In scope:
  - current-user read success path
  - missing session identity handling
  - session identity present but current-user row not resolvable
- Out of scope:
  - full people/users CRUD lifecycle
  - upstream IdP integration

## Design / Behavior
`GET /api/v1/people/users/current_user` is driven by DB session identity:
- `401 Unauthorized` when no effective session user exists.
- `404 Not Found` when a session user exists but the current-user read model cannot resolve it.

The `404` contract is intentionally shared across:
- session user hidden or filtered from the current-user read model
- session user disabled/inactive/deprovisioned such that it no longer resolves in the active user read model

## Scenario Catalog
- `TS-CU-001` Valid session user returns `200` with current-user payload.
- `TS-CU-002` Missing session user returns `401`.
- `TS-CU-003` Session user exists but is filtered/hidden from current-user read model returns `404`.
- `TS-CU-004` Session user is inactive/disabled/deprovisioned from current-user read model returns `404`.

## Scenario Details

### TS-CU-001 Valid Current User
- Intent: Confirm happy-path contract for a resolvable session user.
- Setup/Preconditions:
  - Effective session identity resolves to a visible current-user row.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user`.
- Expected:
  - `200 OK`
  - Response matches `UserOut`.
- Cleanup:
  - None.

### TS-CU-002 Missing Session User
- Intent: Confirm fail-closed auth behavior.
- Setup/Preconditions:
  - No effective session identity is present.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user`.
- Expected:
  - `401 Unauthorized`
  - Body: `{ "detail": "Authentication required" }`
- Cleanup:
  - None.

### TS-CU-003 Session User Filtered by RLS/Visibility
- Intent: Stabilize behavior when identity exists but read model hides the user.
- Setup/Preconditions:
  - Effective session identity exists.
  - Current-user read query returns no row because the user is filtered/hidden from the visible read model.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user`.
- Expected:
  - `404 Not Found`
  - Body: `{ "detail": "Current user not found" }`
- Cleanup:
  - None.

### TS-CU-004 Session User Inactive/Disabled
- Intent: Stabilize behavior when the identity refers to a deprovisioned user.
- Setup/Preconditions:
  - Effective session identity exists.
  - User no longer resolves in active current-user read model state.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user`.
- Expected:
  - `404 Not Found`
  - Body: `{ "detail": "Current user not found" }`
- Cleanup:
  - None.

## Automated Test Mapping
- `tests/api/unit/test_current_user_contract.py::test_current_user_returns_valid_user` -> `TS-CU-001`
- `tests/api/unit/test_current_user_contract.py::test_current_user_missing_session_user_returns_401` -> `TS-CU-002`
- `tests/api/unit/test_current_user_contract.py::test_current_user_filtered_by_visibility_returns_404` -> `TS-CU-003`
- `tests/api/unit/test_current_user_contract.py::test_current_user_inactive_user_returns_404` -> `TS-CU-004`

## References
- `api/routers/people.py`
- `api/schemas/people.py`
- `documentation/api_interfaces.md`
- `tests/api/unit/test_current_user_contract.py`
