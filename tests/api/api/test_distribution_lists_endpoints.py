import os
import time
from pathlib import Path

import httpx
import pytest

SCENARIO_DOC_PATH = Path("documentation/test_scenarios/notifications_api_test_plan.md")
TEST_SCENARIO_MAP = {
    "test_distribution_lists_crud_and_membership": ["TS-DL-001"],
    "test_distribution_lists_duplicate_name_rejected": ["TS-DL-002"],
    "test_distribution_list_delete_rejected_when_used_by_notification": ["TS-DL-003"],
}


def _build_base_url() -> str:
    base = os.getenv("API_BASE", "http://localhost:4175").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{base}{prefix}"


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    url = f"{_build_base_url()}{path}"
    start = time.perf_counter()
    response = client.request(method, url, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    payload = None
    if response.content and "application/json" in response.headers.get("content-type", ""):
        payload = response.json()
    return {"status": response.status_code, "payload": payload, "duration_ms": duration_ms}


def _resolve_test_users(client: httpx.Client) -> tuple[int, int, int, int]:
    result = _request(client, "GET", "/people/users")
    if not (200 <= result["status"] < 300) or not result["payload"]:
        pytest.skip("Missing user seed data for distribution list tests")

    user_ids = [row.get("user_id") for row in result["payload"] if isinstance(row, dict)]
    user_ids = [uid for uid in user_ids if uid is not None]
    if len(user_ids) < 3:
        pytest.skip("Need at least 3 users for distribution list tests")

    user_a, user_b, user_c = user_ids[0], user_ids[1], user_ids[2]
    superuser_id = 2
    if superuser_id not in user_ids:
        pytest.skip("Superuser id=2 not available for distribution list tests")
    return user_a, user_b, user_c, superuser_id


@pytest.mark.api_smoke
def test_distribution_lists_crud_and_membership():
    """Scenario IDs: TS-DL-001."""
    with httpx.Client(timeout=10) as client:
        _, user_b, _, _ = _resolve_test_users(client)

        suffix = str(int(time.time() * 1000))[-6:]
        create = _request(
            client,
            "POST",
            "/distribution-lists",
            json={
                "distribution_list_name": f"API DL {suffix}",
            },
        )
        assert create["status"] == 201
        dist_id = create["payload"]["dist_id"]
        assert create["payload"]["doc_id"] is None

        listed = _request(
            client,
            "GET",
            "/distribution-lists",
        )
        assert 200 <= listed["status"] < 300
        created_list_row = next(
            (row for row in listed["payload"] if row.get("dist_id") == dist_id), None
        )
        assert created_list_row is not None
        assert created_list_row.get("doc_id") is None
        filtered_empty = _request(
            client,
            "GET",
            "/distribution-lists",
            params={"doc_id": dist_id},
        )
        assert 200 <= filtered_empty["status"] < 300
        assert not any(row.get("dist_id") == dist_id for row in filtered_empty["payload"])

        add_member = _request(
            client,
            "POST",
            f"/distribution-lists/{dist_id}/members",
            json={"user_id": user_b},
        )
        assert add_member["status"] == 201
        assert add_member["payload"]["user_id"] == user_b
        assert add_member["payload"]["dist_id"] == dist_id

        members = _request(client, "GET", f"/distribution-lists/{dist_id}/members")
        assert 200 <= members["status"] < 300
        assert any(row.get("user_id") == user_b for row in members["payload"])

        remove_member = _request(
            client,
            "DELETE",
            f"/distribution-lists/{dist_id}/members/{user_b}",
        )
        assert remove_member["status"] == 200
        assert remove_member["payload"]["result"] == "ok"

        members_after = _request(client, "GET", f"/distribution-lists/{dist_id}/members")
        assert 200 <= members_after["status"] < 300
        assert not any(row.get("user_id") == user_b for row in members_after["payload"])

        deleted = _request(client, "DELETE", f"/distribution-lists/{dist_id}")
        assert deleted["status"] == 200
        assert deleted["payload"]["result"] == "ok"

        members_404 = _request(client, "GET", f"/distribution-lists/{dist_id}/members")
        assert members_404["status"] == 404


@pytest.mark.api_smoke
def test_distribution_lists_duplicate_name_rejected():
    """Scenario IDs: TS-DL-002."""
    with httpx.Client(timeout=10) as client:
        suffix = str(int(time.time() * 1000))[-6:]
        list_name = f"API DL DUP {suffix}"
        first = _request(
            client,
            "POST",
            "/distribution-lists",
            json={"distribution_list_name": list_name},
        )
        assert first["status"] == 201
        dist_id = first["payload"]["dist_id"]

        second = _request(
            client,
            "POST",
            "/distribution-lists",
            json={"distribution_list_name": list_name},
        )
        assert second["status"] == 400

        _request(client, "DELETE", f"/distribution-lists/{dist_id}")


@pytest.mark.api_smoke
def test_distribution_list_delete_rejected_when_used_by_notification():
    """Scenario IDs: TS-DL-003."""
    with httpx.Client(timeout=10) as client:
        user_a, _, _, superuser_id = _resolve_test_users(client)

        projects = _request(client, "GET", "/lookups/projects")
        if not (200 <= projects["status"] < 300) or not projects["payload"]:
            pytest.skip("Missing project seed data for distribution list in-use test")
        project_id = projects["payload"][0]["project_id"]
        docs = _request(client, "GET", "/documents", params={"project_id": project_id})
        if not (200 <= docs["status"] < 300) or not docs["payload"]:
            pytest.skip("Missing documents for distribution list in-use test")
        doc_id = docs["payload"][0]["doc_id"]
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("Missing revisions for distribution list in-use test")
        rev_id = revisions["payload"][0]["rev_id"]

        suffix = str(int(time.time() * 1000))[-6:]
        created_dl = _request(
            client,
            "POST",
            "/distribution-lists",
            json={"distribution_list_name": f"API DL INUSE {suffix}", "doc_id": doc_id},
        )
        assert created_dl["status"] == 201
        dist_id = created_dl["payload"]["dist_id"]
        assert created_dl["payload"]["doc_id"] == doc_id
        filtered_by_doc = _request(
            client,
            "GET",
            "/distribution-lists",
            params={"doc_id": doc_id},
        )
        assert 200 <= filtered_by_doc["status"] < 300
        assert any(row.get("dist_id") == dist_id for row in filtered_by_doc["payload"])

        add_member = _request(
            client,
            "POST",
            f"/distribution-lists/{dist_id}/members",
            json={"user_id": user_a},
        )
        assert add_member["status"] == 201

        created_notification = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": str(superuser_id)},
            json={
                "title": "DL in use check",
                "body": "Use DL in notification",
                "rev_id": rev_id,
                "recipient_user_ids": [],
                "recipient_dist_ids": [dist_id],
            },
        )
        assert created_notification["status"] == 201

        delete_dl = _request(client, "DELETE", f"/distribution-lists/{dist_id}")
        assert delete_dl["status"] == 409


def test_distribution_lists_traceability_contract():
    """Fails when test-scenario mapping drifts between docs and automated tests."""
    assert SCENARIO_DOC_PATH.exists(), f"Missing scenario doc: {SCENARIO_DOC_PATH}"
    doc_text = SCENARIO_DOC_PATH.read_text(encoding="utf-8")

    for test_name, scenario_ids in TEST_SCENARIO_MAP.items():
        assert test_name in doc_text, f"Missing mapped test in scenario doc: {test_name}"
        for scenario_id in scenario_ids:
            assert scenario_id in doc_text, f"Missing scenario ID in scenario doc: {scenario_id}"
