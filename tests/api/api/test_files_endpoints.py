import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

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
    """
    Helper function to get a valid revision ID for testing.

    Returns:
        int: A valid revision ID.

    Raises:
        pytest.skip: If no revision ID is available.
    """
    projects = _request(client, "GET", "/lookups/projects")
    if projects["status"] == 404:
        pytest.skip("No projects available for files test")
    assert 200 <= projects["status"] < 300
    project_id = _extract_first_id(projects["payload"], ["project_id"])
    if project_id is None:
        pytest.skip("No project_id available for files test")

    docs = _request(client, "GET", "/documents/list", params={"project_id": project_id})
    if docs["status"] == 404:
        pytest.skip("No documents available for files test")
    assert 200 <= docs["status"] < 300
    rev_id = None
    for doc in docs["payload"]:
        if not isinstance(doc, dict):
            continue
        rev_id = doc.get("rev_current_id") or doc.get("rev_actual_id")
        if rev_id is not None:
            break
    if rev_id is None:
        pytest.skip("No revision id available for files test")

    return rev_id


@pytest.mark.api_smoke
def test_files_crud_and_download():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)

        content = f"test-{suffix}".encode()
        upload = _request(
            client,
            "POST",
            "/files/insert",
            files={"file": (f"file-{suffix}.pdf", content, "application/pdf")},
            data={"rev_id": str(rev_id)},
        )
        assert upload["status"] == 201
        file_id = upload["payload"]["id"]

        updated = _request(
            client,
            "PUT",
            "/files/update",
            json={"id": file_id, "filename": f"file-{suffix}-v2.pdf"},
        )
        assert 200 <= updated["status"] < 300
        assert updated["payload"]["filename"] == f"file-{suffix}-v2.pdf"

        listed = _request(client, "GET", "/files/list", params={"rev_id": rev_id})
        assert 200 <= listed["status"] < 300
        assert any(item.get("id") == file_id for item in listed["payload"])

        downloaded = _request(client, "GET", "/files/download", params={"file_id": file_id})
        assert 200 <= downloaded["status"] < 300
        assert downloaded["content"] == content
        content_disposition = downloaded["headers"].get("content-disposition", "")
        assert f"file-{suffix}-v2.pdf" in content_disposition
        assert "etag" in downloaded["headers"]
        assert "last-modified" in downloaded["headers"]

        deleted = _request(client, "DELETE", "/files/delete", json={"id": file_id})
        assert deleted["status"] == 204

        listed_after = _request(client, "GET", "/files/list", params={"rev_id": rev_id})
        assert 200 <= listed_after["status"] < 300
        assert all(item.get("id") != file_id for item in listed_after["payload"])


@pytest.mark.api_smoke
def test_files_insert_empty_file_rejected():
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "POST",
            "/files/insert",
            files={"file": ("empty.txt", b"", "text/plain")},
            data={"rev_id": "1"},
        )
        assert result["status"] == 400


@pytest.mark.api_smoke
def test_files_insert_long_filename_rejected():
    long_name = "a" * 91 + ".txt"
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "POST",
            "/files/insert",
            files={"file": (long_name, b"content", "text/plain")},
            data={"rev_id": "1"},
        )
        assert result["status"] == 400


@pytest.mark.api_smoke
def test_files_insert_nonexistent_revision():
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "POST",
            "/files/insert",
            files={"file": ("file.txt", b"content", "text/plain")},
            data={"rev_id": "999999"},
        )
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_files_insert_unaccepted_file_type_rejected():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)

        result = _request(
            client,
            "POST",
            "/files/insert",
            files={"file": (f"file-{suffix}.txt", b"content", "text/plain")},
            data={"rev_id": str(rev_id)},
        )
        assert result["status"] == 400
        assert "not accepted" in result["payload"]["detail"].lower()


@pytest.mark.api_smoke
def test_files_insert_accepted_file_type_pdf():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)

        content = f"test-{suffix}".encode()
        upload = _request(
            client,
            "POST",
            "/files/insert",
            files={"file": (f"file-{suffix}.pdf", content, "application/pdf")},
            data={"rev_id": str(rev_id)},
        )
        assert upload["status"] == 201
        file_id = upload["payload"]["id"]

        # Cleanup
        _request(client, "DELETE", "/files/delete", json={"id": file_id})


@pytest.mark.api_smoke
def test_files_insert_no_extension_rejected():
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)

        result = _request(
            client,
            "POST",
            "/files/insert",
            files={"file": ("filename_no_extension", b"content", "application/octet-stream")},
            data={"rev_id": str(rev_id)},
        )
        assert result["status"] == 400
        assert "must have an extension" in result["payload"]["detail"].lower()


@pytest.mark.api_smoke
def test_files_concurrent_uploads_same_revision():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        docs = _request(client, "GET", "/documents/list", params={"project_id": 1})
        if docs["status"] == 404:
            pytest.skip("No documents available for files test")
        assert 200 <= docs["status"] < 300
        rev_id = None
        for doc in docs["payload"]:
            if not isinstance(doc, dict):
                continue
            rev_id = doc.get("rev_current_id") or doc.get("rev_actual_id")
            if rev_id is not None:
                break
        if rev_id is None:
            pytest.skip("No revision id available for files test")

        def _upload(idx: int) -> int:
            result = _request(
                client,
                "POST",
                "/files/insert",
                files={
                    "file": (
                        f"file-{suffix}-{idx}.pdf",
                        f"content-{suffix}-{idx}".encode(),
                        "application/pdf",
                    )
                },
                data={"rev_id": str(rev_id)},
            )
            return result["status"]

        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(_upload, [1, 2]))

        assert all(status == 201 for status in statuses)
