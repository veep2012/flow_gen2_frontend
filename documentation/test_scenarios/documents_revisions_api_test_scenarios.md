# Documents Revisions API Test Plan (Curl, Port 4175)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-07
- Last Updated: 2026-03-25
- Version: v2.2

## Change Log
- 2026-03-25 | v2.2 | Removed the redundant public generic revision-create endpoint from the scenario contract, clarified that supersede replaces the current non-final revision with the same `rev_code_id` while restarting at the workflow start status, and synchronized automated coverage with the supported progression paths.
- 2026-03-25 | v1.7 | Added the missing automated mapping for the final-current-revision create rejection scenario and aligned the scenario catalog numbering with the current revisions test suite.
- 2026-03-25 | v1.6 | Added dedicated overview-transition scenarios for current final revisions, changed generic revision-update scenarios so `rev_code_id` is rejected after creation, added document-create default/explicit initial revision-code scenarios, and clarified that canceled revisions disappear from standard revision lists.
- 2026-03-20 | v1.5 | Clarified current revision-code update behavior: there is no dedicated overview-transition endpoint, and the generic revision update workflow may still mutate `doc_revision.rev_code_id` while `ref.revision_overview` remains reference data; also defined `back` transition semantics explicitly as immediate-predecessor rollback via the unique status whose `next_rev_status_id` points to the current status, and added invariant coverage for ambiguous predecessor rejection.
- 2026-03-04 | v1.3 | Added fail-closed session-identity scenario for revisions router reads.
- 2026-02-20 | v1.2 | Added Change Log section for standards compliance

## Purpose
Provide repeatable curl-based validation for revisions list/update, supersede, overview transitions, and status transitions.

## Scope
- In scope:
  - list and missing-document behavior
  - update validations
  - supersede behavior
  - dedicated overview-transition behavior
  - status transition forward/back paths
- Out of scope:
  - document delete/cancel behavior

## Design / Behavior
Revision APIs must enforce required fields, status immutability on update, and workflow transition constraints.
- `POST /api/v1/documents/revisions/{rev_id}/overview-transition` creates the next revision from a current final revision.
- `POST /api/v1/documents/revisions/{rev_id}/supersede` creates a replacement revision with the same `rev_code_id` for the current non-final revision and restarts that replacement at the workflow start status.
- The generic revision update workflow must reject `rev_code_id` changes after revision creation.
- There is no public generic revision-create endpoint for follow-up document revisions.
- A superseded revision must no longer block reuse of its `rev_code_id`.
- Document creation defaults the initial `rev_code_id` to the unique `revision_overview.start=true` step when omitted.

Backward transition contract:
- `direction="back"` means move the revision to the immediate predecessor status only.
- The predecessor is discovered by reverse lookup on `ref.doc_rev_statuses.next_rev_status_id`.
- The predecessor must be unique; ambiguous predecessor graphs are invalid repository state.
- The start status cannot transition back.
- A non-start status can transition back only when its current status has `revertible=true`.
- If no predecessor exists for a non-start revertible status, the transition must fail.

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

# TS-REV-019
REV_CODE_ID=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0].rev_code_id')
curl -i -X PUT "$API_BASE$API_PREFIX/documents/revisions/$REV_ID" \
  -H "Content-Type: application/json" \
  -d "{\"rev_code_id\":$REV_CODE_ID}"
```

## 4. TS-REV-011..018 Status Transition Checks

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

`TS-REV-017` is a privileged invariant test rather than a public HTTP scenario: attempt to create an ambiguous predecessor configuration in `ref.doc_rev_statuses` where two rows point to the same successor. The database must reject that state.

`TS-REV-018` requires selecting a revision currently in the unique `start=true` status.

## 5. TS-REV-020..027 Overview Transition, Supersede, and Document Create Checks

```bash
# TS-REV-020 overview transition from current final revision
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/overview-transition" \
  -H "Content-Type: application/json" \
  -d '{}'

# TS-REV-021 overview transition from non-final revision
curl -i -X POST "$API_BASE$API_PREFIX/documents/revisions/$REV_ID/overview-transition" \
  -H "Content-Type: application/json" \
  -d '{}'

