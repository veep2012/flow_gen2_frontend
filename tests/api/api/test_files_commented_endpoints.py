import os
import time
import uuid

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
        pytest.skip("No projects available for files commented test")
    assert 200 <= projects["status"] < 300
    project_id = _extract_first_id(projects["payload"], ["project_id"])
    if project_id is None:
        pytest.skip("No project_id available for files commented test")

    docs = _request(client, "GET", "/documents", params={"project_id": project_id})
    if docs["status"] == 404:
        pytest.skip("No documents available for files commented test")
    assert 200 <= docs["status"] < 300
    rev_id = None
    for doc in docs["payload"]:
        if not isinstance(doc, dict):
            continue
        rev_id = doc.get("rev_current_id") or doc.get("rev_actual_id")
        if rev_id is not None:
            break
    if rev_id is None:
        pytest.skip("No revision id available for files commented test")

    return rev_id


def _get_test_user(client: httpx.Client) -> tuple[int, str]:
    users = _request(client, "GET", "/people/users")
    if users["status"] == 404:
        pytest.skip("No users available for files commented test")
    assert 200 <= users["status"] < 300
    for item in users["payload"]:
        if not isinstance(item, dict):
            continue
        user_id = item.get("user_id")
        user_acronym = item.get("user_acronym")
        if user_id is not None and user_acronym:
            return user_id, user_acronym
    pytest.skip("No user_id/user_acronym available for files commented test")


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


@pytest.mark.api_smoke
def test_files_commented_list():
    """Test listing commented files by file_id."""
    with httpx.Client(timeout=10) as client:
        # List with a file_id (should return empty list or data)
        result = _request(client, "GET", "/files/commented/list", params={"file_id": 1})
        # Should succeed even if no data exists
        assert 200 <= result["status"] < 300
        assert isinstance(result["payload"], list)


@pytest.mark.api_smoke
def test_files_commented_list_with_user_filter():
    """Test listing commented files by file_id and user_id."""
    with httpx.Client(timeout=10) as client:
        # List with both file_id and user_id
        result = _request(
            client, "GET", "/files/commented/list", params={"file_id": 1, "user_id": 1}
        )
        # Should succeed even if no data exists
        assert 200 <= result["status"] < 300
        assert isinstance(result["payload"], list)


@pytest.mark.api_smoke
def test_files_commented_list_missing_file_id():
    """Test listing commented files without file_id should fail."""
    with httpx.Client(timeout=10) as client:
        # List without file_id (mandatory parameter)
        result = _request(client, "GET", "/files/commented/list")
        # Should fail validation
        assert result["status"] == 422


@pytest.mark.api_smoke
def test_files_commented_insert_and_download():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, _ = _get_test_user(client)
        base_file = _upload_base_file(client, rev_id, suffix, "pdf", "application/pdf")

        commented_content = f"commented-{suffix}".encode()
        insert = _request(
            client,
            "POST",
            "/files/commented/",
            files={
                "file": (
                    f"commented-{suffix}.pdf",
                    commented_content,
                    "application/pdf",
                )
            },
            data={"file_id": str(base_file["id"]), "user_id": str(user_id)},
        )
        assert insert["status"] == 201
        commented_id = insert["payload"]["id"]
        assert insert["payload"]["file_id"] == base_file["id"]
        assert insert["payload"]["user_id"] == user_id
        assert insert["payload"]["filename"] != base_file["filename"]
        assert "_commented_" in insert["payload"]["filename"]
        assert insert["payload"]["mimetype"] == base_file["mimetype"]
        assert insert["payload"]["rev_id"] == base_file["rev_id"]

        listed = _request(
            client,
            "GET",
            "/files/commented/list",
            params={"file_id": base_file["id"], "user_id": user_id},
        )
        assert 200 <= listed["status"] < 300
        assert any(item.get("id") == commented_id for item in listed["payload"])

        downloaded = _request(
            client, "GET", "/files/commented/download", params={"file_id": commented_id}
        )
        assert 200 <= downloaded["status"] < 300
        assert downloaded["content"] == commented_content
        content_disposition = downloaded["headers"].get("content-disposition", "")
        assert insert["payload"]["filename"] in content_disposition

        deleted = _request(client, "DELETE", f"/files/commented/{commented_id}")
        assert deleted["status"] == 204
        _request(client, "DELETE", f"/files/{base_file['id']}")


