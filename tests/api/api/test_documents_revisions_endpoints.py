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


def _get_project_id(client: httpx.Client) -> int | None:
    result = _request(client, "GET", "/lookups/projects")
    if not (200 <= result["status"] < 300):
        return None
    return _extract_first_id(result["payload"], ["project_id"])


def _get_doc_id(client: httpx.Client) -> int | None:
    project_id = _get_project_id(client)
    if project_id is None:
        return None
    docs = _request(client, "GET", "/documents", params={"project_id": project_id})
    if not (200 <= docs["status"] < 300):
        return None
    return _extract_first_id(docs["payload"], ["doc_id", "id"])


@pytest.mark.api_smoke
def test_documents_revisions_list():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for revisions test")
        result = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert 200 <= result["status"] < 300
        assert isinstance(result["payload"], list)
        if result["payload"]:
            sample = result["payload"][0]
            assert sample.get("doc_id") == doc_id
            assert "rev_id" in sample
            assert "rev_status_id" in sample
            assert "rev_code_id" in sample
            assert "seq_num" in sample


@pytest.mark.api_smoke
def test_documents_revisions_missing_doc():
    with httpx.Client(timeout=10) as client:
        result = _request(client, "GET", "/documents/999999/revisions")
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_documents_revisions_update():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for revisions update test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for revisions update test")
        rev_id = revisions["payload"][0].get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for revisions update test")
        updated = _request(
            client,
            "PUT",
            f"/documents/revisions/{rev_id}",
            json={
                "rev_id": rev_id,
                "transmital_current_revision": f"TR-TEST-{rev_id}",
            },
        )
        assert 200 <= updated["status"] < 300
        assert updated["payload"]["rev_id"] == rev_id
        assert updated["payload"]["transmital_current_revision"].startswith("TR-TEST-")


@pytest.mark.api_smoke
def test_documents_revisions_update_missing_fields():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for revisions update missing-fields test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for revisions update missing-fields test")
        rev_id = revisions["payload"][0].get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for revisions update missing-fields test")
        updated = _request(client, "PUT", f"/documents/revisions/{rev_id}", json={"rev_id": rev_id})
        assert updated["status"] == 400


@pytest.mark.api_smoke
def test_documents_revisions_update_mismatch_id():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for revisions update mismatch-id test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for revisions update mismatch-id test")
        rev_id = revisions["payload"][0].get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for revisions update mismatch-id test")
        updated = _request(
            client,
            "PUT",
            f"/documents/revisions/{rev_id}",
            json={"rev_id": rev_id + 1, "transmital_current_revision": "TR-MISMATCH"},
        )
        assert updated["status"] == 400


@pytest.mark.api_smoke
def test_documents_revisions_update_missing_revision():
    with httpx.Client(timeout=10) as client:
        updated = _request(
            client,
            "PUT",
            "/documents/revisions/999999",
            json={"rev_id": 999999, "transmital_current_revision": "TR-MISSING"},
        )
        assert updated["status"] == 404


@pytest.mark.api_smoke
def test_documents_revisions_create():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for revisions create test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for revisions create test")
        base_revision = revisions["payload"][0]
        max_seq_num = max(rev.get("seq_num", 0) for rev in revisions["payload"])
        payload = {
            "rev_code_id": base_revision["rev_code_id"],
            "rev_author_id": base_revision["rev_author_id"],
            "rev_originator_id": base_revision["rev_originator_id"],
            "rev_modifier_id": base_revision["rev_modifier_id"],
            "transmital_current_revision": f"TR-NEW-{doc_id}",
            "planned_start_date": base_revision["planned_start_date"],
            "planned_finish_date": base_revision["planned_finish_date"],
            "rev_status_id": base_revision["rev_status_id"],
        }
        created = _request(client, "POST", f"/documents/{doc_id}/revisions", json=payload)
        assert created["status"] == 201
        assert created["payload"]["doc_id"] == doc_id
        assert created["payload"]["seq_num"] == max_seq_num + 1


@pytest.mark.api_smoke
def test_documents_revisions_create_missing_doc():
    with httpx.Client(timeout=10) as client:
        payload = {
            "rev_code_id": 1,
            "rev_author_id": 1,
            "rev_originator_id": 1,
            "rev_modifier_id": 1,
            "transmital_current_revision": "TR-NEW-999999",
            "planned_start_date": "2024-01-02T12:00:00Z",
            "planned_finish_date": "2024-01-05T12:00:00Z",
            "rev_status_id": 1,
        }
        created = _request(client, "POST", "/documents/999999/revisions", json=payload)
        assert created["status"] == 404


@pytest.mark.api_smoke
def test_documents_revisions_create_missing_required_fields():
    with httpx.Client(timeout=10) as client:
        created = _request(client, "POST", "/documents/1/revisions", json={})
        assert created["status"] == 422
