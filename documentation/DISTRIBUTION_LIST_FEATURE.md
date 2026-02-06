# Distribution List Feature

## Document Control
- Status: Review
- Owner: Backend and Frontend Team
- Reviewers: API and UI maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-06
- Version: v1.2

## Purpose
Describe current user-visible distribution list behavior in the Document Flow IDC tab.

## Scope
- In scope:
  - Distribution list browsing in IDC.
  - Recipient viewing for selected lists.
  - Send-for-review user action.
- Out of scope:
  - Distribution list CRUD administration policy.
  - External email delivery implementation.

## Design / Behavior
The feature is integrated in the IDC tab and relies on distribution-list endpoints under `/api/v1/documents/{doc_id}/distribution-lists/*`.

## Overview
Users open the IDC section of a document, choose a distribution list, review recipients, and trigger send-for-review.

## Location
1. Open a document in Document Flow.
2. Open the `IDC` step.
3. Select the `Distribution list` subtab.

## API Contract Used by UI
- `GET /api/v1/documents/{doc_id}/distribution-lists`
  - Returns distribution lists for the document project.
- `GET /api/v1/documents/{doc_id}/distribution-lists/{list_id}/recipients`
  - Returns recipients in the selected list.
- `POST /api/v1/documents/{doc_id}/distribution-lists/{list_id}/send-for-review`
  - Sends document for review using validated recipients.

## User Flow
1. Select a list.
2. Verify recipients loaded for that list.
3. Trigger send-for-review.
4. Show success or API error message.

## Error Handling
- API errors are surfaced to the user.
- Loading state prevents repeated submissions.
- Missing/invalid recipient sets result in backend validation errors.

## Testing
- Verify list and recipient retrieval for valid `doc_id`.
- Verify `404` handling for invalid document or list.
- Verify send-for-review success path and failure path.
- Verify no duplicate send action while request is in progress.

## Edge Cases
- Document has no distribution lists.
- Distribution list has zero recipients.
- UI payload and backend validation expectations diverge.

## References
- `documentation/distribution_list_implementation.md`
- `api/routers/distribution_lists.py`
- `api/schemas/distribution_lists.py`
- `ui/src/components/DistributionList/DistributionList.jsx`
