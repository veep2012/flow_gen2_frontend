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
    return {
        "status": response.status_code,
        "payload": payload,
        "duration_ms": duration_ms,
        "headers": response.headers,
        "content": response.content,
    }


def _extract_first_id(items: list, keys: list[str]) -> int | None:
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in keys:
            value = item.get(key)
            if value is not None:
                return value
    return None


def _get_test_revision_id(client: httpx.Client) -> int:
    projects = _request(client, "GET", "/lookups/projects")
    if projects["status"] == 404:
        pytest.skip("No projects available for comments test")
    assert 200 <= projects["status"] < 300
    project_id = _extract_first_id(projects["payload"], ["project_id"])
    if project_id is None:
        pytest.skip("No project_id available for comments test")

    docs = _request(client, "GET", "/documents", params={"project_id": project_id})
    if docs["status"] == 404:
        pytest.skip("No documents available for comments test")
    assert 200 <= docs["status"] < 300
    rev_id = None
    for doc in docs["payload"]:
        if not isinstance(doc, dict):
            continue
        rev_id = doc.get("rev_current_id") or doc.get("rev_actual_id")
        if rev_id is not None:
            break
    if rev_id is None:
        pytest.skip("No revision id available for comments test")

    return rev_id


def _get_test_user(client: httpx.Client) -> tuple[int, str]:
    users = _request(client, "GET", "/people/users")
    if users["status"] == 404:
        pytest.skip("No users available for comments test")
    assert 200 <= users["status"] < 300
    for item in users["payload"]:
        if not isinstance(item, dict):
            continue
        user_id = item.get("user_id")
        user_acronym = item.get("user_acronym")
        if user_id is not None and user_acronym:
            return user_id, user_acronym
    pytest.skip("No user_id/user_acronym available for comments test")


def _get_second_test_user(client: httpx.Client, exclude_user_id: int) -> tuple[int, str] | None:
    users = _request(client, "GET", "/people/users")
    if users["status"] == 404:
        return None
    if not (200 <= users["status"] < 300):
        return None
    for item in users["payload"]:
        if not isinstance(item, dict):
            continue
        user_id = item.get("user_id")
        user_acronym = item.get("user_acronym")
        role_name = str(item.get("role_name") or "").strip().lower()
        if (
            user_id is not None
            and user_acronym
            and user_id != exclude_user_id
            and role_name
            not in {
                "superuser",
                "admin",
            }
        ):
            return user_id, user_acronym
    return None


def _upload_base_file(
    client: httpx.Client, rev_id: int, suffix: str, ext: str, mimetype: str
) -> dict:
    content = f"base-{suffix}".encode()
    filename = f"file-{suffix}.{ext}"
    upload = _request(
        client,
        "POST",
        "/files/",
        files={"file": (filename, content, mimetype)},
        data={"rev_id": str(rev_id)},
    )
    assert upload["status"] == 201
    return {
        "id": upload["payload"]["id"],
        "filename": upload["payload"]["filename"],
        "mimetype": upload["payload"]["mimetype"],
        "rev_id": upload["payload"]["rev_id"],
        "content": content,
    }
