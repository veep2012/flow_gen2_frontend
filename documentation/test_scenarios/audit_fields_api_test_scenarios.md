# Audit Fields API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-07
- Last Updated: 2026-02-11
- Version: v1.2

## Purpose
Provide repeatable curl-based validation for audit fields across documents, revisions, files, and commented files.

## Scope
- In scope:
  - `created_by`, `updated_by`, `created_at`, `updated_at` checks
  - cross-user updates via `X-User-Id`
- Out of scope:
  - non-audit validation semantics

## Design / Behavior
Every create/update operation must persist audit metadata and update actor attribution correctly.

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:4175
export API_PREFIX=/api/v1
```

## 2. Resolve Seed IDs

```bash
AREA_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/areas" | jq -r '.[0].area_id')
UNIT_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/units" | jq -r '.[0].unit_id')
PROJECT_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/projects" | jq -r '.[0].project_id')
TYPE_ID=$(curl -s "$API_BASE$API_PREFIX/documents/doc_types" | jq -r '.[0].type_id')
REV_CODE_ID=$(curl -s "$API_BASE$API_PREFIX/documents/revision_overview" | jq -r '.[0].rev_code_id')
PERSON_ID=$(curl -s "$API_BASE$API_PREFIX/people/persons" | jq -r '.[0].person_id')
TS=$(date +%s)
echo "AREA_ID=$AREA_ID UNIT_ID=$UNIT_ID PROJECT_ID=$PROJECT_ID TYPE_ID=$TYPE_ID REV_CODE_ID=$REV_CODE_ID PERSON_ID=$PERSON_ID"
```

## 3. TS-AUD-001 Document and Revision Audit Fields

Create document as user `1`:

```bash
DOC_CREATE=$(curl -s -X POST "$API_BASE$API_PREFIX/documents" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d "{
    \"doc_name_unique\": \"DOC-AUD-$TS\",
    \"title\": \"Audit Document $TS\",
    \"project_id\": $PROJECT_ID,
    \"type_id\": $TYPE_ID,
    \"area_id\": $AREA_ID,
    \"unit_id\": $UNIT_ID,
    \"rev_code_id\": $REV_CODE_ID,
    \"rev_author_id\": $PERSON_ID,
    \"rev_originator_id\": $PERSON_ID,
    \"rev_modifier_id\": $PERSON_ID,
    \"transmital_current_revision\": \"TR-$TS\",
    \"planned_start_date\": \"2024-01-01T00:00:00Z\",
    \"planned_finish_date\": \"2024-12-31T23:59:59Z\"
  }")
echo "$DOC_CREATE" | jq '{doc_id,created_by,updated_by,created_at,updated_at}'
DOC_ID=$(echo "$DOC_CREATE" | jq -r '.doc_id')
```

Update document as user `2`:

```bash
curl -s -X PUT "$API_BASE$API_PREFIX/documents/$DOC_ID" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 2" \
  -d "{\"title\":\"Audit Document Updated $TS\"}" | jq '{doc_id,created_by,updated_by,updated_at}'
```

Get revision and update as user `3`:

```bash
REV_ID=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0].rev_id')
curl -s -X PUT "$API_BASE$API_PREFIX/documents/revisions/$REV_ID" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 3" \
  -d "{\"transmital_current_revision\":\"TR-AUD-$TS\"}" | jq '{rev_id,created_by,updated_by,created_at,updated_at}'
```

## 4. TS-AUD-002 Files and Commented Files Audit Fields

Upload base file as user `1`:

```bash
FILE_CREATE=$(curl -s -X POST "$API_BASE$API_PREFIX/files/" \
  -H "X-User-Id: 1" \
  -F "rev_id=$REV_ID" \
  -F "file=@/etc/hosts;type=application/pdf;filename=audit-$TS.pdf")
echo "$FILE_CREATE" | jq '{id,file_id,created_by,updated_by,created_at,updated_at}'
FILE_ID=$(echo "$FILE_CREATE" | jq -r '.id // .file_id')
```

Upload commented file as user `2`:

```bash
curl -s -X POST "$API_BASE$API_PREFIX/files/commented/" \
  -H "X-User-Id: 2" \
  -F "file_id=$FILE_ID" \
  -F "user_id=1" \
  -F "file=@/etc/hosts;type=application/pdf;filename=commented-$TS.pdf" | jq '{id,file_id,user_id,created_by,updated_by,created_at,updated_at}'
```

## Edge Cases
- If any lookup endpoint returns empty arrays, seed data is missing and this plan is not applicable.
- `id` and `file_id` may vary by response shape; both are accepted.

## Scenario Catalog
- `TS-AUD-001`: document/revision audit fields are set and updated correctly.
- `TS-AUD-002`: files/commented files audit fields are set with caller identity.

## Automated Test Mapping
- `tests/api/api/test_audit_fields.py::test_audit_fields_document_and_revision` -> `TS-AUD-001`
- `tests/api/api/test_audit_fields.py::test_audit_fields_files_and_commented` -> `TS-AUD-002`

## References
- `tests/api/api/test_audit_fields.py`
- `api/routers/documents.py`
- `api/routers/files.py`
