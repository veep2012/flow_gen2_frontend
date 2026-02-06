# Distribution List Feature Implementation

## Document Control
- Status: Review
- Owner: Backend and Frontend Team
- Reviewers: API and UI maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-06
- Version: v1.2

## Purpose
Describe the implemented backend/frontend wiring for distribution-list retrieval and send-for-review behavior.

## Scope
- In scope:
  - Active API endpoints in `api/routers/distribution_lists.py`.
  - UI integration in IDC behavior and DistributionList component.
  - Current validation and response behavior.
- Out of scope:
  - Historical in-memory prototypes.
  - Future database redesign proposals.

## Design / Behavior
Distribution list operations are project-scoped through the target document. Backend validates document, project, and list ownership before returning lists/recipients or accepting send-for-review.

## Backend
### Router
- File: `api/routers/distribution_lists.py`
- Prefix: `/api/v1/documents`
- Implemented endpoints:
  - `GET /{doc_id}/distribution-lists`
  - `GET /{doc_id}/distribution-lists/{list_id}/recipients`
  - `POST /{doc_id}/distribution-lists/{list_id}/send-for-review`

### Validation
- Document must exist.
- Document must be linked to a project.
- Distribution list must belong to the same project.
- Send-for-review requires non-empty recipients and all recipients must belong to the list.

## Frontend
### Components
- `ui/src/components/DistributionList/DistributionList.jsx`
- `ui/src/components/DocRevStatusBehaviors/IDCBehavior.jsx`

### Behavior
- Loads lists and recipient data from API.
- Triggers send-for-review from selected list.
- Displays API-side error detail where available.

## Known Gap
- Backend expects `SendForReviewRequest.recipients`.
- Current UI send action may submit an empty JSON body.
- This contract mismatch should be resolved in code so docs and behavior stay aligned.

## Compatibility
- Frontend: React 18+
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL

## Edge Cases
- Empty list returned for valid document/project.
- Selected list deleted or no longer project-scoped.
- Recipient membership changed between list fetch and send action.

## References
- `documentation/distribution_list_feature.md`
- `api/routers/distribution_lists.py`
- `api/schemas/distribution_lists.py`
- `ui/src/components/DistributionList/DistributionList.jsx`
