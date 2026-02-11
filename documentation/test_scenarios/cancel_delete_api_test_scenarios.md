# Cancel and Delete API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-07
- Last Updated: 2026-02-11
- Version: v1.2

## Purpose
Provide repeatable curl-based validation for revision cancel and document delete behavior.

## Scope
- In scope:
  - revision cancel success and rejection paths
  - hard delete, void delete, idempotency, and missing-doc delete
- Out of scope:
  - status transition endpoint testing

## Design / Behavior
Cancellation must apply only to cancellable revisions. Delete must hard-delete or void according to revision state/history.

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:4175
export API_PREFIX=/api/v1
```

## 2. Resolve Existing Revision for Cancel Checks

```bash
PROJECT_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/projects" | jq -r '.[0].project_id')
DOC_ID=$(curl -s "$API_BASE$API_PREFIX/documents?project_id=$PROJECT_ID" | jq -r '.[0].doc_id')
REV_ID=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0].rev_id')
echo "DOC_ID=$DOC_ID REV_ID=$REV_ID"
```

## 3. TS-CD-001..003 Cancel Checks

```bash
# TS-CD-001 cancel revision
curl -i -X PATCH "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/cancel"

# TS-CD-001 idempotent cancel
curl -i -X PATCH "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/cancel"

# TS-CD-003 missing revision
curl -i -X PATCH "$API_BASE$API_PREFIX/documents/revisions/999999/cancel"
```

`TS-CD-002` (non-cancellable/final revision -> `409`) requires choosing a final-status revision from your environment.

## 4. Create Disposable Document for Delete Checks

```bash
AREA_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/areas" | jq -r '.[0].area_id')
UNIT_ID=$(curl -s "$API_BASE$API_PREFIX/lookups/units" | jq -r '.[0].unit_id')
TYPE_ID=$(curl -s "$API_BASE$API_PREFIX/documents/doc_types" | jq -r '.[0].type_id')
REV_CODE_ID=$(curl -s "$API_BASE$API_PREFIX/documents/revision_overview" | jq -r '.[0].rev_code_id')
PERSON_ID=$(curl -s "$API_BASE$API_PREFIX/people/persons" | jq -r '.[0].person_id')
TS=$(date +%s)

DOC_CREATE=$(curl -s -X POST "$API_BASE$API_PREFIX/documents" \
  -H "Content-Type: application/json" \
  -d "{
    \"doc_name_unique\": \"DOC-DEL-$TS\",
    \"title\": \"Delete Candidate $TS\",
    \"project_id\": $PROJECT_ID,
    \"type_id\": $TYPE_ID,
    \"area_id\": $AREA_ID,
    \"unit_id\": $UNIT_ID,
    \"rev_code_id\": $REV_CODE_ID,
    \"rev_author_id\": $PERSON_ID,
    \"rev_originator_id\": $PERSON_ID,
    \"rev_modifier_id\": $PERSON_ID,
    \"transmital_current_revision\": \"TR-DEL-$TS\",
    \"planned_start_date\": \"2024-01-01T00:00:00Z\",
    \"planned_finish_date\": \"2024-12-31T23:59:59Z\"
  }")
DOC_DEL_ID=$(echo "$DOC_CREATE" | jq -r '.doc_id')
echo "DOC_DEL_ID=$DOC_DEL_ID"
```

## 5. TS-CD-004 Hard Delete

```bash
curl -i -X DELETE "$API_BASE$API_PREFIX/documents/$DOC_DEL_ID"
curl -i "$API_BASE$API_PREFIX/documents/$DOC_DEL_ID/revisions"
```

## 6. TS-CD-005..007 Void/Idempotent/Concurrent Delete

Create another document and add second revision first:

```bash
DOC2=$(curl -s -X POST "$API_BASE$API_PREFIX/documents" \
  -H "Content-Type: application/json" \
  -d "{
    \"doc_name_unique\": \"DOC-VOID-$TS\",
    \"title\": \"Void Candidate $TS\",
    \"project_id\": $PROJECT_ID,
    \"type_id\": $TYPE_ID,
    \"area_id\": $AREA_ID,
    \"unit_id\": $UNIT_ID,
    \"rev_code_id\": $REV_CODE_ID,
    \"rev_author_id\": $PERSON_ID,
    \"rev_originator_id\": $PERSON_ID,
    \"rev_modifier_id\": $PERSON_ID,
    \"transmital_current_revision\": \"TR-VOID-$TS\",
    \"planned_start_date\": \"2024-01-01T00:00:00Z\",
    \"planned_finish_date\": \"2024-12-31T23:59:59Z\"
  }")
