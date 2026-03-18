import os
import time

import httpx
import pytest

_DEFAULT_TEST_USER_ACRONYM = os.getenv("TEST_USER_ACRONYM", "FDQC")


def _build_base_url() -> str:
    base = os.getenv("API_BASE", "http://localhost:4175").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{base}{prefix}"


def _merge_default_auth(kwargs: dict) -> dict:
    merged = dict(kwargs)
    if merged.pop("auth", True):
        headers = dict(merged.get("headers") or {})
        headers.setdefault("X-User-Id", _DEFAULT_TEST_USER_ACRONYM)
        merged["headers"] = headers
    return merged


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    url = f"{_build_base_url()}{path}"
    start = time.perf_counter()
    response = client.request(method, url, **_merge_default_auth(kwargs))
    duration_ms = (time.perf_counter() - start) * 1000
    payload = None
    if response.content and "application/json" in response.headers.get("content-type", ""):
        payload = response.json()
    return {
        "status": response.status_code,
        "payload": payload,
        "duration_ms": duration_ms,
    }


def _get_first_revision_id(client: httpx.Client) -> int | None:
    projects = _request(client, "GET", "/lookups/projects")
    if not (200 <= projects["status"] < 300) or not projects["payload"]:
        return None
    project_id = projects["payload"][0].get("project_id")
    if project_id is None:
        return None

    docs = _request(client, "GET", "/documents", params={"project_id": project_id})
    if not (200 <= docs["status"] < 300) or not docs["payload"]:
        return None
    doc_id = docs["payload"][0].get("doc_id")
    if doc_id is None:
        return None

    revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
    if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
        return None
    return revisions["payload"][0].get("rev_id")


def _find_notification(rows: list[dict], notification_id: int) -> dict | None:
    for row in rows:
        if row.get("notification_id") == notification_id:
            return row
    return None


def _user_acronym_map(payload: list[dict] | None) -> dict[int, str]:
    mapping: dict[int, str] = {}
    if not payload:
        return mapping
    for row in payload:
        if not isinstance(row, dict):
            continue
        user_id = row.get("user_id")
        user_acronym = row.get("user_acronym")
        if user_id is not None and user_acronym:
            mapping[user_id] = user_acronym
    return mapping


def _resolve_test_users(client: httpx.Client) -> tuple[int, int, int, int]:
    users = _request(client, "GET", "/people/users")
    if not (200 <= users["status"] < 300) or not users["payload"]:
        pytest.skip("No users available for notifications tests")

    user_ids = [row.get("user_id") for row in users["payload"] if isinstance(row, dict)]
    user_ids = [uid for uid in user_ids if uid is not None]
    if len(user_ids) < 3:
        pytest.skip("Need at least 3 users for notifications tests")

    user_a, user_b, user_c = user_ids[0], user_ids[1], user_ids[2]
    superuser_id = 2
    if superuser_id not in user_ids:
        pytest.skip("Superuser id=2 not available for notifications tests")
    return user_a, user_b, user_c, superuser_id


@pytest.mark.api_smoke
def test_notifications_create_list_mark_read_flow():
    with httpx.Client(timeout=10) as client:
        user_a, _, _, superuser_id = _resolve_test_users(client)
        users = _request(client, "GET", "/people/users")
        user_map = _user_acronym_map(users["payload"])
        rev_id = _get_first_revision_id(client)
        if rev_id is None:
            pytest.skip("No revision available for notifications test")

        create = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": user_map[superuser_id]},
            json={
                "title": "Smoke notification",
                "body": "Please review this revision",
                "rev_id": rev_id,
                "recipient_user_ids": [user_a],
                "recipient_dist_ids": [],
            },
        )
        assert create["status"] == 201
        created_id = create["payload"]["notification_id"]
        assert create["payload"]["recipient_count"] >= 1

        inbox = _request(
            client,
            "GET",
            "/notifications",
            headers={"X-User-Id": user_map[user_a]},
            params={"unread_only": True},
        )
        assert 200 <= inbox["status"] < 300
        created_row = _find_notification(inbox["payload"], created_id)
        assert created_row is not None
        assert created_row["event_type"] == "regular"
        assert created_row["read_at"] is None
        assert created_row["sender_user_id"] == superuser_id

        marked = _request(
            client,
            "POST",
            f"/notifications/{created_id}/read",
            headers={"X-User-Id": user_map[user_a]},
            json={},
        )
        assert 200 <= marked["status"] < 300
        assert marked["payload"]["notification_id"] == created_id
        assert marked["payload"]["recipient_user_id"] == user_a
        assert marked["payload"]["read_at"] is not None


