# Notifications + DL API Test Plan (Curl, Port 5556)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-06
- Version: v1.2

## Purpose
Provide a repeatable manual curl-based validation flow for:
- Distribution List APIs
- Notification lifecycle APIs
- Notification delivery through Distribution Lists

Assumption: DB is already up and API is reachable on port `5556`.

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:5556
export API_PREFIX=/api/v1
```

## 2. Resolve Seed IDs

```bash
USERS_JSON=$(curl -s "$API_BASE$API_PREFIX/people/users")
echo "$USERS_JSON" | jq

CURRENT_USER_ID=$(curl -s "$API_BASE$API_PREFIX/people/users/current_user" | jq -r '.user_id')
MEMBER_USER_ID=$(echo "$USERS_JSON" | jq -r --arg cid "$CURRENT_USER_ID" '.[] | select((.user_id|tostring)!=$cid) | .user_id' | head -n1)

for pid in $(seq 1 10); do
  DOCS=$(curl -s "$API_BASE$API_PREFIX/documents?project_id=$pid")
  CNT=$(echo "$DOCS" | jq 'length')
  if [ "$CNT" -gt 0 ]; then
    DOC_ID=$(echo "$DOCS" | jq -r '.[0].doc_id')
    break
  fi
done

REVISIONS=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions")
REV_ID=$(echo "$REVISIONS" | jq -r '.[0].rev_id')

echo "CURRENT_USER_ID=$CURRENT_USER_ID MEMBER_USER_ID=$MEMBER_USER_ID DOC_ID=$DOC_ID REV_ID=$REV_ID"
```

## 3. Distribution List API Checks

Create DL:

```bash
TS=$(date +%s)
DL_CREATE=$(curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists" \
  -H "Content-Type: application/json" \
  -d "{\"distribution_list_name\":\"API DL $TS\"}")
echo "$DL_CREATE" | jq
DIST_ID=$(echo "$DL_CREATE" | jq -r '.dist_id')
```

List DLs:

```bash
curl -s "$API_BASE$API_PREFIX/distribution-lists" | jq --argjson id "$DIST_ID" \
  '.[] | select(.dist_id==$id)'
```

Add member:

```bash
DL_MEMBER_ADD=$(curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$MEMBER_USER_ID}")
echo "$DL_MEMBER_ADD" | jq
```

List members:

```bash
curl -s "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members" | jq
```

## 4. Create Notification Targeting DL

```bash
CREATE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $CURRENT_USER_ID" \
  -d "{
    \"title\": \"API test notification via DL\",
    \"body\": \"Please review revision $REV_ID\",
    \"rev_id\": $REV_ID,
    \"recipient_user_ids\": [],
    \"recipient_dist_ids\": [$DIST_ID]
  }")

echo "$CREATE_RESP" | jq
CREATED_ID=$(echo "$CREATE_RESP" | jq -r '.notification_id')
```

Verify DL member got unread notification:

```bash
curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$MEMBER_USER_ID&unread_only=true" | jq \
  --argjson id "$CREATED_ID" \
  '.[] | select(.notification_id==$id) | {notification_id,event_type,read_at,sender_user_id,rev_id}'
```

## 5. Mark Read

```bash
READ_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications/$CREATED_ID/read" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $MEMBER_USER_ID" \
  -d "{}")
echo "$READ_RESP" | jq
```

## 6. Replace Notification (Drop + Changed Notice)

```bash
REPLACE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications/$CREATED_ID/replace" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $CURRENT_USER_ID" \
  -d "{
    \"title\": \"API test notification via DL (changed)\",
    \"body\": \"Updated content for revision $REV_ID\",
    \"remark\": \"changed during API test\"
  }")
echo "$REPLACE_RESP" | jq
CHANGED_ID=$(echo "$REPLACE_RESP" | jq -r '.notification_id')
```

## 7. Delete Notification (Drop + Dropped Notice)

```bash
DELETE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications/$CHANGED_ID/delete" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $CURRENT_USER_ID" \
  -d "{\"remark\":\"removed during API test\"}")
echo "$DELETE_RESP" | jq
DROPPED_NOTICE_ID=$(echo "$DELETE_RESP" | jq -r '.notification_id')
```

Verify chain:

```bash
curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$MEMBER_USER_ID" | jq \
  --argjson a "$CREATED_ID" --argjson b "$CHANGED_ID" --argjson c "$DROPPED_NOTICE_ID" \
  '[.[] | select(.notification_id==$a or .notification_id==$b or .notification_id==$c) |
    {notification_id,event_type,read_at,dropped_at,superseded_by_notification_id}]'
```

## 8. DL Negative Checks

Duplicate member add should be `400`:

```bash
curl -i -X POST "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$MEMBER_USER_ID}"
```

Remove missing member should be `404`:

```bash
curl -i -X DELETE "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members/9999"
```

## 9. Cleanup

Remove member:

```bash
curl -s -X DELETE "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members/$MEMBER_USER_ID" | jq
```

Delete DL:

```bash
curl -i -X DELETE "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID"
```

Expected result here: `409`, because this DL was used in notification targets and is protected from deletion.

If you want to validate successful delete (`200`) as well, create a fresh unused DL and delete it:

```bash
TMP_DL=$(curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists" \
  -H "Content-Type: application/json" \
  -d "{\"distribution_list_name\":\"TMP DELETE $(date +%s)\"}")
TMP_DIST_ID=$(echo "$TMP_DL" | jq -r '.dist_id')
curl -s -X DELETE "$API_BASE$API_PREFIX/distribution-lists/$TMP_DIST_ID" | jq
```

## References
- `api/routers/notifications.py`
- `api/schemas/notifications.py`
- `api/routers/distribution_lists.py`
- `api/schemas/distribution_lists.py`
- `documentation/notifications_and_dls.md`
