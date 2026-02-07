import os
import time

import httpx
import pytest


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


def _first_user_id(client: httpx.Client) -> int | None:
    result = _request(client, "GET", "/people/users")
    if not (200 <= result["status"] < 300) or not result["payload"]:
        return None
    return result["payload"][0].get("user_id")


@pytest.mark.api_smoke
def test_distribution_lists_crud_and_membership():
    with httpx.Client(timeout=10) as client:
        user_id = _first_user_id(client)
        if user_id is None:
            pytest.skip("Missing user seed data for distribution list test")

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

        listed = _request(
            client,
            "GET",
            "/distribution-lists",
        )
        assert 200 <= listed["status"] < 300
        assert any(row.get("dist_id") == dist_id for row in listed["payload"])

        add_member = _request(
            client,
            "POST",
            f"/distribution-lists/{dist_id}/members",
            json={"user_id": user_id},
        )
        assert add_member["status"] == 201
        assert add_member["payload"]["user_id"] == user_id
        assert add_member["payload"]["dist_id"] == dist_id

        members = _request(client, "GET", f"/distribution-lists/{dist_id}/members")
        assert 200 <= members["status"] < 300
        assert any(row.get("user_id") == user_id for row in members["payload"])

        remove_member = _request(
            client,
            "DELETE",
            f"/distribution-lists/{dist_id}/members/{user_id}",
        )
        assert remove_member["status"] == 200
        assert remove_member["payload"]["result"] == "ok"

        members_after = _request(client, "GET", f"/distribution-lists/{dist_id}/members")
        assert 200 <= members_after["status"] < 300
        assert not any(row.get("user_id") == user_id for row in members_after["payload"])

        deleted = _request(client, "DELETE", f"/distribution-lists/{dist_id}")
        assert deleted["status"] == 200
        assert deleted["payload"]["result"] == "ok"

        members_404 = _request(client, "GET", f"/distribution-lists/{dist_id}/members")
        assert members_404["status"] == 404


@pytest.mark.api_smoke
def test_distribution_lists_duplicate_name_rejected():
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
    with httpx.Client(timeout=10) as client:
        user_id = _first_user_id(client)
        if user_id is None:
            pytest.skip("Missing user seed data for distribution list in-use test")

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
            json={"distribution_list_name": f"API DL INUSE {suffix}"},
        )
        assert created_dl["status"] == 201
        dist_id = created_dl["payload"]["dist_id"]

        add_member = _request(
            client,
            "POST",
            f"/distribution-lists/{dist_id}/members",
            json={"user_id": user_id},
        )
        assert add_member["status"] == 201

        created_notification = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": "2"},
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
