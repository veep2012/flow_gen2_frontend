# JWT Auth Validation API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: Security and API maintainers
- Created: 2026-03-07
- Last Updated: 2026-03-07
- Version: v0.1

## Change Log
- 2026-03-07 | v0.1 | Added explicit JWT/JWKS fail-closed validation scenarios and automated test mappings for bearer-auth regression coverage.

## Purpose
Define explicit fail-closed validation scenarios for bearer JWT parsing, claim validation, JWKS retrieval, and identity resolution.

## Scope
- In scope:
  - malformed bearer header handling
  - signature, expiry, issuer, and audience validation
  - missing JWT identity claim handling
  - unknown internal user handling after JWT verification
  - JWKS discovery/fetch/client failure handling
- Out of scope:
  - IdP login UX
  - end-to-end browser authentication flows

## Design / Behavior
Bearer-token validation must fail closed and remain observable. Validation failures must not fall back to lower-priority identity sources, and JWKS retrieval/client failures must emit the existing `jwks_fetch_failed` telemetry reason.

## Scenario Catalog
- `TS-JWT-001`: malformed bearer header fails closed.
- `TS-JWT-002`: invalid JWT signature fails validation.
- `TS-JWT-003`: expired JWT fails validation.
- `TS-JWT-004`: wrong issuer fails validation.
- `TS-JWT-005`: wrong audience fails validation.
- `TS-JWT-006`: missing identity claim fails closed after JWT validation.
- `TS-JWT-007`: unknown internal user fails closed after JWT validation.
- `TS-JWT-008`: JWKS discovery or fetch failure fails closed with `jwks_fetch_failed`.
- `TS-JWT-009`: JWKS client parsing/key-resolution failure fails closed with `jwks_fetch_failed`.

## Scenario Details

### TS-JWT-001 Malformed Bearer Header
- Intent: Reject malformed `Authorization` header formats before token verification.
- Setup/Preconditions:
  - Request carries a non-bearer `Authorization` header.
- Request/Action:
  - Resolve effective identity for a request with `Authorization: Token not-a-bearer`.
- Expected:
  - `401 Unauthorized`
  - `flow_auth_jwt_validation_failures_total{reason="malformed_authorization_header"}` increments.
- Cleanup:
  - Reset in-process metrics.

### TS-JWT-002 Invalid JWT Signature
- Intent: Reject tokens that were not signed with the configured key.
- Setup/Preconditions:
  - HS256 verification is configured with a shared secret.
- Request/Action:
  - Decode a token signed with a different secret.
- Expected:
  - Token validation raises `InvalidTokenError`.
- Cleanup:
  - None.

### TS-JWT-003 Expired JWT
- Intent: Reject expired bearer tokens.
- Setup/Preconditions:
  - HS256 verification is configured with a shared secret.
- Request/Action:
  - Decode a token whose `exp` is already in the past.
- Expected:
  - Token validation raises `InvalidTokenError`.
- Cleanup:
  - None.

### TS-JWT-004 Wrong Issuer
- Intent: Reject tokens whose `iss` does not match configured issuer.
- Setup/Preconditions:
  - HS256 verification is configured with a shared secret.
- Request/Action:
  - Decode a token with the wrong `iss`.
- Expected:
  - Token validation raises `InvalidTokenError`.
- Cleanup:
  - None.

### TS-JWT-005 Wrong Audience
- Intent: Reject tokens whose `aud` does not match configured audience.
- Setup/Preconditions:
  - HS256 verification is configured with a shared secret.
- Request/Action:
  - Decode a token with the wrong `aud`.
- Expected:
  - Token validation raises `InvalidTokenError`.
- Cleanup:
  - None.

### TS-JWT-006 Missing Identity Claim
- Intent: Fail closed when a verified token does not provide any configured identity claim.
- Setup/Preconditions:
  - Bearer token decoding succeeds.
  - No configured identity claim yields a non-empty string.
- Request/Action:
  - Resolve effective identity from a decoded payload with no usable identity claim.
- Expected:
  - `401 Unauthorized`
  - `flow_auth_jwt_validation_failures_total{reason="missing_identity_claim"}` increments.
- Cleanup:
  - Reset in-process metrics.

### TS-JWT-007 Unknown Internal User
- Intent: Fail closed when JWT identity claim does not resolve to an internal user.
- Setup/Preconditions:
  - Bearer token decoding succeeds.
  - Claim value does not resolve in `workflow.v_users`.
- Request/Action:
  - Resolve effective identity from a verified token for an unknown acronym.
- Expected:
  - `401 Unauthorized`
  - `flow_auth_jwt_validation_failures_total{reason="unknown_internal_user"}` increments.
- Cleanup:
  - Reset in-process metrics.

### TS-JWT-008 JWKS Discovery or Fetch Failure
- Intent: Fail closed when the API cannot discover or fetch JWKS metadata.
- Setup/Preconditions:
  - JWT verification uses JWKS instead of shared secret.
  - OIDC discovery or JWKS URL resolution fails.
- Request/Action:
  - Resolve effective identity while JWKS discovery raises a fetch error.
- Expected:
  - `401 Unauthorized`
  - `flow_auth_jwt_validation_failures_total{reason="jwks_fetch_failed"}` increments.
- Cleanup:
  - Reset in-process metrics.

### TS-JWT-009 JWKS Client Parsing or Key Resolution Failure
- Intent: Fail closed when JWKS client parsing or signing-key resolution fails after JWKS URL resolution.
- Setup/Preconditions:
  - JWT verification uses JWKS instead of shared secret.
  - JWKS client key-resolution path raises a client/parsing error.
- Request/Action:
  - Resolve effective identity while `get_signing_key_from_jwt(...)` raises a client error.
- Expected:
  - `401 Unauthorized`
  - `flow_auth_jwt_validation_failures_total{reason="jwks_fetch_failed"}` increments.
- Cleanup:
  - Reset in-process metrics.

## Automated Test Mapping
- `tests/api/unit/test_auth_observability.py::test_malformed_authorization_header_increments_metric_and_logs` -> `TS-JWT-001`
- `tests/api/unit/test_jwt_verification.py::test_decode_bearer_token_rejects_invalid_signature` -> `TS-JWT-002`
- `tests/api/unit/test_jwt_verification.py::test_decode_bearer_token_rejects_expired_token` -> `TS-JWT-003`
- `tests/api/unit/test_jwt_verification.py::test_decode_bearer_token_rejects_wrong_issuer` -> `TS-JWT-004`
- `tests/api/unit/test_jwt_verification.py::test_decode_bearer_token_rejects_wrong_audience` -> `TS-JWT-005`
- `tests/api/unit/test_auth_observability.py::test_missing_identity_claim_from_jwt_fails_closed` -> `TS-JWT-006`
- `tests/api/unit/test_auth_observability.py::test_unknown_internal_user_from_jwt_fails_closed` -> `TS-JWT-007`
- `tests/api/unit/test_auth_observability.py::test_jwks_discovery_fetch_failure_fails_closed_and_records_metric` -> `TS-JWT-008`
- `tests/api/unit/test_auth_observability.py::test_jwks_client_failure_fails_closed_and_records_metric` -> `TS-JWT-009`

## Edge Cases
- JWTs can pass signature validation but still fail identity resolution because configured identity claims are missing or empty.
- JWKS fetch failures and JWKS client parsing failures must share the same external failure handling (`jwks_fetch_failed`) even when the underlying exception classes differ.

## References
- `api/utils/database.py`
- `tests/api/unit/test_jwt_verification.py`
- `tests/api/unit/test_auth_observability.py`
