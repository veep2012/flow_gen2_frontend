# Notifications + DL API Test Plan (Curl, Port 5556)

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-06
- Last Updated: 2026-02-07
- Version: v1.4

## Purpose
Provide a repeatable manual curl-based validation flow for:
- Distribution List APIs
- Notification lifecycle APIs
- Notification delivery through Distribution Lists

Assumption: DB is already up and API is reachable on port `5556`.

## Scenario Catalog (Automated Coverage Contract)

- `TS-DL-001` Distribution list CRUD + membership lifecycle must succeed (`201/200/404` sequence).
- `TS-DL-002` Duplicate distribution list name must be rejected (`400`).
- `TS-DL-003` Distribution list used in notifications must not be deletable (`409`).
- `TS-NTF-001` Notification create -> list unread -> mark read flow must succeed.
- `TS-NTF-002` Notification replace/delete chain must set dropped/superseded fields correctly.
- `TS-NTF-003` Replace by non-sender/non-superuser must be forbidden (`403`).
- `TS-NTF-004` Mark-read payload must reject `recipient_user_id` field (`422`).
- `TS-NTF-005` Superuser on-behalf create must persist `sender_user_id`.

Any change to these acceptance criteria must be reflected in:
- this scenario document
- `tests/api/api/test_distribution_lists_endpoints.py`
- `tests/api/api/test_notifications_endpoints.py`

## 1. Set Env Vars

```bash
export API_BASE=http://localhost:5556
export API_PREFIX=/api/v1
```

## 2. Resolve Seed IDs

```bash
USERS_JSON=$(curl -s "$API_BASE$API_PREFIX/people/users")
echo "$USERS_JSON" | jq

USER_A=$(echo "$USERS_JSON" | jq -r '.[0].user_id')
USER_B=$(echo "$USERS_JSON" | jq -r '.[1].user_id')
USER_C=$(echo "$USERS_JSON" | jq -r '.[2].user_id')
SUPERUSER_ID=2

for pid in $(seq 1 20); do
  DOCS=$(curl -s "$API_BASE$API_PREFIX/documents?project_id=$pid")
  CNT=$(echo "$DOCS" | jq 'length')
  if [ "$CNT" -gt 0 ]; then
    DOC_ID=$(echo "$DOCS" | jq -r '.[0].doc_id')
    break
  fi
done

REV_ID=$(curl -s "$API_BASE$API_PREFIX/documents/$DOC_ID/revisions" | jq -r '.[0].rev_id')
TS=$(date +%s)

echo "USER_A=$USER_A USER_B=$USER_B USER_C=$USER_C SUPERUSER_ID=$SUPERUSER_ID DOC_ID=$DOC_ID REV_ID=$REV_ID"
```

## 3. TS-DL-001 Distribution List CRUD + Membership Lifecycle

```bash
DL_CREATE=$(curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists" \
  -H "Content-Type: application/json" \
  -d "{\"distribution_list_name\":\"API DL $TS\"}")
echo "$DL_CREATE" | jq
DIST_ID=$(echo "$DL_CREATE" | jq -r '.dist_id')

curl -s "$API_BASE$API_PREFIX/distribution-lists" | jq --argjson id "$DIST_ID" '.[] | select(.dist_id==$id)'

curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER_B}" | jq

curl -s "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members" | jq

curl -s -X DELETE "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members/$USER_B" | jq
curl -s "$API_BASE$API_PREFIX/distribution-lists/$DIST_ID/members" | jq
```

Expected results:
- create member returns `201`
- remove member returns `200`
- listing members after remove no longer includes `USER_B`

## 4. TS-DL-002 Duplicate DL Name Rejected