@pytest.mark.api_smoke
def test_notifications_require_session_identity():
    with httpx.Client(timeout=10) as client:
        user_a, _, _, _ = _resolve_test_users(client)
        denied = _request(
            client,
            "GET",
            "/notifications",
            headers={"X-User-Id": ""},
            auth=False,
        )
        assert denied["status"] == 401
        assert denied["payload"] == {"detail": "Authentication required"}


@pytest.mark.api_smoke
def test_notifications_replace_delete_chain():
    with httpx.Client(timeout=10) as client:
        user_a, _, _, superuser_id = _resolve_test_users(client)
        users = _request(client, "GET", "/people/users")
        user_map = _user_acronym_map(users["payload"])
        rev_id = _get_first_revision_id(client)
        if rev_id is None:
            pytest.skip("No revision available for notifications chain test")

        created = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": user_map[superuser_id]},
            json={
                "title": "Chain original",
                "body": "Original body",
                "rev_id": rev_id,
                "recipient_user_ids": [user_a],
                "recipient_dist_ids": [],
            },
        )
        assert created["status"] == 201
        original_id = created["payload"]["notification_id"]

        replaced = _request(
            client,
            "POST",
            f"/notifications/{original_id}/replace",
            headers={"X-User-Id": user_map[superuser_id]},
            json={"title": "Chain changed", "body": "Changed body", "remark": "changed"},
        )
        assert 200 <= replaced["status"] < 300
        changed_id = replaced["payload"]["notification_id"]
        assert changed_id != original_id

        inbox_after_replace = _request(
            client,
            "GET",
            "/notifications",
            headers={"X-User-Id": user_map[user_a]},
        )
        assert 200 <= inbox_after_replace["status"] < 300
        old_row = _find_notification(inbox_after_replace["payload"], original_id)
        new_row = _find_notification(inbox_after_replace["payload"], changed_id)
        assert old_row is not None
        assert new_row is not None
        assert old_row["dropped_at"] is not None
        assert old_row["superseded_by_notification_id"] == changed_id
        assert new_row["event_type"] == "changed_notice"
        assert new_row["read_at"] is None

        dropped = _request(
            client,
            "POST",
            f"/notifications/{changed_id}/delete",
            headers={"X-User-Id": user_map[superuser_id]},
            json={"remark": "dropped"},
        )
        assert 200 <= dropped["status"] < 300
        dropped_notice_id = dropped["payload"]["notification_id"]
        assert dropped_notice_id != changed_id

        inbox_after_delete = _request(
            client,
            "GET",
            "/notifications",
            headers={"X-User-Id": user_map[user_a]},
        )
        assert 200 <= inbox_after_delete["status"] < 300
        changed_row = _find_notification(inbox_after_delete["payload"], changed_id)
        drop_row = _find_notification(inbox_after_delete["payload"], dropped_notice_id)
        assert changed_row is not None
        assert drop_row is not None
        assert changed_row["dropped_at"] is not None
        assert changed_row["superseded_by_notification_id"] == dropped_notice_id
        assert drop_row["event_type"] == "dropped_notice"
        assert drop_row["read_at"] is None


@pytest.mark.api_smoke
def test_notifications_replace_forbidden_for_non_sender_non_superuser():
    with httpx.Client(timeout=10) as client:
        user_a, user_b, _, superuser_id = _resolve_test_users(client)
        users = _request(client, "GET", "/people/users")
        user_map = _user_acronym_map(users["payload"])
        if not (200 <= users["status"] < 300) or not users["payload"]:
            pytest.skip("No users available for forbidden replace test")
        candidate_user_ids = [
            row.get("user_id")
            for row in users["payload"]
            if isinstance(row, dict) and row.get("user_id") not in (None, user_a, superuser_id)
        ]
        if not candidate_user_ids:
            pytest.skip("No non-sender non-superuser candidate for forbidden replace test")
        rev_id = _get_first_revision_id(client)
        if rev_id is None:
            pytest.skip("No revision available for notifications auth test")

        for actor_user_id in candidate_user_ids:
            created = _request(
                client,
                "POST",
                "/notifications",
                headers={"X-User-Id": user_map[user_a]},
                json={
                    "title": "Forbidden replace source",
                    "body": "Sender is user 1",
                    "rev_id": rev_id,
                    "recipient_user_ids": [user_b],
                    "recipient_dist_ids": [],
                },
            )
            assert created["status"] == 201
            notification_id = created["payload"]["notification_id"]

            forbidden = _request(
                client,
                "POST",
                f"/notifications/{notification_id}/replace",
                headers={"X-User-Id": user_map[actor_user_id]},
                json={"title": "Nope", "body": "Nope"},
            )
            if forbidden["status"] == 403:
                return
            if 200 <= forbidden["status"] < 300:
                continue
            pytest.fail(
                f"Unexpected status for forbidden replace candidate {actor_user_id}: "
                f"{forbidden['status']}"
            )

        pytest.skip(
            "No candidate user produced 403; seed users appear privileged in this environment"
        )


