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
def test_files_commented_update_nonexistent():
    """Test updating a non-existent commented file."""
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "PUT",
            "/files/commented/update",
            json={"id": 999999, "s3_uid": "test/path/file.pdf"},
        )
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_files_commented_update_empty_s3_uid():
    """Test updating a commented file with empty s3_uid."""
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "PUT",
            "/files/commented/update",
            json={"id": 1, "s3_uid": "   "},
        )
        # Pydantic will reject whitespace-only strings, or 404 if id doesn't exist
        assert result["status"] in [422, 404]


@pytest.mark.api_smoke
def test_files_commented_delete_nonexistent():
    """Test deleting a non-existent commented file."""
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "DELETE",
            "/files/commented/delete",
            json={"id": 999999},
        )
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_files_commented_download_nonexistent():
    """Test downloading a non-existent commented file."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, "GET", "/files/commented/download", params={"file_id": 999999})
        assert result["status"] == 404