```bash
DUP_NAME="API DL DUP $TS"
FIRST=$(curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists" \
  -H "Content-Type: application/json" \
  -d "{\"distribution_list_name\":\"$DUP_NAME\"}")
FIRST_ID=$(echo "$FIRST" | jq -r '.dist_id')

echo "First create:"; echo "$FIRST" | jq

echo "Duplicate create (expect 400):"
curl -i -X POST "$API_BASE$API_PREFIX/distribution-lists" \
  -H "Content-Type: application/json" \
  -d "{\"distribution_list_name\":\"$DUP_NAME\"}"

# cleanup duplicate test DL
curl -s -X DELETE "$API_BASE$API_PREFIX/distribution-lists/$FIRST_ID" | jq
```

## 5. TS-NTF-001 Notification Create -> Unread List -> Mark Read

```bash
CREATE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $SUPERUSER_ID" \
  -d "{
    \"title\": \"API test notification\",
    \"body\": \"Please review revision $REV_ID\",
    \"rev_id\": $REV_ID,
    \"recipient_user_ids\": [$USER_A],
    \"recipient_dist_ids\": []
  }")

echo "$CREATE_RESP" | jq
CREATED_ID=$(echo "$CREATE_RESP" | jq -r '.notification_id')

curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$USER_A&unread_only=true" | jq \
  --argjson id "$CREATED_ID" '.[] | select(.notification_id==$id) | {notification_id,event_type,read_at,sender_user_id}'

curl -s -X POST "$API_BASE$API_PREFIX/notifications/$CREATED_ID/read" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_A" \
  -d '{}' | jq
```

## 6. TS-NTF-002 Replace/Delete Chain Integrity

```bash
ORIG=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $SUPERUSER_ID" \
  -d "{
    \"title\": \"Chain original\",
    \"body\": \"Original body\",
    \"rev_id\": $REV_ID,
    \"recipient_user_ids\": [$USER_A],
    \"recipient_dist_ids\": []
  }")
ORIG_ID=$(echo "$ORIG" | jq -r '.notification_id')

REPLACE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications/$ORIG_ID/replace" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $SUPERUSER_ID" \
  -d '{"title":"Chain changed","body":"Changed body","remark":"changed"}')
CHANGED_ID=$(echo "$REPLACE_RESP" | jq -r '.notification_id')

echo "$REPLACE_RESP" | jq

DELETE_RESP=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications/$CHANGED_ID/delete" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $SUPERUSER_ID" \
  -d '{"remark":"dropped"}')
DROPPED_NOTICE_ID=$(echo "$DELETE_RESP" | jq -r '.notification_id')

echo "$DELETE_RESP" | jq

curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$USER_A" | jq \
  --argjson a "$ORIG_ID" --argjson b "$CHANGED_ID" --argjson c "$DROPPED_NOTICE_ID" \
  '[.[] | select(.notification_id==$a or .notification_id==$b or .notification_id==$c) | {notification_id,event_type,read_at,dropped_at,superseded_by_notification_id}]'
```

## 7. TS-NTF-003 Forbidden Replace for Non-Sender/Non-Superuser

```bash
SRC=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_A" \
  -d "{
    \"title\": \"Forbidden replace source\",
    \"body\": \"Sender is USER_A\",
    \"rev_id\": $REV_ID,
    \"recipient_user_ids\": [$USER_B],
    \"recipient_dist_ids\": []
  }")
SRC_ID=$(echo "$SRC" | jq -r '.notification_id')

# USER_C tries to replace USER_A notification: expect 403
curl -i -X POST "$API_BASE$API_PREFIX/notifications/$SRC_ID/replace" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_C" \
  -d '{"title":"Nope","body":"Nope"}'
```

## 8. TS-NTF-004 Mark Read Rejects recipient_user_id in Payload

```bash
SRC2=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $SUPERUSER_ID" \
  -d "{
    \"title\": \"Read validation\",
    \"body\": \"Read validation body\",
    \"rev_id\": $REV_ID,
    \"recipient_user_ids\": [$USER_A],
    \"recipient_dist_ids\": []
  }")
SRC2_ID=$(echo "$SRC2" | jq -r '.notification_id')

curl -i -X POST "$API_BASE$API_PREFIX/notifications/$SRC2_ID/read" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_A" \
  -d "{\"recipient_user_id\":$USER_A}"
```

