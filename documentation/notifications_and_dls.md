**Notifications And Distribution Lists**

**Purpose**
Define how users exchange information through notifications and distribution lists in Flow, with clear read/unread tracking and delivery rules.

**Why It Is Needed**
- The system is multi-user and requires information exchange.
- Users must be able to send messages directly or via distribution lists.
- Delivered notifications must be marked as unread.
- Reading a notification must mark it as read.

**Scope**
- User-visible notifications.
- Distribution lists and recipients.
- Read and unread state tracking.
- Delivery behavior and basic lifecycle.

**Out Of Scope**
- Real-time delivery transport details.
- Email or external push integrations.
- Full permissions model for all features.

**Core Concepts**
- **Notification**: A message created by a user or system event and delivered to one or more users.
- **Notification Linkage**: Each notification should link to a revision and optionally to a commented file
  for fast UI navigation.
- **Recipient**: A user who receives a notification.
- **Distribution List (DL)**: A named list of recipients.
- **Read State**: Per-recipient flag indicating whether the notification has been read.

**Primary Use Cases**
- User-to-user message.
- User-to-DL broadcast.
- System-to-user event notification.
- Review workflows for document revisions in intermediate statuses.

**Document Flow Integration**
- Intermediate revision statuses require review by multiple users.
- Users can leave comments that are either text or file-based (see `files_commented` table).
- All comments must be saved in the database (no hard deletes).
- Comment notifications must be delivered to recipients via direct users or DLs.
- DLs may be predefined and also adjusted by the current user.

```mermaid
sequenceDiagram
    participant User as Reviewer
    participant UI as Flow UI
    participant API as API
    participant DB as DB
    participant DL as Distribution Lists
    participant Rec as Recipients

    User->>UI: Add comment (text or file) on revision
    UI->>API: Create comment (rev_id, optional file)
    API->>DB: Insert comment (text / files_commented)
    DB-->>API: Comment saved
    API->>DL: Resolve recipients (direct + DLs)
    DL-->>API: Recipient user IDs
    API->>DB: Create notification (rev_id, commented_file_id?)
    API->>DB: Create per-recipient deliveries (unread)
    DB-->>API: Delivered
    API-->>UI: Comment created + notification count
    Rec->>UI: Open notification
    UI->>API: Mark as read
    API->>DB: Update recipient read state
    DB-->>API: Read state updated
    API-->>UI: Read confirmed
```

**User And Recipient Model**
- A recipient is a user ID.
- Notification delivery is stored per recipient.
- Read state is tracked per recipient, not globally.

**Distribution Lists**
- A DL is a named collection of recipients.
- A notification can target one or more DLs.
- Recipients are resolved at send time.
- Duplicate recipients are deduplicated per notification.

**Notification Lifecycle**
1. Create a notification with sender, content, and targets.
2. Resolve recipients from direct targets and DLs.
3. Persist per-recipient delivery rows with `unread` state.
4. Users fetch their notifications with read and unread filters.
5. User marks a notification as read, changing only their delivery row.
6. Sender or superuser can replace a notification when content must be changed.
7. Replace flow: original notification is marked as dropped, then a new notification is created and linked to the original with a remark that it was changed.
8. Sender or superuser can delete a notification.
9. Delete flow: original notification is marked as dropped, then recipients receive a new notification that the previous one was dropped.

**Read And Unread Rules**
- New deliveries default to `unread`.
- Marking read is idempotent.
- Read state is per user and does not affect other recipients.
- Replacement and deletion notices are new notifications and must be delivered as `unread`.
- All notifications must be retained in the database (no hard deletes).

**Delivery Rules**
- A user must exist to receive a notification.
- If a DL contains invalid users, those entries are skipped and logged.
- If a notification targets both a user and a DL containing that user, the user receives one delivery record.
- For each notification target row, **exactly one** of `recipient_user_id` or `recipient_dist_id` is set.
- API must deduplicate recipients across direct user IDs and DL membership.
- Replacement/delete notices must be sent to the original recipient set.

**Data Model Sketch**
- `notifications`
  - `notification_id`
  - `sender_user_id`
  - `event_type` (`regular`, `changed_notice`, `dropped_notice`)
  - `title`
  - `body`
  - `remark` (optional system/user remark, e.g. "changed")
  - `rev_id` (required link to revision)
  - `commented_file_id` (optional link to commented file)
  - `recipient_user_id` (direct recipient, mutually exclusive with `recipient_dist_id`)
  - `recipient_dist_id` (DL recipient, mutually exclusive with `recipient_user_id`)
  - `created_at`
  - `dropped_at` (nullable)
  - `dropped_by_user_id` (nullable)
  - `superseded_by_notification_id` (nullable)
- `notification_recipients`
  - `notification_id`
  - `recipient_user_id`
  - `read_at` or `is_read`
  - `delivered_at`
- `distribution_list`
  - `dist_id`
  - `distribution_list_name`
  - `project_id`
- `distribution_list_content`
  - `dist_id`
  - `person_id` or `user_id`

**API Surface Sketch**
- Create notification:
  - Inputs: sender, title, body, direct user IDs, DL IDs.
  - Output: notification ID and recipient count.
- Replace notification:
  - Allowed for sender or superuser.
  - Behavior: mark original as dropped and create a new linked notification with change remark.
  - Output: new notification ID and recipient count.
- Delete notification:
  - Allowed for sender or superuser.
  - Behavior: mark original as dropped and create a new linked drop notice for recipients.
  - Output: drop notice notification ID and recipient count.
- List notifications for user:
  - Filters: unread only, date range, sender.
- Mark notification read:
  - Input: notification ID.
  - Output: read state.
- List DLs and members:
  - Read-only via API if DLs are managed via seed/admin workflow.

**Behavioral Expectations**
- API should not enforce workflow rules beyond request shape and basic authorization.
- DB should enforce recipient uniqueness and write consistency.
- All updates should be transactional per notification creation.

**Sync Now, Async Later**
- Current implementation can remain synchronous inside the API for simplicity.
- Design should keep notification creation and delivery in a single service path so it can be
  swapped to an async worker later without changing API behavior.
- Future async extension can enqueue delivery jobs and resolve recipients out of band.

**Open Questions**
- Should DL membership be scoped per project or global.
