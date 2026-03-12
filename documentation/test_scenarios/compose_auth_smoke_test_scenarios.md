# Compose Auth Smoke Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-03-12
- Last Updated: 2026-03-12
- Version: v0.1
- Related Tickets: TD-20260307-01

## Change Log
- 2026-03-12 | v0.1 | Initial scenario contract for `make test-compose` auth and ingress smoke validation against the running compose stack.

## Purpose
Define the scenario contract for the shell-based compose auth smoke verification that runs against the already started `make up` environment.

## Scope
- In scope:
  - compose stack readiness prerequisites for nginx and Keycloak
  - unauthenticated API ingress redirect behavior
  - bearer-token passthrough through nginx to the API
  - invalid bearer-token fail-closed behavior
  - cookie-based login through oauth2-proxy and Keycloak to `current_user`
- Out of scope:
  - compose lifecycle management
  - broad API regression coverage already handled by `make test`
  - performance, load, and browser UI coverage

## Audience
- Backend Team
- API maintainers
- Developers validating the local compose auth stack before merge

## Definitions
- Compose auth smoke: A targeted verification pass executed by `make test-compose` against the already running compose stack.
- Edge ingress: The nginx + oauth2-proxy + Keycloak path exposed on `http://localhost`.
- Current user endpoint: `GET /api/v1/people/users/current_user`.

## Background / Context
The normal `make test` flow validates API behavior against the local test stack without Keycloak, oauth2-proxy, or nginx. `make test-compose` exists to cover only the auth and ingress behaviors that require the full compose environment to be running first.

## Requirements
### Functional Requirements
- FR-1: `make test-compose` must fail if the running compose stack does not expose a reachable Keycloak discovery endpoint.
- FR-2: `make test-compose` must fail if nginx is not reachable on the configured base URL.
- FR-3: Unauthenticated access to `GET /api/v1/people/users/current_user` through nginx must redirect into the Keycloak authorization flow.
- FR-4: A valid bearer token issued by the seeded `flow-ui` Keycloak client must resolve the expected current user through nginx.
- FR-5: An invalid bearer token must fail closed with `401 Unauthorized`.
- FR-6: A cookie-based login through oauth2-proxy and Keycloak must resolve the expected current user through nginx.

### Non-Functional Requirements
- NFR-1: The smoke flow should stay deterministic by using seeded local realm users and clients only.
- NFR-2: The smoke flow should avoid managing compose lifecycle and should assume `make up` is already running.
- NFR-3: The smoke flow should emit enough command/result detail to debug ingress or auth failures quickly.

## Design / Behavior
`make test-compose` runs `scripts/test-compose.sh` against the already running compose environment.

The script must:
- wait for Keycloak discovery and nginx favicon endpoints to respond
- verify that unauthenticated API ingress redirects to the Keycloak auth flow
- obtain a token for the seeded `flow-ui` public client using the seeded test user
- call `current_user` through nginx with a valid bearer token
- call the same endpoint with an invalid bearer token and require `401`
- perform a cookie-based login flow and require a successful JSON `current_user` response

## Edge Cases
- Compose stack not started: readiness checks fail early with a clear message.
- Keycloak started but realm import or discovery unavailable: readiness check fails before token or cookie checks run.
- oauth2-proxy misconfigured: unauthenticated redirect or cookie-login flow fails.
- nginx bearer passthrough regressed: bearer-token request does not return the expected current user.
- wrong seeded user credentials or acronym override: token or cookie checks fail with an unexpected user identity.

## Testing Strategy
- Unit tests:
  - None. This flow is intentionally shell-based because it depends on the already running compose environment.
- Integration tests:
  - `make test-compose`
- Manual verification:
  - Start the full stack with `make up`.
  - Run `make test-compose`.
  - Review the emitted request/response summary lines for any failing step.

## Automated Test Mapping
- `scripts/test-compose.sh` -> `TS-CAS-001`, `TS-CAS-002`, `TS-CAS-003`, `TS-CAS-004`, `TS-CAS-005`

## Scenario Catalog
- `TS-CAS-001` Compose auth prerequisites are reachable before ingress checks run.
- `TS-CAS-002` Unauthenticated `current_user` ingress redirects into the Keycloak auth flow.
- `TS-CAS-003` Valid bearer-token ingress resolves the expected current user.
- `TS-CAS-004` Invalid bearer-token ingress fails closed with `401`.
- `TS-CAS-005` Cookie-based login through oauth2-proxy and Keycloak resolves the expected current user.

## Scenario Details

### TS-CAS-001 Compose Auth Prerequisites Reachable
- Intent: Confirm the running compose stack exposes the minimum live endpoints needed for auth smoke execution.
- Setup/Preconditions:
  - The full compose stack is already running via `make up`.
- Request/Action:
  - Call the Keycloak discovery endpoint.
  - Call the nginx favicon endpoint.
- Expected:
  - Both endpoints return success.
- Cleanup:
  - None.

### TS-CAS-002 Unauthenticated Ingress Redirect
- Intent: Confirm unauthenticated API ingress enters the expected auth flow instead of leaking API access.
- Setup/Preconditions:
  - The full compose stack is running.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user` without credentials through nginx.
- Expected:
  - Response redirects into the Keycloak authorization endpoint.
- Cleanup:
  - None.

### TS-CAS-003 Valid Bearer Token Passthrough
- Intent: Confirm nginx bypasses oauth2-proxy for bearer-token API requests and the API resolves identity from the verified token.
- Setup/Preconditions:
  - The full compose stack is running.
  - The seeded Keycloak user credentials are valid.
- Request/Action:
  - Obtain a bearer token from the `flow-ui` client.
  - Call `GET /api/v1/people/users/current_user` through nginx with that token.
- Expected:
  - Response is `200 OK`.
  - Returned `user_acronym` matches the expected seeded user.
- Cleanup:
  - None.

### TS-CAS-004 Invalid Bearer Token Fails Closed
- Intent: Confirm direct bearer-token ingress does not fall back to a lower-priority auth source.
- Setup/Preconditions:
  - The full compose stack is running.
- Request/Action:
  - Call `GET /api/v1/people/users/current_user` through nginx with an invalid bearer token.
- Expected:
  - Response is `401 Unauthorized`.
- Cleanup:
  - None.

### TS-CAS-005 Cookie Login Flow Resolves Current User
- Intent: Confirm the oauth2-proxy + Keycloak cookie/session flow reaches the protected API successfully.
- Setup/Preconditions:
  - The full compose stack is running.
  - The seeded Keycloak user credentials are valid.
- Request/Action:
  - Start an unauthenticated request to `current_user` through nginx.
  - Submit the Keycloak login form with the seeded user credentials.
- Expected:
  - Final response is JSON from `current_user`.
  - Returned `user_acronym` matches the expected seeded user.
- Cleanup:
  - None.

## References
- `README.md`
- `ci/docker-compose.yml`
- `ci/nginx/default.conf`
- `ci/keycloak/flow-local-realm.json`
- `scripts/test-compose.sh`
