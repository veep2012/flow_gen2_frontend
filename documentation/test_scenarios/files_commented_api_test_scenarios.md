# Files Commented API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-07
- Last Updated: 2026-03-13
- Version: v1.10

## Change Log
- 2026-03-13 | v1.10 | Added owner-or-superuser authorization scenario for commented-file replace, documenting fail-closed `403`/`404` behavior and shifted scenario/test mappings.
- 2026-03-12 | v1.9 | Added commented-file replace endpoint scenario and automated coverage mapping, removed create-time `user_id` form field from commented-file scenarios, and bound create authorship to effective session identity.
- 2026-03-04 | v1.7 | Added fail-closed session-identity scenario for commented-files router access.
- 2026-02-21 | v1.6 | Added written comments scenarios and mappings, added update scenarios, moved automated mapping to dedicated test module/router references, and split written-comments scenarios into dedicated `written_comments_api_test_scenarios.md`
- 2026-02-20 | v1.5 | Updated commented download examples to use query parameter `id`.
- 2026-02-19 | v1.4 | Added scenario for insert without file and synchronized mapping.

## Purpose
Provide repeatable curl-based validation for commented-file endpoints.

## Scope
- In scope:
  - list/filter behavior
  - commented file insert/replace/download/delete
  - duplicate and validation checks
- Out of scope:
  - base files API full validation

## Design / Behavior
Commented files are user-specific derivatives and must enforce uniqueness for `(file_id, user_id)`.
Returned/downloaded commented `filename` is the commented object name derived from `s3_uid` (not the original source filename).

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:4175
export API_PREFIX=/api/v1
```

## 2. Resolve IDs and Upload Base File

```bash
PROJECT_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/projects" | jq -r '.[0].project_id')
DOC_ID=$(curl -s "$API_BASE$API_PREFIX/documents?project_id=$PROJECT_ID" | jq -r '.[0].doc_id')
REV_ID=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0].rev_id')
USER_ID=$(curl -s "$API_BASE$API_PREFIX/people/users" | jq -r '.[0].user_id')
USER_ACRONYM=$(curl -s "$API_BASE$API_PREFIX/people/users" | jq -r '.[0].user_acronym')
TS=$(date +%s)

BASE_FILE=$(curl -s -X POST "$API_BASE$API_PREFIX/files/" \
  -F "rev_id=$REV_ID" \
  -F "file=@/etc/hosts;type=application/pdf;filename=base-$TS.pdf")
FILE_ID=$(echo "$BASE_FILE" | jq -r '.id')
echo "FILE_ID=$FILE_ID USER_ID=$USER_ID USER_ACRONYM=$USER_ACRONYM"
```

## 3. TS-FC-001..003 List Endpoints

```bash
# TS-FC-001
curl -i "$API_BASE$API_PREFIX/files/commented/list?file_id=$FILE_ID"

# TS-FC-002
curl -i "$API_BASE$API_PREFIX/files/commented/list?file_id=$FILE_ID&user_id=$USER_ID"

# TS-FC-003
curl -i "$API_BASE$API_PREFIX/files/commented/list"
```

## 4. TS-FC-004 Insert/Download/Delete Flow

```bash
COMMENTED=$(curl -s -X POST "$API_BASE$API_PREFIX/files/commented/" \
  -H "X-User-Id: $USER_ACRONYM" \
  -F "file_id=$FILE_ID" \
  -F "file=@/etc/hosts;type=application/pdf;filename=commented-$TS.pdf")
echo "$COMMENTED" | jq
COMMENTED_ID=$(echo "$COMMENTED" | jq -r '.id')

curl -i "$API_BASE$API_PREFIX/files/commented/download?id=$COMMENTED_ID"
curl -i -X DELETE "$API_BASE$API_PREFIX/files/commented/$COMMENTED_ID"
```

## 5. TS-FC-005..010 Negative Checks

```bash
# TS-FC-005 duplicate insert
curl -i -X POST "$API_BASE$API_PREFIX/files/commented/" \
  -H "X-User-Id: $USER_ACRONYM" \
  -F "file_id=$FILE_ID" \
  -F "file=@/etc/hosts;type=application/pdf;filename=dup-$TS.pdf"

# TS-FC-006 delete missing
curl -i -X DELETE "$API_BASE$API_PREFIX/files/commented/999999"

# TS-FC-007 download missing
curl -i "$API_BASE$API_PREFIX/files/commented/download?id=999999"

# TS-FC-008 missing fields
curl -i -X POST "$API_BASE$API_PREFIX/files/commented/" -H "X-User-Id: $USER_ACRONYM" -F "file=@/etc/hosts;type=application/pdf;filename=missing.pdf"

# TS-FC-009 nonexistent references
curl -i -X POST "$API_BASE$API_PREFIX/files/commented/" -H "X-User-Id: $USER_ACRONYM" -F "file=@/etc/hosts;type=application/pdf;filename=missing.pdf" -F "file_id=999999"

# TS-FC-010 mimetype mismatch
curl -i -X POST "$API_BASE$API_PREFIX/files/commented/" \
  -H "X-User-Id: $USER_ACRONYM" \
  -F "file_id=$FILE_ID" \
  -F "file=@/etc/hosts;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document;filename=commented-$TS.docx"