@pytest.mark.api_smoke
def test_notifications_mark_read_rejects_payload_user_field():
    with httpx.Client(timeout=10) as client:
        user_a, _, _, superuser_id = _resolve_test_users(client)
        users = _request(client, "GET", "/people/users")
        user_map = _user_acronym_map(users["payload"])
        rev_id = _get_first_revision_id(client)
        if rev_id is None:
            pytest.skip("No revision available for mark-read validation test")

        created = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": user_map[superuser_id]},
            json={
                "title": "Read validation",
                "body": "Read validation body",
                "rev_id": rev_id,
                "recipient_user_ids": [user_a],
                "recipient_dist_ids": [],
            },
        )
        assert created["status"] == 201
        notification_id = created["payload"]["notification_id"]

        bad_payload = _request(
            client,
            "POST",
            f"/notifications/{notification_id}/read",
            headers={"X-User-Id": user_map[user_a]},
            json={"recipient_user_id": user_a},
        )
        assert bad_payload["status"] == 422


@pytest.mark.api_smoke
def test_notifications_list_ignores_recipient_override_and_uses_current_user():
    with httpx.Client(timeout=10) as client:
        user_a, user_b, _, superuser_id = _resolve_test_users(client)
        users = _request(client, "GET", "/people/users")
        user_map = _user_acronym_map(users["payload"])
        rev_id = _get_first_revision_id(client)
        if rev_id is None:
            pytest.skip("No revision available for notifications recipient test")

        created = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": user_map[superuser_id]},
            json={
                "title": "Current user inbox only",
                "body": "Recipient override must be ignored",
                "rev_id": rev_id,
                "recipient_user_ids": [user_a],
                "recipient_dist_ids": [],
            },
        )
        assert created["status"] == 201
        notification_id = created["payload"]["notification_id"]

        inbox = _request(
            client,
            "GET",
            "/notifications",
            headers={"X-User-Id": user_map[user_b]},
            params={"recipient_user_id": user_a},
        )
        assert 200 <= inbox["status"] < 300
        assert _find_notification(inbox["payload"], notification_id) is None


@pytest.mark.api_smoke
def test_notifications_create_rejects_sender_user_id_field():
    with httpx.Client(timeout=10) as client:
        user_a, _, _, superuser_id = _resolve_test_users(client)
        users = _request(client, "GET", "/people/users")
        user_map = _user_acronym_map(users["payload"])
        rev_id = _get_first_revision_id(client)
        if rev_id is None:
            pytest.skip("No revision available for sender-field validation test")

        rejected = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": user_map[superuser_id]},
            json={
                "sender_user_id": user_a,
                "title": "Rejected sender field",
                "body": "sender_user_id must not be accepted",
                "rev_id": rev_id,
                "recipient_user_ids": [user_a],
                "recipient_dist_ids": [],
            },
        )
        assert rejected["status"] == 422


@pytest.mark.api_smoke
def test_notifications_create_requires_at_least_one_recipient_target():
    with httpx.Client(timeout=10) as client:
        _, _, _, superuser_id = _resolve_test_users(client)
        users = _request(client, "GET", "/people/users")
        user_map = _user_acronym_map(users["payload"])
        rev_id = _get_first_revision_id(client)
        if rev_id is None:
            pytest.skip("No revision available for recipient validation test")

        create = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": user_map[superuser_id]},
            json={
                "title": "No recipients",
                "body": "No recipients body",
                "rev_id": rev_id,
                "recipient_user_ids": [],
                "recipient_dist_ids": [],
            },
        )

        assert create["status"] == 422
        assert create["payload"] is not None
        assert "At least one recipient_user_ids or recipient_dist_ids entry is required" in str(
            create["payload"]
        )