# TS-REV-022 create document without rev_code_id (backend must default start step)
curl -i -X POST "$API_BASE$API_PREFIX/documents" \
  -H "Content-Type: application/json" \
  -d '{ "doc_name_unique": "DOC-TS-REV-022", "title": "TS REV 022", "type_id": 1, "area_id": 1, "unit_id": 1, "rev_author_id": 1, "rev_originator_id": 1, "rev_modifier_id": 1, "transmital_current_revision": "TR-TS-REV-022", "planned_start_date": "2024-01-01T00:00:00Z", "planned_finish_date": "2024-12-31T23:59:59Z" }'
```

`TS-REV-023` requires creating a brand new document with an explicit non-start `rev_code_id` that is permitted by current business rules.

`TS-REV-024` requires canceling a non-final revision and confirming it no longer appears in standard revision-list responses.

`TS-REV-026` requires superseding the current non-final revision through the dedicated supersede endpoint and verifying the replacement revision keeps the same `rev_code_id` while restarting at the workflow start status.

`TS-REV-027` requires attempting to supersede a current final revision and confirming the API rejects it in favor of the overview-transition workflow.

## Edge Cases
- Transition checks are data-dependent; pick suitable revisions from current seed state.
- Forward transition may require a file attachment on revision depending on status rules.

## Scenario Catalog
- `TS-REV-001` list revisions for existing document.
- `TS-REV-002` list revisions for missing document returns `404`.
- `TS-REV-003` update non-final revision fields succeeds.
- `TS-REV-004` empty update payload returns `400`.
- `TS-REV-005` update missing revision returns `404`.
- `TS-REV-006` update with `rev_status_id` is rejected (`422`).
- `TS-REV-019` update with `rev_code_id` is rejected (`422`).
- `TS-REV-011` forward status transition succeeds when eligible.
- `TS-REV-012` back status transition succeeds when eligible.
  - The target status is the unique immediate predecessor whose `next_rev_status_id` points to the current status.
- `TS-REV-013` invalid direction returns `422`.
- `TS-REV-014` forward transition from final state returns `409`.
- `TS-REV-015` back transition from non-revertible state returns `409`.
- `TS-REV-017` ambiguous predecessor status graphs are rejected by database constraints.
- `TS-REV-018` back transition from the start status returns `409`.
- `TS-REV-016` revisions router denies requests when effective session identity is missing.
- `TS-REV-020` overview transition from a current final revision creates a new revision row.
- `TS-REV-021` overview transition from a non-final revision returns `409`.
- `TS-REV-022` document create without `rev_code_id` defaults to the `revision_overview.start` step.
- `TS-REV-023` document create with an explicit allowed non-start `rev_code_id` succeeds.
- `TS-REV-024` canceled revisions are excluded from standard revision-list responses.
- `TS-REV-026` supersede revision creates a replacement row with the same `rev_code_id`, resets it to the workflow start status, and marks the source revision as `superseded=true`.
- `TS-REV-027` supersede revision from a final source returns `409`.

## Automated Test Mapping
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_list` -> `TS-REV-001`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_missing_doc` -> `TS-REV-002`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update` -> `TS-REV-003`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update_missing_fields` -> `TS-REV-004`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update_missing_revision` -> `TS-REV-005`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update_rejects_status_change` -> `TS-REV-006`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_update_rejects_rev_code_change` -> `TS-REV-019`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_forward` -> `TS-REV-011`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_back` -> `TS-REV-012`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_invalid_direction` -> `TS-REV-013`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_already_final` -> `TS-REV-014`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_not_revertible` -> `TS-REV-015`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_graph_rejects_ambiguous_predecessor` -> `TS-REV-017`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_status_transition_already_start` -> `TS-REV-018`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_require_session_identity` -> `TS-REV-016`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_create_defaults_initial_revision_code_to_start` -> `TS-REV-022`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_overview_transition_from_final` -> `TS-REV-020`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_overview_transition_from_non_start_code` -> `TS-REV-023`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_overview_transition_rejects_non_final_source` -> `TS-REV-021`
- `tests/api/api/test_cancel_delete_endpoints.py::test_cancel_revision` -> `TS-REV-024`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_supersede` -> `TS-REV-026`
- `tests/api/api/test_documents_revisions_endpoints.py::test_documents_revisions_supersede_rejects_final_source` -> `TS-REV-027`

## References
- `tests/api/api/test_documents_revisions_endpoints.py`
- `api/routers/documents.py`
