# Documents Revisions API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-07
- Last Updated: 2026-03-04
- Version: v1.3

## Change Log
- 2026-03-04 | v1.3 | Added fail-closed session-identity scenario for revisions router reads.
- 2026-02-20 | v1.2 | Added Change Log section for standards compliance

## Purpose
Provide repeatable curl-based validation for revisions list/update/create and status transitions.

## Scope
- In scope:
  - list and missing-document behavior
  - create/update validations
  - status transition forward/back paths
- Out of scope:
  - document delete/cancel behavior

## Design / Behavior
Revision APIs must enforce required fields, status immutability on update, and workflow transition constraints.

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
TS=$(date +%s)
echo "PROJECT_ID=$PROJECT_ID DOC_ID=$DOC_ID REV_ID=$REV_ID"
```

## 3. TS-REV-001..006 List/Update Checks

```bash
# TS-REV-001
curl -i "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions"

# TS-REV-002
curl -i "$API_BASE$API_PREFIX/documents/999999/revisions"

# TS-REV-003
curl -i -X PUT "$API_BASE$API_PREFIX/documents/revisions/$REV_ID" \
  -H "Content-Type: application/json" \
  -d "{\"transmital_current_revision\":\"TR-TEST-$TS\"}"

# TS-REV-004
curl -i -X PUT "$API_BASE$API_PREFIX/documents/revisions/$REV_ID" -H "Content-Type: application/json" -d "{}"

# TS-REV-005
curl -i -X PUT "$API_BASE$API_PREFIX/documents/revisions/999999" \
  -H "Content-Type: application/json" \
  -d '{"transmital_current_revision":"TR-MISSING"}'

# TS-REV-006
REV_STATUS_ID=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0].rev_status_id')
curl -i -X PUT "$API_BASE$API_PREFIX/documents/revisions/$REV_ID" \
  -H "Content-Type: application/json" \
  -d "{\"rev_status_id\":$REV_STATUS_ID}"
```

## 4. TS-REV-007..010 Create Checks

```bash
BASE_REV=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0]')

CREATE_PAYLOAD=$(cat <<JSON
{
  "rev_code_id": $(echo "$BASE_REV" | jq -r '.rev_code_id'),
  "rev_author_id": $(echo "$BASE_REV" | jq -r '.rev_author_id'),
  "rev_originator_id": $(echo "$BASE_REV" | jq -r '.rev_originator_id'),
  "rev_modifier_id": $(echo "$BASE_REV" | jq -r '.rev_modifier_id'),
  "transmital_current_revision": "TR-NEW-$TS",
  "planned_start_date": "$(echo "$BASE_REV" | jq -r '.planned_start_date')",
  "planned_finish_date": "$(echo "$BASE_REV" | jq -r '.planned_finish_date')"
}
JSON
)

# TS-REV-007
curl -i -X POST "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" -H "Content-Type: application/json" -d "$CREATE_PAYLOAD"

# TS-REV-008
curl -i -X POST "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" \
  -H "Content-Type: application/json" \
  -d "$(echo "$CREATE_PAYLOAD" | jq '. + {rev_status_id: 1}')"

# TS-REV-009
curl -i -X POST "$API_BASE$API_PREFIX/documents/999999/revisions" -H "Content-Type: application/json" -d "$CREATE_PAYLOAD"

# TS-REV-010
curl -i -X POST "$API_BASE$API_PREFIX/documents/1/revisions" -H "Content-Type: application/json" -d "{}"
```

## 5. TS-REV-011..015 Status Transition Checks

```bash
# TS-REV-011 forward transition (requires eligible revision)
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/status-transitions" \
  -H "Content-Type: application/json" \
  -d '{"direction":"forward"}'

# TS-REV-012 back transition (requires revertible non-start revision)
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/status-transitions" \
  -H "Content-Type: application/json" \
  -d '{"direction":"back"}'

# TS-REV-013 invalid direction
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/status-transitions" \
  -H "Content-Type: application/json" \
  -d '{"direction":"sideways"}'
```

`TS-REV-014` and `TS-REV-015` require selecting revisions currently in final or non-revertible statuses.

## Edge Cases
- Transition checks are data-dependent; pick suitable revisions from current seed state.
- Forward transition may require a file attachment on revision depending on status rules.

## Scenario Catalog
- `TS-REV-001` list revisions for existing document.
- `TS-REV-002` list revisions for missing document returns `404`.
- `TS-REV-003` update non-final revision metadata succeeds.
- `TS-REV-004` empty update payload returns `400`.
- `TS-REV-005` update missing revision returns `404`.
- `TS-REV-006` update with `rev_status_id` is rejected (`422`).
- `TS-REV-007` create revision succeeds.
- `TS-REV-008` create revision with explicit status is rejected (`422`).
- `TS-REV-009` create revision for missing doc returns `404`.
- `TS-REV-010` create revision missing required fields returns `422`.
- `TS-REV-011` forward status transition succeeds when eligible.
- `TS-REV-012` back status transition succeeds when eligible.
- `TS-REV-013` invalid direction returns `422`.
- `TS-REV-014` forward transition from final state returns `409`.
- `TS-REV-015` back transition from non-revertible state returns `409`.
- `TS-REV-016` revisions router denies requests when effective session identity is missing.

## Automated Test Mapping
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_list` -> `TS-REV-001`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_missing_doc` -> `TS-REV-002`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update` -> `TS-REV-003`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update_missing_fields` -> `TS-REV-004`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update_missing_revision` -> `TS-REV-005`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update_rejects_status_change` -> `TS-REV-006`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_create` -> `TS-REV-007`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_create_rejects_rev_status_id` -> `TS-REV-008`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_create_missing_doc` -> `TS-REV-009`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_create_missing_required_fields` -> `TS-REV-010`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_forward` -> `TS-REV-011`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_back` -> `TS-REV-012`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_invalid_direction` -> `TS-REV-013`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_already_final` -> `TS-REV-014`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_not_revertible` -> `TS-REV-015`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_require_session_identity` -> `TS-REV-016`

## References
- `tests/api/api/test_documents_revisions_endpoints.py`
- `api/routers/documents_revisions.py`