DOC_VOID_ID=$(echo "$DOC2" | jq -r '.doc_id')
BASE_REV=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_VOID_ID/revisions" | jq -r '.[0]')

curl -i -X POST "$API_BASE$API_PREFIX/documents/$DOC_VOID_ID/revisions" \
  -H "Content-Type: application/json" \
  -d "{
    \"rev_code_id\": $(echo "$BASE_REV" | jq -r '.rev_code_id'),
    \"rev_author_id\": $(echo "$BASE_REV" | jq -r '.rev_author_id'),
    \"rev_originator_id\": $(echo "$BASE_REV" | jq -r '.rev_originator_id'),
    \"rev_modifier_id\": $(echo "$BASE_REV" | jq -r '.rev_modifier_id'),
    \"transmital_current_revision\": \"TR-VOID-2-$TS\",
    \"planned_start_date\": \"$(echo "$BASE_REV" | jq -r '.planned_start_date')\",
    \"planned_finish_date\": \"$(echo "$BASE_REV" | jq -r '.planned_finish_date')\"
  }"

# TS-CD-005 void delete expected
curl -i -X DELETE "$API_BASE$API_PREFIX/documents/$DOC_VOID_ID"

# TS-CD-006 idempotent delete
curl -i -X DELETE "$API_BASE$API_PREFIX/documents/$DOC_VOID_ID"
```

`TS-CD-007` can be executed by sending two deletes in parallel shells for `DOC_VOID_ID`.

## 7. TS-CD-008 Missing Document

```bash
curl -i -X DELETE "$API_BASE$API_PREFIX/documents/999999"
```

## Edge Cases
- Cancel tests depend on current workflow statuses in seed data.
- Concurrency checks depend on network timing and may return `200`/`404` mix.

## Scenario Catalog
- `TS-CD-001` cancel revision sets and persists `canceled_date`.
- `TS-CD-002` cancel final/non-cancellable revision returns `409`.
- `TS-CD-003` cancel missing revision returns `404`.
- `TS-CD-004` deleting single-revision document performs hard delete.
- `TS-CD-005` deleting multi-revision document performs void behavior.
- `TS-CD-006` repeated delete on voided document is idempotent.
- `TS-CD-007` concurrent delete requests are safe.
- `TS-CD-008` deleting missing document returns `404`.

## Automated Test Mapping
- `tests/api/api/test_cancel_delete_endpoints.py::test_cancel_revision` -> `TS-CD-001`
- `tests/api/api/test_cancel_delete_endpoints.py::test_cancel_revision_not_cancellable` -> `TS-CD-002`
- `tests/api/api/test_cancel_delete_endpoints.py::test_cancel_revision_not_found` -> `TS-CD-003`
- `tests/api/api/test_cancel_delete_endpoints.py::test_delete_document_hard_delete_cascade` -> `TS-CD-004`
- `tests/api/api/test_cancel_delete_endpoints.py::test_delete_document_void` -> `TS-CD-005`
- `tests/api/api/test_cancel_delete_endpoints.py::test_delete_document_void_idempotent` -> `TS-CD-006`
- `tests/api/api/test_cancel_delete_endpoints.py::test_delete_document_concurrent_requests` -> `TS-CD-007`
- `tests/api/api/test_cancel_delete_endpoints.py::test_delete_document_not_found` -> `TS-CD-008`

## References
- `tests/api/api/test_cancel_delete_endpoints.py`
- `api/routers/documents.py`