@pytest.mark.api_smoke
def test_files_commented_insert_without_file_copies_source():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, _ = _get_test_user(client)
        base_file = _upload_base_file(client, rev_id, suffix, "pdf", "application/pdf")

        insert = _request(
            client,
            "POST",
            "/files/commented/",
            data={"file_id": str(base_file["id"]), "user_id": str(user_id)},
        )
        assert insert["status"] == 201
        commented_id = insert["payload"]["id"]
        assert insert["payload"]["file_id"] == base_file["id"]
        assert insert["payload"]["user_id"] == user_id
        assert insert["payload"]["filename"] != base_file["filename"]
        assert "_commented_" in insert["payload"]["filename"]
        assert insert["payload"]["mimetype"] == base_file["mimetype"]
        assert insert["payload"]["rev_id"] == base_file["rev_id"]

        downloaded = _request(
            client, "GET", "/files/commented/download", params={"file_id": commented_id}
        )
        assert 200 <= downloaded["status"] < 300
        assert downloaded["content"] == base_file["content"]
        content_disposition = downloaded["headers"].get("content-disposition", "")
        assert insert["payload"]["filename"] in content_disposition

        _request(client, "DELETE", f"/files/commented/{commented_id}")
        _request(client, "DELETE", f"/files/{base_file['id']}")


@pytest.mark.api_smoke
def test_files_commented_insert_duplicate():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, _ = _get_test_user(client)
        base_file = _upload_base_file(client, rev_id, suffix, "pdf", "application/pdf")

        first = _request(
            client,
            "POST",
            "/files/commented/",
            files={
                "file": (
                    f"commented-{suffix}.pdf",
                    f"commented-{suffix}".encode(),
                    "application/pdf",
                )
            },
            data={"file_id": str(base_file["id"]), "user_id": str(user_id)},
        )
        assert first["status"] == 201
        duplicate = _request(
            client,
            "POST",
            "/files/commented/",
            files={
                "file": (
                    f"commented-{suffix}-dup.pdf",
                    f"commented-{suffix}-dup".encode(),
                    "application/pdf",
                )
            },
            data={"file_id": str(base_file["id"]), "user_id": str(user_id)},
        )
        assert duplicate["status"] == 400
        assert "already exists" in duplicate["payload"]["detail"].lower()

        _request(client, "DELETE", f"/files/commented/{first['payload']['id']}")
        _request(client, "DELETE", f"/files/{base_file['id']}")


@pytest.mark.api_smoke
def test_files_commented_delete_nonexistent():
    """Test deleting a non-existent commented file."""
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "DELETE",
            "/files/commented/999999",
        )
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_files_commented_download_nonexistent():
    """Test downloading a non-existent commented file."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, "GET", "/files/commented/download", params={"file_id": 999999})
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_files_commented_insert_missing_fields():
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "POST",
            "/files/commented/",
            files={"file": ("missing.pdf", b"content", "application/pdf")},
            data={"user_id": "1"},
        )
        assert result["status"] == 422
        result = _request(
            client,
            "POST",
            "/files/commented/",
            files={"file": ("missing.pdf", b"content", "application/pdf")},
            data={"file_id": "1"},
        )
        assert result["status"] == 422


@pytest.mark.api_smoke
def test_files_commented_insert_nonexistent_file_or_user():
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "POST",
            "/files/commented/",
            files={"file": ("missing.pdf", b"content", "application/pdf")},
            data={"file_id": "999999", "user_id": "1"},
        )
        assert result["status"] == 404
        result = _request(
            client,
            "POST",
            "/files/commented/",
            files={"file": ("missing.pdf", b"content", "application/pdf")},
            data={"file_id": "1", "user_id": "999999"},
        )
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_files_commented_insert_mimetype_mismatch():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, _ = _get_test_user(client)
        base_file = _upload_base_file(client, rev_id, suffix, "pdf", "application/pdf")

        mismatch = _request(
            client,
            "POST",
            "/files/commented/",
            files={
                "file": (
                    f"commented-{suffix}.docx",
                    f"commented-{suffix}".encode(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"file_id": str(base_file["id"]), "user_id": str(user_id)},
        )
        assert mismatch["status"] in [400, 415]

        _request(client, "DELETE", f"/files/{base_file['id']}")
