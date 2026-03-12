# Written Comments API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-21
- Last Updated: 2026-03-12
- Version: v1.2

## Change Log
- 2026-03-12 | v1.2 | Removed create-time `user_id` from written-comments contract, bound authorship to effective session identity, and replaced missing-user coverage with request-field rejection coverage.
- 2026-03-04 | v1.1 | Added fail-closed session-identity scenario for written-comments router access.
- 2026-02-21 | v1.0 | Initial split from `files_commented_api_test_scenarios.md` into dedicated written-comments scenario contract.

## Purpose
Provide repeatable curl-based validation for written-comments endpoints.

## Scope
- In scope:
  - written comment list/create/update/delete
  - validation checks
  - authorization checks (author vs non-author)
- Out of scope:
  - commented-file upload/download endpoints

## Design / Behavior
Written comments are short text messages linked to revision (`rev_id`) and authored by the effective session user.
Create is bound to revision path (`/documents/revisions/{rev_id}/comments`).
Update/delete are item operations by comment id (`/documents/revisions/comments/{id}`) and require actor identity via `X-User-Id`.

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:4175
export API_PREFIX=/api/v1
```

## 2. Resolve IDs

```bash
PROJECT_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/projects" | jq -r '.[0].project_id')
DOC_ID=$(curl -s "$API_BASE$API_PREFIX/documents?project_id=$PROJECT_ID" | jq -r '.[0].doc_id')
REV_ID=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0].rev_id')
USER_ID=$(curl -s "$API_BASE$API_PREFIX/people/users" | jq -r '.[0].user_id')
USER_ACRONYM=$(curl -s "$API_BASE$API_PREFIX/people/users" | jq -r '.[0].user_acronym')
OTHER_USER_ACRONYM=$(curl -s "$API_BASE$API_PREFIX/people/users" | jq -r --arg uid "$USER_ID" '.[] | select((.user_id|tostring) != $uid and ((.role_name // "") | ascii_downcase) != "superuser" and ((.role_name // "") | ascii_downcase) != "admin") | .user_acronym' | head -n1)
```

## 3. TS-WC-001 Create/List/Delete

```bash
WRITTEN=$(curl -s -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ACRONYM" \
  -d "{\"comment_text\":\"Please verify IFC tag.\"}")
echo "$WRITTEN" | jq
WRITTEN_ID=$(echo "$WRITTEN" | jq -r '.id')

curl -i "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments?user_id=$USER_ID"
curl -i -X DELETE -H "X-User-Id: $USER_ACRONYM" "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_ID"
```

## 4. TS-WC-002 Validation

```bash
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -d "{}"

curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -d "{\"comment_text\":\"   \"}"
```

## 5. TS-WC-003 Missing References

```bash
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/999999/comments" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ACRONYM" \
  -d "{\"comment_text\":\"Missing rev\"}"
```

## 6. TS-WC-004 Reject user_id Field on Create

```bash
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ACRONYM" \
  -d "{\"user_id\":$USER_ID,\"comment_text\":\"Should fail\"}"
```

## 7. TS-WC-005 Delete Forbidden for Non-author

```bash
if [ -n "$OTHER_USER_ACRONYM" ]; then
  WRITTEN_2=$(curl -s -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
    -H "Content-Type: application/json" \
    -H "X-User-Id: $USER_ACRONYM" \
    -d "{\"comment_text\":\"Author-only delete check.\"}")
  WRITTEN_2_ID=$(echo "$WRITTEN_2" | jq -r '.id')

  curl -i -X DELETE -H "X-User-Id: $OTHER_USER_ACRONYM" "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_2_ID"
  curl -i -X DELETE -H "X-User-Id: $USER_ACRONYM" "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_2_ID"
fi
```

## 8. TS-WC-006 Update by Author

```bash
WRITTEN_3=$(curl -s -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ACRONYM" \
  -d "{\"comment_text\":\"Initial text\"}")
WRITTEN_3_ID=$(echo "$WRITTEN_3" | jq -r '.id')

curl -i -X PUT -H "Content-Type: application/json" -H "X-User-Id: $USER_ACRONYM" \
  -d '{"comment_text":"Updated text"}' \
  "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_3_ID"
```

## 9. TS-WC-007 Update Forbidden for Non-author

```bash
if [ -n "$OTHER_USER_ACRONYM" ]; then
  curl -i -X PUT -H "Content-Type: application/json" -H "X-User-Id: $OTHER_USER_ACRONYM" \
    -d '{"comment_text":"Not allowed update"}' \
    "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_3_ID"
fi

curl -i -X DELETE -H "X-User-Id: $USER_ACRONYM" "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_3_ID"
```

## Edge Cases
- If no second non-admin/non-superuser user exists, forbidden checks may need to be skipped.
- Blank `comment_text` is rejected by DB-level constraint mapping and may surface as `400`.

## Scenario Catalog
- `TS-WC-001` create/list/delete written comment succeeds.
- `TS-WC-002` validation errors are rejected (`400`/`422`).
- `TS-WC-003` create rejects missing revision reference (`404`).
- `TS-WC-004` create rejects request-body `user_id` field (`422`).
- `TS-WC-005` delete by non-author/non-superuser is rejected (`403`).
- `TS-WC-006` update by author succeeds.
- `TS-WC-007` update by non-author/non-superuser is rejected (`403`).
- `TS-WC-008` written-comments router denies requests when effective session identity is missing.

## Automated Test Mapping
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_crud` -> `TS-WC-001`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_validation` -> `TS-WC-002`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_missing_revision` -> `TS-WC-003`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_create_rejects_user_id_field` -> `TS-WC-004`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_delete_forbidden_non_author` -> `TS-WC-005`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_update` -> `TS-WC-006`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_update_forbidden_non_author` -> `TS-WC-007`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_require_session_identity` -> `TS-WC-008`

## References
- `tests/api/api/test_written_comments_endpoints.py`
- `api/routers/written_comments.py`
- `documentation/test_scenarios/files_commented_api_test_scenarios.md`