## 9. TS-NTF-005 Superuser On-Behalf Sender

```bash
ON_BEHALF=$(curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $SUPERUSER_ID" \
  -d "{
    \"sender_user_id\": $USER_A,
    \"title\": \"On behalf create\",
    \"body\": \"Created by superuser for sender USER_A\",
    \"rev_id\": $REV_ID,
    \"recipient_user_ids\": [$USER_C],
    \"recipient_dist_ids\": []
  }")
ON_BEHALF_ID=$(echo "$ON_BEHALF" | jq -r '.notification_id')
echo "$ON_BEHALF" | jq

curl -s "$API_BASE$API_PREFIX/notifications?recipient_user_id=$USER_C" | jq \
  --argjson id "$ON_BEHALF_ID" '.[] | select(.notification_id==$id) | {notification_id,sender_user_id,recipient_user_id,event_type}'
```

## 10. TS-DL-003 DL Used in Notification Cannot Be Deleted

```bash
DL_IN_USE=$(curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists" \
  -H "Content-Type: application/json" \
  -d "{\"distribution_list_name\":\"API DL INUSE $TS\"}")
DIST_IN_USE_ID=$(echo "$DL_IN_USE" | jq -r '.dist_id')

curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists/$DIST_IN_USE_ID/members" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER_A}" | jq

curl -s -X POST "$API_BASE$API_PREFIX/notifications" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $SUPERUSER_ID" \
  -d "{
    \"title\": \"DL in use check\",
    \"body\": \"Use DL in notification\",
    \"rev_id\": $REV_ID,
    \"recipient_user_ids\": [],
    \"recipient_dist_ids\": [$DIST_IN_USE_ID]
  }" | jq

# expect 409
curl -i -X DELETE "$API_BASE$API_PREFIX/distribution-lists/$DIST_IN_USE_ID"
```

## 11. Cleanup

```bash
# delete unused temporary DL (expected 200)
TMP_DL=$(curl -s -X POST "$API_BASE$API_PREFIX/distribution-lists" \
  -H "Content-Type: application/json" \
  -d "{\"distribution_list_name\":\"TMP DELETE $(date +%s)\"}")
TMP_DIST_ID=$(echo "$TMP_DL" | jq -r '.dist_id')
curl -s -X DELETE "$API_BASE$API_PREFIX/distribution-lists/$TMP_DIST_ID" | jq
```

## Automated Test Mapping

- `tests/api/api/test_distribution_lists_endpoints.py::test_distribution_lists_crud_and_membership` -> `TS-DL-001`
- `tests/api/api/test_distribution_lists_endpoints.py::test_distribution_lists_duplicate_name_rejected` -> `TS-DL-002`
- `tests/api/api/test_distribution_lists_endpoints.py::test_distribution_list_delete_rejected_when_used_by_notification` -> `TS-DL-003`
- `tests/api/api/test_distribution_lists_endpoints.py::test_distribution_lists_traceability_contract` -> validates this mapping contract.
- `tests/api/api/test_notifications_endpoints.py::test_notifications_create_list_mark_read_flow` -> `TS-NTF-001`
- `tests/api/api/test_notifications_endpoints.py::test_notifications_replace_delete_chain` -> `TS-NTF-002`
- `tests/api/api/test_notifications_endpoints.py::test_notifications_replace_forbidden_for_non_sender_non_superuser` -> `TS-NTF-003`
- `tests/api/api/test_notifications_endpoints.py::test_notifications_mark_read_rejects_payload_user_field` -> `TS-NTF-004`
- `tests/api/api/test_notifications_endpoints.py::test_notifications_create_on_behalf_sender` -> `TS-NTF-005`

## References
- `api/routers/notifications.py`
- `api/schemas/notifications.py`
- `api/routers/distribution_lists.py`
- `api/schemas/distribution_lists.py`
- `documentation/notifications_and_dls.md`
- `tests/api/api/test_distribution_lists_endpoints.py`
- `tests/api/api/test_notifications_endpoints.py`