```

## 6. TS-FC-011 Insert Without `file` Copies Source

```bash
COPIED=$(curl -s -X POST "$API_BASE$API_PREFIX/files/commented/" \
  -H "X-User-Id: $USER_ACRONYM" \
  -F "file_id=$FILE_ID")
echo "$COPIED" | jq
COPIED_ID=$(echo "$COPIED" | jq -r '.id')

curl -i "$API_BASE$API_PREFIX/files/commented/download?id=$COPIED_ID"
curl -i -X DELETE "$API_BASE$API_PREFIX/files/commented/$COPIED_ID"
```

## 7. TS-FC-012 Replace Existing Commented File

```bash
REPLACE_SRC=$(curl -s -X POST "$API_BASE$API_PREFIX/files/commented/" \
  -H "X-User-Id: $USER_ACRONYM" \
  -F "file_id=$FILE_ID" \
  -F "file=@/etc/hosts;type=application/pdf;filename=replace-src-$TS.pdf")
echo "$REPLACE_SRC" | jq
REPLACE_ID=$(echo "$REPLACE_SRC" | jq -r '.id')

curl -s -X POST "$API_BASE$API_PREFIX/files/commented/$REPLACE_ID/replace" \
  -H "X-User-Id: $USER_ACRONYM" \
  -F "file=@/etc/services;type=application/pdf;filename=replace-new-$TS.pdf" | jq

curl -i "$API_BASE$API_PREFIX/files/commented/download?id=$REPLACE_ID"
curl -i -X DELETE "$API_BASE$API_PREFIX/files/commented/$REPLACE_ID"
```

## 8. TS-FC-013 Replace Forbidden For Non-Owner

```bash
OTHER_USER_ACRONYM=$(curl -s "$API_BASE$API_PREFIX/people/users" | jq -r --arg SELF "$USER_ACRONYM" '.[] | select(.user_acronym != $SELF and ((.role_name // "") | ascii_downcase) != "superuser" and ((.role_name // "") | ascii_downcase) != "admin") | .user_acronym' | head -n 1)

curl -i -X POST "$API_BASE$API_PREFIX/files/commented/$REPLACE_ID/replace" \
  -H "X-User-Id: $OTHER_USER_ACRONYM" \
  -F "file=@/etc/services;type=application/pdf;filename=replace-forbidden-$TS.pdf"
```

## 9. TS-FC-014 Replace Missing Commented File

```bash
curl -i -X POST "$API_BASE$API_PREFIX/files/commented/999999/replace" \
  -H "X-User-Id: $USER_ACRONYM" \
  -F "file=@/etc/services;type=application/pdf;filename=replace-missing-$TS.pdf"
```

## Edge Cases
- Some environments may return `400` or `415` for mimetype mismatch.
- If base file creation fails, remaining commented-file checks are blocked.

## Scenario Catalog
- `TS-FC-001` list commented files by `file_id` succeeds.
- `TS-FC-002` list commented files by `file_id` and `user_id` succeeds.
- `TS-FC-003` list without `file_id` is rejected (`422`).
- `TS-FC-004` insert/list/download/delete commented file succeeds.
- `TS-FC-005` duplicate commented insert is rejected (`400`).
- `TS-FC-006` delete missing commented file returns `404`.
- `TS-FC-007` download missing commented file returns `404`.
- `TS-FC-008` missing insert fields are rejected (`422`).
- `TS-FC-009` missing file reference returns `404`.
- `TS-FC-010` mimetype mismatch rejected (`400`/`415`).
- `TS-FC-011` insert without multipart `file` copies source file bytes from `file_id`.
- `TS-FC-012` replace existing commented file succeeds and preserves the same commented-file id.
- `TS-FC-013` replace is rejected for a non-owner non-superuser actor; response may be `403` or fail-closed `404` when read-side RLS hides the row.
- `TS-FC-014` replace missing commented file returns `404`.
- `TS-FC-015` commented-files router denies requests when effective session identity is missing.

## Automated Test Mapping
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_list` -> `TS-FC-001`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_list_with_user_filter` -> `TS-FC-002`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_list_missing_file_id` -> `TS-FC-003`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_insert_and_download` -> `TS-FC-004`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_insert_duplicate` -> `TS-FC-005`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_delete_nonexistent` -> `TS-FC-006`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_download_nonexistent` -> `TS-FC-007`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_insert_missing_fields` -> `TS-FC-008`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_insert_nonexistent_file` -> `TS-FC-009`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_insert_mimetype_mismatch` -> `TS-FC-010`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_insert_without_file_copies_source` -> `TS-FC-011`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_replace` -> `TS-FC-012`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_replace_forbidden_for_non_owner` -> `TS-FC-013`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_replace_nonexistent` -> `TS-FC-014`
- `tests/api/api/test_files_commented_endpoints.py::test_files_commented_require_session_identity` -> `TS-FC-015`

## References
- `tests/api/api/test_files_commented_endpoints.py`
- `api/routers/files_commented.py`
