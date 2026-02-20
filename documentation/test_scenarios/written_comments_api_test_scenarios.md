# Written Comments API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-21
- Last Updated: 2026-02-21
- Version: v1.0

## Change Log
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
Written comments are short text messages linked to revision (`rev_id`) and user (`user_id`).
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
OTHER_USER_ID=$(curl -s "$API_BASE$API_PREFIX/people/users" | jq -r --arg uid "$USER_ID" '.[] | select((.user_id|tostring) != $uid and ((.role_name // "") | ascii_downcase) != "superuser" and ((.role_name // "") | ascii_downcase) != "admin") | .user_id' | head -n1)
```

## 3. TS-WC-001 Create/List/Delete

```bash
WRITTEN=$(curl -s -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER_ID,\"comment_text\":\"Please verify IFC tag.\"}")
echo "$WRITTEN" | jq
WRITTEN_ID=$(echo "$WRITTEN" | jq -r '.id')

curl -i "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments?user_id=$USER_ID"
curl -i -X DELETE -H "X-User-Id: $USER_ID" "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_ID"
```

## 4. TS-WC-002 Validation

```bash
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER_ID}"

curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER_ID,\"comment_text\":\"   \"}"
```

## 5. TS-WC-003 Missing References

```bash
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/999999/comments" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER_ID,\"comment_text\":\"Missing rev\"}"

curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":999999,\"comment_text\":\"Missing user\"}"
```

## 6. TS-WC-004 Delete Forbidden for Non-author

```bash
if [ -n "$OTHER_USER_ID" ]; then
  WRITTEN_2=$(curl -s -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":$USER_ID,\"comment_text\":\"Author-only delete check.\"}")
  WRITTEN_2_ID=$(echo "$WRITTEN_2" | jq -r '.id')

  curl -i -X DELETE -H "X-User-Id: $OTHER_USER_ID" "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_2_ID"
  curl -i -X DELETE -H "X-User-Id: $USER_ID" "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_2_ID"
fi
```

## 7. TS-WC-005 Update by Author

```bash
WRITTEN_3=$(curl -s -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/comments" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER_ID,\"comment_text\":\"Initial text\"}")
WRITTEN_3_ID=$(echo "$WRITTEN_3" | jq -r '.id')

curl -i -X PUT -H "Content-Type: application/json" -H "X-User-Id: $USER_ID" \
  -d '{"comment_text":"Updated text"}' \
  "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_3_ID"
```

## 8. TS-WC-006 Update Forbidden for Non-author

```bash
if [ -n "$OTHER_USER_ID" ]; then
  curl -i -X PUT -H "Content-Type: application/json" -H "X-User-Id: $OTHER_USER_ID" \
    -d '{"comment_text":"Not allowed update"}' \
    "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_3_ID"
fi

curl -i -X DELETE -H "X-User-Id: $USER_ID" "$API_BASE$API_PREFIX/documents/revisions/comments/$WRITTEN_3_ID"
```

## Edge Cases
- If no second non-admin/non-superuser user exists, forbidden checks may need to be skipped.
- Blank `comment_text` is rejected by DB-level constraint mapping and may surface as `400`.

## Scenario Catalog
- `TS-WC-001` create/list/delete written comment succeeds.
- `TS-WC-002` validation errors are rejected (`400`/`422`).
- `TS-WC-003` create rejects missing revision/user references (`404`).
- `TS-WC-004` delete by non-author/non-superuser is rejected (`403`).
- `TS-WC-005` update by author succeeds.
- `TS-WC-006` update by non-author/non-superuser is rejected (`403`).

## Automated Test Mapping
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_crud` -> `TS-WC-001`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_validation` -> `TS-WC-002`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_missing_references` -> `TS-WC-003`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_delete_forbidden_non_author` -> `TS-WC-004`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_update` -> `TS-WC-005`
- `tests/api/api/test_written_comments_endpoints.py::test_written_comments_update_forbidden_non_author` -> `TS-WC-006`

## References
- `tests/api/api/test_written_comments_endpoints.py`
- `api/routers/written_comments.py`
- `documentation/test_scenarios/files_commented_api_test_scenarios.md`
