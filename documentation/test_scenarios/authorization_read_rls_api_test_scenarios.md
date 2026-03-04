# Authorization Read RLS API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: Security and API maintainers
- Created: 2026-02-26
- Last Updated: 2026-03-04
- Version: v0.2

## Change Log
- 2026-03-04 | v0.2 | Added transaction-scoped session identity propagation scenario to prove pooled DB connections do not leak identity across rapid alternating API requests.
- 2026-02-26 | v0.1 | Initial Phase 1 read-path authorization scenarios for `workflow.check_user_permission(...)` and inherited RLS read policies.

## Purpose
Define repeatable integration scenarios for Phase 1 read authorization enforcement.

## Scope
- In scope:
  - multi-role scope union on read paths
  - fail-closed read behavior for missing/unknown session user
  - fail-closed predicate behavior for invalid inputs and unresolved resources
  - inherited read filtering for `doc_revision`, `files`, and `files_commented`
  - transaction-scoped identity behavior across pooled API requests
- Out of scope:
  - write-path authorization (`read-write`, `WITH CHECK` policies)
  - IdP/JWT role mapping flow

## Design / Behavior
Authorization is enforced by a single DB predicate and RLS `USING` policies. Reads must be permitted only when capability + scope checks pass; all unknown/invalid contexts must deny access.

## Scenario Catalog
- `TS-AUTH-001`: User with two scoped roles gets union visibility across both scoped projects, including inherited entities.
- `TS-AUTH-002`: Missing or unknown `app.user_id` is fail-closed and returns no rows through read views.
- `TS-AUTH-003`: `workflow.check_user_permission(...)` returns `false` for invalid capability/resource, unresolved doc, or role-less user context.
- `TS-AUTH-004`: Rapid alternating API requests for different users do not leak `app.user` / `app.user_id` across pooled DB connections.

## Scenario Details

### TS-AUTH-001 Multi-Role Read Union
- Intent: Validate role superposition for read scope.
- Setup/Preconditions:
  - Create two non-super roles, each with `read-only` capability for `doc`, `doc_revision`, `files`, `files_commented`.
  - Attach role A scope to project A and role B scope to project B.
  - Assign both roles to the same user.
  - Prepare one document/revision/file/commented-file lineage per scoped project.
- Request/Action:
  - Query `workflow.v_documents`, `workflow.v_document_revisions`, `workflow.v_files`, and `workflow.v_files_commented` as that user.
- Expected:
  - Rows from both scoped projects are returned.
  - Project scope is authoritative; non-project lookups (`areas`, `units`) are not scope-filtered in this phase.
  - Inherited entities follow document authorization.
- Cleanup:
  - Remove test roles/scopes/assignments and test file rows.

### TS-AUTH-002 Fail-Closed Session Context
- Intent: Validate deny-by-default for missing/unknown session identity.
- Setup/Preconditions:
  - Prepare at least one document lineage that would be readable for a scoped user.
- Request/Action:
  - Execute read queries with `app.user_id=''`.
  - Execute same read queries with unknown `app.user_id` (for example `999999`).
- Expected:
  - No rows returned in both cases.
- Cleanup:
  - Remove test rows created for setup.

### TS-AUTH-003 Fail-Closed Predicate Inputs
- Intent: Validate strict predicate behavior.
- Setup/Preconditions:
  - Have at least one valid user and one valid document.
- Request/Action:
  - Call `workflow.check_user_permission(...)` with invalid capability.
  - Call with invalid resource.
  - Call with unresolved `p_doc_id`.
  - Call with role-less/unknown user.
- Expected:
  - Every call returns `false`.
- Cleanup:
  - None beyond role/test fixture cleanup.

### TS-AUTH-004 Transaction-Scoped Identity Isolation
- Intent: Validate that request identity is re-applied per DB transaction so pooled connections cannot leak the previous caller.
- Setup/Preconditions:
  - Have at least two resolvable users with distinct `user_id` / `user_acronym` values.
  - API is running with the normal pooled SQLAlchemy engine.
- Request/Action:
  - Send rapid alternating `GET /api/v1/people/users/current_user` requests with different `X-User-Id` values, including concurrent overlap.
- Expected:
  - Every response returns `200`.
  - Each response body resolves the same `user_id` and `user_acronym` as the request header that triggered it.
  - No response may return the other caller's identity.
- Cleanup:
  - None.

## Automated Test Mapping
- `tests/api/api/test_authorization_read_rls.py::test_read_rls_multi_role_scope_union` -> `TS-AUTH-001`
- `tests/api/api/test_authorization_read_rls.py::test_read_rls_fail_closed_for_missing_or_unknown_session_user` -> `TS-AUTH-002`
- `tests/api/api/test_authorization_read_rls.py::test_check_user_permission_fail_closed_inputs` -> `TS-AUTH-003`
- `tests/api/api/test_authorization_read_rls.py::test_current_user_identity_does_not_leak_across_rapid_requests` -> `TS-AUTH-004`

## References
- `documentation/authorization_rls_matrix.md`
- `ci/init/07_workflow.sql`
- `ci/init/09_security.sql`
- `tests/api/api/test_authorization_read_rls.py`
