# Auth Router Matrix API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: Security and API maintainers
- Created: 2026-03-04
- Last Updated: 2026-03-04
- Version: v0.1

## Change Log
- 2026-03-04 | v0.1 | Initial router-level auth regression matrix for missing effective session identity across changed routers.

## Purpose
Define the fail-closed router matrix for auth-sensitive endpoints changed by the recent identity hardening work.

## Scope
- In scope:
  - representative auth-sensitive endpoint per changed router
  - missing effective identity regression checks
- Out of scope:
  - endpoint-specific business-rule validation
  - authenticated authorization success paths

## Design / Behavior
Each changed auth-sensitive router must have at least one representative endpoint that hard-fails with `401 Authentication required` when no effective session identity exists.

## Scenario Catalog
- `TS-ARM-001`: documents router denies missing identity.
- `TS-ARM-002`: files router denies missing identity.
- `TS-ARM-003`: files commented router denies missing identity.
- `TS-ARM-004`: written comments router denies missing identity.
- `TS-ARM-005`: notifications router denies missing identity.
- `TS-ARM-006`: distribution lists router denies missing identity.
- `TS-ARM-007`: current-user endpoint denies missing identity.

## Scenario Details

### TS-ARM-001 Documents Router Fail-Closed
- Intent: Guard representative documents reads from anonymous execution.
- Setup/Preconditions:
  - Override DB dependency so effective identity resolves to `NULL`.
- Request/Action:
  - Call `GET /api/v1/documents/1/revisions`.
- Expected:
  - Response status is `401`.
  - Response body is `{"detail": "Authentication required"}`.
- Cleanup:
  - Clear dependency overrides.

### TS-ARM-002 Files Router Fail-Closed
- Intent: Guard representative files reads from anonymous execution.
- Setup/Preconditions:
  - Override DB dependency so effective identity resolves to `NULL`.
- Request/Action:
  - Call `GET /api/v1/files?rev_id=1`.
- Expected:
  - Response status is `401`.
  - Response body is `{"detail": "Authentication required"}`.
- Cleanup:
  - Clear dependency overrides.

### TS-ARM-003 Files Commented Router Fail-Closed
- Intent: Guard representative commented-file reads from anonymous execution.
- Setup/Preconditions:
  - Override DB dependency so effective identity resolves to `NULL`.
- Request/Action:
  - Call `GET /api/v1/files/commented/list?file_id=1`.
- Expected:
  - Response status is `401`.
  - Response body is `{"detail": "Authentication required"}`.
- Cleanup:
  - Clear dependency overrides.

### TS-ARM-004 Written Comments Router Fail-Closed
- Intent: Guard written comments reads from anonymous execution.
- Setup/Preconditions:
  - Override DB dependency so effective identity resolves to `NULL`.
- Request/Action:
  - Call `GET /api/v1/documents/revisions/1/comments`.
- Expected:
  - Response status is `401`.
  - Response body is `{"detail": "Authentication required"}`.
- Cleanup:
  - Clear dependency overrides.

### TS-ARM-005 Notifications Router Fail-Closed
- Intent: Guard notifications reads from anonymous execution.
- Setup/Preconditions:
  - Override DB dependency so effective identity resolves to `NULL`.
- Request/Action:
  - Call `GET /api/v1/notifications`.
- Expected:
  - Response status is `401`.
  - Response body is `{"detail": "Authentication required"}`.
- Cleanup:
  - Clear dependency overrides.

### TS-ARM-006 Distribution Lists Router Fail-Closed
- Intent: Guard distribution list reads from anonymous execution.
- Setup/Preconditions:
  - Override DB dependency so effective identity resolves to `NULL`.
- Request/Action:
  - Call `GET /api/v1/distribution-lists`.
- Expected:
  - Response status is `401`.
  - Response body is `{"detail": "Authentication required"}`.
- Cleanup:
  - Clear dependency overrides.

### TS-ARM-007 Current User Fail-Closed
- Intent: Guard the current-user endpoint from anonymous execution.
- Setup/Preconditions:
  - Override DB dependency so effective identity resolves to `NULL`.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user`.
- Expected:
  - Response status is `401`.
  - Response body is `{"detail": "Authentication required"}`.
- Cleanup:
  - Clear dependency overrides.

## Automated Test Mapping
- `tests/api/unit/test_auth_router_matrix.py::test_documents_router_requires_identity` -> `TS-ARM-001`
- `tests/api/unit/test_auth_router_matrix.py::test_files_router_requires_identity` -> `TS-ARM-002`
- `tests/api/unit/test_auth_router_matrix.py::test_files_commented_router_requires_identity` -> `TS-ARM-003`
- `tests/api/unit/test_auth_router_matrix.py::test_written_comments_router_requires_identity` -> `TS-ARM-004`
- `tests/api/unit/test_auth_router_matrix.py::test_notifications_router_requires_identity` -> `TS-ARM-005`
- `tests/api/unit/test_auth_router_matrix.py::test_distribution_lists_router_requires_identity` -> `TS-ARM-006`
- `tests/api/unit/test_auth_router_matrix.py::test_current_user_endpoint_requires_identity` -> `TS-ARM-007`

## References
- `api/routers/documents.py`
- `api/routers/files.py`
- `api/routers/files_commented.py`
- `api/routers/written_comments.py`
- `api/routers/notifications.py`
- `api/routers/distribution_lists.py`
- `api/routers/people.py`
