# Notifications and Distribution Lists

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-06
- Version: v1.2

## Purpose
Document the single Notifications + Distribution Lists module:
- notification lifecycle and inbox semantics
- distribution list recipient source model
- current API/DB behavior and legacy removals

## Scope
- In scope:
  - Notification create/list/replace/drop/read API behavior.
  - Recipient resolution from direct users and distribution lists (DL).
  - Per-recipient unread/read delivery semantics.
  - DL data model usage in notification delivery.
  - Current backend status of legacy DL endpoints.
- Out of scope:
  - Real-time push transport.
  - External email or mobile push delivery.

## Design / Behavior
Notifications are created through workflow functions, recipients are resolved and deduplicated server-side, and each recipient gets an inbox delivery row with independent read state.

Distribution lists are used as recipient sources only. At send time, DL membership is expanded to users and merged with direct user targets.

## Implemented API Surface
Router: `api/routers/notifications.py` (`/api/v1/notifications`)

- `POST /api/v1/notifications`
  - Creates a `regular` notification and delivery rows.
- `GET /api/v1/notifications`
  - Lists recipient inbox rows with filters (`unread_only`, sender, date range).
- `POST /api/v1/notifications/{notification_id}/replace`
  - Drops original notification and creates linked `changed_notice`.
- `POST /api/v1/notifications/{notification_id}/delete`
  - Drops original notification and creates linked `dropped_notice`.
- `POST /api/v1/notifications/{notification_id}/read`
  - Marks current recipient delivery row as read (idempotent).

## Distribution List Integration
- DL source tables:
  - `ref.distribution_list`
  - `ref.distribution_list_content`
- Notification target and recipient tables:
  - `core.notification_targets`
  - `core.notification_recipients`
- Resolution behavior:
  - direct user IDs + DL IDs are accepted as targets
  - DL members are resolved directly via `distribution_list_content.user_id`
  - final recipient set is deduplicated before inbox delivery rows are created

## Distribution Lists API and Legacy Removal
- Active DL API is implemented and exposed under `/api/v1/distribution-lists/*`:
  - Router: `api/routers/distribution_lists.py`
  - Schemas: `api/schemas/distribution_lists.py`
  - Endpoints: list/create/delete list, list/add/remove members
- Only legacy document-scoped endpoints were removed:
  - `/api/v1/documents/{doc_id}/distribution-lists/*`
- DL functionality remains part of this module both as standalone DL management API and as notification recipient targeting.

## Recipient Resolution Rules
- Notification targets can include direct user IDs and distribution list IDs.
- Backend resolves distribution list members at send time.
- Recipients are deduplicated across all targets.
- If no valid recipient can be resolved, API returns `400`.

## Authorization and Actor Rules
- `replace` and `delete` require current actor (`X-User-Id`) and allow only sender or superuser.
- `read` uses current actor (`X-User-Id`) as recipient identity.
- `create` and `list` can resolve actor from body/query or fallback to current actor header.

## Data and Event Model
- Event types:
  - `regular`
  - `changed_notice`
  - `dropped_notice`
- Notification links:
  - `rev_id` is required.
  - `commented_file_id` is optional and validated against revision relation.
- Drop/replace linkage:
  - Original notifications are marked dropped.
  - New notification links back through `superseded_by_notification_id` semantics.

## Operational Notes
- Workflow functions are transaction boundaries for notification actions.
- Read state is per-recipient and never global.
- Inbox listing order is newest-first by delivery timestamp and notification ID.

## Edge Cases
- `date_from > date_to` in list query returns `400`.
- Attempting to replace/drop an already dropped notification returns `400`.
- Non-sender/non-superuser actor on replace/drop returns `403`.
- Mark-read for missing delivery row returns `404`.

## References
- `documentation/api_interfaces.md`
- `api/routers/notifications.py`
- `api/schemas/notifications.py`
- `api/routers/distribution_lists.py`
- `api/schemas/distribution_lists.py`
- `documentation/test_scenarios/notifications_api_test_plan.md`
