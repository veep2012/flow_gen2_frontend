# Auth Precedence Matrix API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: Security and API maintainers
- Created: 2026-03-27
- Last Updated: 2026-03-27
- Version: v0.1

## Change Log
- 2026-03-27 | v0.1 | Added explicit auth precedence matrix scenarios for JWT, trusted headers, local header fallback, anonymous partial identities, and rejection observability.

## Purpose
Define a compact precedence matrix for effective identity resolution so auth-source ordering, fail-closed behavior, and rejection telemetry remain stable across JWT, trusted-header, and local fallback paths.

## Scope
- In scope:
  - precedence between bearer JWT and trusted header identity
  - trusted header success when no bearer token is present
  - malformed bearer header fail-closed behavior
  - production rejection of `APP_USER` bootstrap mode
  - partial/blank header handling for trusted header and `X-User-Id`
  - rejection logging and metrics for denied trusted-header auth
- Out of scope:
  - IdP login flows
  - browser cookie/session authentication

## Design / Behavior
Identity resolution order is: verified bearer JWT, then trusted identity header, then `X-User-Id` in local/dev/test/ci environments, then `APP_USER` bootstrap in those same non-production environments. Higher-trust failures must not fall back to lower-trust inputs, and rejected auth attempts must remain observable in metrics/logging.

## Scenario Catalog
- `TS-APM-001`: valid bearer JWT takes precedence over disagreeing trusted-header and `X-User-Id` inputs.
- `TS-APM-002`: trusted header resolves identity when JWT is absent.
- `TS-APM-003`: malformed bearer header fails closed instead of falling back to trusted-header identity.
- `TS-APM-004`: local/dev `APP_USER` bootstrap mode is rejected in production-like configuration.
- `TS-APM-005`: blank trusted header is ignored so local `X-User-Id` can still resolve in non-production.
- `TS-APM-006`: blank `X-User-Id` is treated as anonymous/missing identity rather than a parse failure.
- `TS-APM-007`: rejected trusted-header identity emits parse-failure telemetry and security logs.

## Scenario Details

### TS-APM-001 JWT Beats Disagreeing Headers
- Intent: Prove that verified JWT identity wins over lower-trust identity sources even when all disagree.
- Setup/Preconditions:
  - Request carries a valid bearer token.
  - Request also carries conflicting `X-Auth-User` and `X-User-Id` values.
- Request/Action:
  - Resolve effective identity from the request.
- Expected:
  - Effective identity uses the JWT claim only.
  - No fallback resolution is attempted for trusted header or `X-User-Id`.
- Cleanup:
  - None.

### TS-APM-002 Trusted Header Without JWT
- Intent: Confirm that the trusted identity header remains the next precedence tier when JWT is absent.
- Setup/Preconditions:
  - No `Authorization` header is present.
  - `X-Auth-User` resolves to an internal user.
- Request/Action:
  - Resolve effective identity from the request.
- Expected:
  - Trusted header becomes the effective identity source.
  - Request auth mode is `trusted_identity_header`.
- Cleanup:
  - None.

### TS-APM-003 Malformed Bearer Header Fails Closed
- Intent: Prevent malformed JWT input from silently falling back to a lower-trust header.
- Setup/Preconditions:
  - Request carries malformed `Authorization` header content.
  - A resolvable trusted-header value is also present.
- Request/Action:
  - Resolve effective identity from the request.
- Expected:
  - `401 Unauthorized`
  - `flow_auth_jwt_validation_failures_total{reason="malformed_authorization_header"}` increments.
- Cleanup:
  - Reset in-process metrics.

### TS-APM-004 Production Rejects APP_USER Bootstrap
- Intent: Enforce that local/dev fallback identity cannot be enabled in production-like deployments.
- Setup/Preconditions:
  - `APP_ENV=production`
  - `APP_USER` is configured.
- Request/Action:
  - Validate startup auth mode.
- Expected:
  - Startup validation raises a runtime error and service boot should fail.
- Cleanup:
  - Clear env overrides.

### TS-APM-005 Blank Trusted Header Falls Through
- Intent: Treat blank trusted-header values as absent rather than as authoritative-but-invalid identity.
- Setup/Preconditions:
  - Non-production environment where `X-User-Id` is enabled.
  - Request carries whitespace-only `X-Auth-User` and a resolvable `X-User-Id`.
- Request/Action:
  - Resolve effective identity from the request.
- Expected:
  - `X-User-Id` path is used.
  - Request auth mode is `x_user_id_header`.
- Cleanup:
  - Clear env overrides.

### TS-APM-006 Blank X-User-Id Stays Anonymous
- Intent: Treat empty `X-User-Id` values as missing identity rather than as malformed identity headers.
- Setup/Preconditions:
  - Non-production environment where `X-User-Id` is enabled.
  - Request carries whitespace-only `X-User-Id`.
- Request/Action:
  - Resolve effective identity from the request.
- Expected:
  - Request remains anonymous with auth mode `missing_identity`.
  - No identity-header parse-failure metric is emitted.
- Cleanup:
  - Reset in-process metrics.

### TS-APM-007 Trusted Header Rejection Is Observable
- Intent: Keep fail-closed trusted-header rejections visible to operators.
- Setup/Preconditions:
  - Request carries an unresolvable `X-Auth-User`.
- Request/Action:
  - Resolve effective identity from the request.
- Expected:
  - `401 Unauthorized`
  - `flow_auth_identity_header_parse_failures_total{auth_mode="trusted_identity_header"}` increments.
  - Security log includes `event=identity_header_parse_failure`.
- Cleanup:
  - Reset in-process metrics.

## Automated Test Mapping
- `tests/api/unit/test_auth_precedence_matrix.py::test_jwt_identity_takes_precedence_over_disagreeing_trusted_header` -> `TS-APM-001`
- `tests/api/unit/test_auth_precedence_matrix.py::test_trusted_header_resolves_when_bearer_token_missing` -> `TS-APM-002`
- `tests/api/unit/test_auth_observability.py::test_malformed_authorization_header_increments_metric_and_logs` -> `TS-APM-003`
- `tests/api/unit/test_app_user_startup.py::test_validate_startup_app_user_mode_rejects_production` -> `TS-APM-004`
- `tests/api/unit/test_auth_precedence_matrix.py::test_blank_trusted_header_falls_back_to_x_user_id_in_local` -> `TS-APM-005`
- `tests/api/unit/test_auth_precedence_matrix.py::test_blank_x_user_id_keeps_request_anonymous_without_parse_failure` -> `TS-APM-006`
- `tests/api/unit/test_auth_precedence_matrix.py::test_invalid_trusted_header_rejection_logs_and_counts_parse_failure` -> `TS-APM-007`

## Edge Cases
- Once an `Authorization` header is present, malformed or invalid JWTs must fail closed instead of consulting trusted headers or local `X-User-Id`.
- Whitespace-only trusted-header and `X-User-Id` values follow different contracts: blank trusted headers are ignored, while blank `X-User-Id` values keep the request anonymous.
- `APP_USER` remains a startup-only bootstrap contract; production safety depends on rejecting it before request handling begins.

## References
- `api/utils/database.py`
- `tests/api/unit/test_auth_precedence_matrix.py`
- `tests/api/unit/test_auth_observability.py`
- `tests/api/unit/test_app_user_startup.py`
