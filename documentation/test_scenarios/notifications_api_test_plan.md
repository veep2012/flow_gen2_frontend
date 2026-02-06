# Notifications API Test Plan (Curl, Port 5556)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-06
- Version: v1.1

## Purpose
Provide a repeatable manual curl-based validation flow for notification lifecycle APIs.

## Scope
- In scope:
  - API-level create/list/read/replace/delete flow checks.
  - Seed-data-driven ID resolution.
- Out of scope:
  - UI notification behavior.
  - Load/performance testing.

## Design / Behavior
This scenario validates end-to-end behavior of notification APIs against seeded PostgreSQL data.

This plan runs against the seeded PostgreSQL state and verifies notification lifecycle behavior:
`create -> read -> replace(drop+new) -> delete(drop+new)`.

Assumption: DB is already up and API is reachable on port `5556`.

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:5556
export API_PREFIX=/api/v1
```

## 2. Resolve Real IDs From Seeded Data

Get current user and recipient from real seeded users:

```bash
USERS_JSON=$(curl -s "$API_BASE$API_PREFIX/people/users")
echo "$USERS_JSON" | jq

CURRENT_USER_ID=$(curl -s "$API_BASE$API_PREFIX/people/users/current_user" | jq -r '.user_id')
RECIPIENT_ID=$(echo "$USERS_JSON" | jq -r --arg cid "$CURRENT_USER_ID" '.[] | select((.user_id|tostring)!=$cid) | .user_id' | head -n1)

echo "CURRENT_USER_ID=$CURRENT_USER_ID RECIPIENT_ID=$RECIPIENT_ID"
```

Find a project with documents and resolve one `doc_id` + `rev_id`:

```bash
for pid in $(seq 1 10); do
  DOCS=$(curl -s "$API_BASE$API_PREFIX/documents?project_id=$pid")
  CNT=$(echo "$DOCS" | jq 'length')
  if [ "$CNT" -gt 0 ]; then
    PROJECT_ID=$pid
    DOC_ID=$(echo "$DOCS" | jq -r '.[0].doc_id')
    break
  fi
done

REVISIONS=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions")
REV_ID=$(echo "$REVISIONS" | jq -r '.[0].rev_id')

echo "PROJECT_ID=$PROJECT_ID DOC_ID=$DOC_ID REV_ID=$REV_ID"
```

Baseline inbox snapshot:

```bash
BASELINE=$(curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$RECIPIENT_ID")
BASELINE_COUNT=$(echo "$BASELINE" | jq 'length')
echo "BASELINE_COUNT=$BASELINE_COUNT"
```

## 3. Create Notification

```bash
CREATE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $CURRENT_USER_ID" \
  -d "{
    \"title\": \"API test notification\",
    \"body\": \"Please review revision $REV_ID\",
    \"rev_id\": $REV_ID,
    \"recipient_user_ids\": [$RECIPIENT_ID],
    \"recipient_dist_ids\": []
  }")

echo "$CREATE_RESP" | jq
CREATED_ID=$(echo "$CREATE_RESP" | jq -r '.notification_id')
```

Verify recipient got unread `regular` event:

```bash
curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$RECIPIENT_ID&unread_only=true" | jq \
  --argjson id "$CREATED_ID" \
  '.[] | select(.notification_id==$id) | {notification_id,event_type,read_at,rev_id,sender_user_id}'
```

## Edge Cases
- Empty recipient set should fail create/send validation.
- Replace/delete as non-sender should return authorization failure.
- Date-range filter with invalid order should return `400`.

## References
- `api/routers/notifications.py`
- `api/schemas/notifications.py`
- `documentation/notifications_and_dls.md`

## 4. Mark Read

```bash
READ_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications/$CREATED_ID/read" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $RECIPIENT_ID" \
  -d "{}")

echo "$READ_RESP" | jq
```

Verify `read_at` is set:

```bash
curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$RECIPIENT_ID" | jq \
  --argjson id "$CREATED_ID" \
  '.[] | select(.notification_id==$id) | {notification_id,read_at}'
```

## 5. Replace Notification (Drop Old + New Changed Notice)

```bash
REPLACE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications/$CREATED_ID/replace" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $CURRENT_USER_ID" \
  -d "{
    \"title\": \"API test notification (changed)\",
    \"body\": \"Updated content for revision $REV_ID\",
    \"remark\": \"changed during API test\"
  }")

echo "$REPLACE_RESP" | jq
CHANGED_ID=$(echo "$REPLACE_RESP" | jq -r '.notification_id')
```

Verify chain state:
- original notification has `dropped_at` and `superseded_by_notification_id = CHANGED_ID`
- new notification has `event_type = changed_notice` and unread `read_at = null`

```bash
curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$RECIPIENT_ID" | jq \
  --argjson old "$CREATED_ID" --argjson new "$CHANGED_ID" \
  '[.[] | select(.notification_id==$old or .notification_id==$new) |
    {notification_id,event_type,read_at,dropped_at,superseded_by_notification_id}]'
```

## 6. Delete Notification (Drop Changed + New Dropped Notice)

```bash
DELETE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications/$CHANGED_ID/delete" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $CURRENT_USER_ID" \
  -d "{\"remark\":\"removed during API test\"}")

echo "$DELETE_RESP" | jq
DROPPED_NOTICE_ID=$(echo "$DELETE_RESP" | jq -r '.notification_id')
```

Verify final chain and unread dropped notice:

```bash
curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$RECIPIENT_ID" | jq \
  --argjson old "$CHANGED_ID" --argjson notice "$DROPPED_NOTICE_ID" \
  '[.[] | select(.notification_id==$old or .notification_id==$notice) |
    {notification_id,event_type,read_at,dropped_at,superseded_by_notification_id,remark}]'
```

## 7. Negative Checks

Make sure required vars are present:

```bash
echo "CURRENT_USER_ID=$CURRENT_USER_ID RECIPIENT_ID=$RECIPIENT_ID REV_ID=$REV_ID"
```

Create a fresh notification for negative tests:

```bash
NEG_CREATE=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $CURRENT_USER_ID" \
  -d "{
    \"title\":\"Negative checks notification\",
    \"body\":\"Negative checks body\",
    \"rev_id\":$REV_ID,
    \"recipient_user_ids\":[$RECIPIENT_ID],
    \"recipient_dist_ids\":[]
  }")

echo "$NEG_CREATE" | jq
NEG_ID=$(echo "$NEG_CREATE" | jq -r '.notification_id')
echo "NEG_ID=$NEG_ID"
```

Unauthorized replace by non-sender/non-superuser should be `403`:

```bash
curl -i -X POST "$API_BASE$API_PREFIX/notifications/$NEG_ID/replace" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $RECIPIENT_ID" \
  -d '{"title":"forbidden","body":"forbidden"}'
```

Mark read with user that has no delivery row should be `404`:

```bash
curl -i -X POST "$API_BASE$API_PREFIX/notifications/$NEG_ID/read" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $CURRENT_USER_ID" \
  -d "{}"
```

## 8. Done

You can rerun sections 3-7 as many times as needed; each run creates its own notification chain.
