# Files API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-07
- Last Updated: 2026-02-11
- Version: v1.2

## Purpose
Provide repeatable curl-based validation for files upload/update/list/download/delete and input validation.

## Scope
- In scope:
  - file CRUD lifecycle
  - accepted and rejected upload shapes
- Out of scope:
  - commented-file routes

## Design / Behavior
Files API must enforce validation, preserve immutable identity, and support reliable binary download.

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:4175
export API_PREFIX=/api/v1
```

## 2. Resolve Revision ID

```bash
PROJECT_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/projects" | jq -r '.[0].project_id')
DOC_ID=$(curl -s "$API_BASE$API_PREFIX/documents?project_id=$PROJECT_ID" | jq -r '.[0].doc_id')
REV_ID=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0].rev_id')
TS=$(date +%s)
echo "PROJECT_ID=$PROJECT_ID DOC_ID=$DOC_ID REV_ID=$REV_ID"
```

## 3. TS-F-001 File CRUD + Download

```bash
UPLOAD=$(curl -s -X POST "$API_BASE$API_PREFIX/files/" \
  -F "rev_id=$REV_ID" \
  -F "file=@/etc/hosts;type=application/pdf;filename=file-$TS.pdf")
echo "$UPLOAD" | jq
FILE_ID=$(echo "$UPLOAD" | jq -r '.id')

curl -s -X PUT "$API_BASE$API_PREFIX/files/$FILE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"filename\":\"file-$TS-v2.pdf\"}" | jq

curl -s "$API_BASE$API_PREFIX/files?rev_id=$REV_ID" | jq
curl -i "$API_BASE$API_PREFIX/files/$FILE_ID/download"
curl -i -X DELETE "$API_BASE$API_PREFIX/files/$FILE_ID"
```

## 4. Validation Checks (TS-F-002..TS-F-009)

```bash
# TS-F-002: reject id in body
curl -i -X PUT "$API_BASE$API_PREFIX/files/$FILE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"id\":$FILE_ID,\"filename\":\"bad.pdf\"}"

# TS-F-003: empty file rejected
curl -i -X POST "$API_BASE$API_PREFIX/files/" -F "rev_id=$REV_ID" -F "file=@/dev/null;filename=empty.txt;type=text/plain"

# TS-F-004: long filename rejected
LONG_NAME=$(printf 'a%.0s' {1..91}).txt
curl -i -X POST "$API_BASE$API_PREFIX/files/" -F "rev_id=$REV_ID" -F "file=@/etc/hosts;filename=$LONG_NAME;type=text/plain"

# TS-F-005: missing revision
curl -i -X POST "$API_BASE$API_PREFIX/files/" -F "rev_id=999999" -F "file=@/etc/hosts;filename=missing-rev.txt;type=text/plain"

# TS-F-006: unaccepted type
curl -i -X POST "$API_BASE$API_PREFIX/files/" -F "rev_id=$REV_ID" -F "file=@/etc/hosts;filename=file-$TS.txt;type=text/plain"

# TS-F-007: accepted pdf
curl -i -X POST "$API_BASE$API_PREFIX/files/" -F "rev_id=$REV_ID" -F "file=@/etc/hosts;filename=ok-$TS.pdf;type=application/pdf"

# TS-F-008: no extension
curl -i -X POST "$API_BASE$API_PREFIX/files/" -F "rev_id=$REV_ID" -F "file=@/etc/hosts;filename=no_extension;type=application/octet-stream"
```

`TS-F-009` (concurrent uploads) is best validated by running two upload curls in parallel shells.

## Edge Cases
- `/etc/hosts` is used as portable local test payload.
- If your shell does not support brace expansion in `LONG_NAME`, construct it with another method.

## Scenario Catalog
- `TS-F-001` file CRUD and binary download roundtrip succeeds.
- `TS-F-002` update with body `id` is rejected (`422`).
- `TS-F-003` empty file upload is rejected (`400`).
- `TS-F-004` too-long filename is rejected (`400`).
- `TS-F-005` upload for missing revision returns `404`.
- `TS-F-006` unaccepted file type is rejected (`400`).
- `TS-F-007` accepted PDF upload succeeds (`201`).
- `TS-F-008` filename without extension is rejected (`400`).
- `TS-F-009` concurrent uploads to same revision succeed.

## Automated Test Mapping
- `tests/api/api/test_files_endpoints.py::test_files_crud_and_download` -> `TS-F-001`
- `tests/api/api/test_files_endpoints.py::test_files_update_rejects_id_in_body` -> `TS-F-002`
- `tests/api/api/test_files_endpoints.py::test_files_insert_empty_file_rejected` -> `TS-F-003`
- `tests/api/api/test_files_endpoints.py::test_files_insert_long_filename_rejected` -> `TS-F-004`
- `tests/api/api/test_files_endpoints.py::test_files_insert_nonexistent_revision` -> `TS-F-005`
- `tests/api/api/test_files_endpoints.py::test_files_insert_unaccepted_file_type_rejected` -> `TS-F-006`
- `tests/api/api/test_files_endpoints.py::test_files_insert_accepted_file_type_pdf` -> `TS-F-007`
- `tests/api/api/test_files_endpoints.py::test_files_insert_no_extension_rejected` -> `TS-F-008`
- `tests/api/api/test_files_endpoints.py::test_files_concurrent_uploads_same_revision` -> `TS-F-009`

## References
- `tests/api/api/test_files_endpoints.py`
- `api/routers/files.py`
