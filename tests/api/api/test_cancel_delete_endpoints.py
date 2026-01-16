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
def test_cancel_revision():
    """Test canceling a revision sets cancelled_date."""
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for cancel revision test")

        # Get revisions for the document
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for cancel revision test")

        rev_id = revisions["payload"][0].get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for cancel revision test")

        # Check initial state - cancelled_date should be None
        initial_canceled_date = revisions["payload"][0].get("canceled_date")
        assert initial_canceled_date is None, "canceled_date should be None initially"

        # Cancel the revision
        result = _request(client, "PATCH", f"/documents/revisions/{rev_id}/cancel")
        assert 200 <= result["status"] < 300, f"Expected 2xx status, got {result['status']}"
        assert result["payload"]["rev_id"] == rev_id
        assert result["payload"]["canceled_date"] is not None, "canceled_date should be set"

        # Verify the change persisted
        updated_revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert 200 <= updated_revisions["status"] < 300
        updated_rev = next((r for r in updated_revisions["payload"] if r["rev_id"] == rev_id), None)
        assert updated_rev is not None
        assert updated_rev["canceled_date"] is not None, "canceled_date should persist"


@pytest.mark.api_smoke
def test_cancel_revision_not_found():
    """Test canceling a non-existent revision returns 404."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, "PATCH", "/documents/revisions/999999/cancel")
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_delete_document_void():
    """Test deleting a document with multiple revisions sets voided to true."""
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for delete document test")

        # Get revisions to check count
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for delete document test")

        # If there's only one revision, create another to ensure voiding behavior
        if len(revisions["payload"]) == 1:
            base_revision = revisions["payload"][0]
            # Try to create a new revision
            new_rev_payload = {
                "rev_code_id": base_revision["rev_code_id"],
                "rev_author_id": base_revision["rev_author_id"],
                "rev_originator_id": base_revision["rev_originator_id"],
                "rev_modifier_id": base_revision["rev_modifier_id"],
                "transmital_current_revision": "TR-TEST-DELETE",
                "planned_start_date": base_revision["planned_start_date"],
                "planned_finish_date": base_revision["planned_finish_date"],
                "rev_status_id": base_revision["rev_status_id"],
            }
            create_result = _request(
                client,
                "POST",
                f"/documents/{doc_id}/revisions",
                json=new_rev_payload,
            )
            if not (200 <= create_result["status"] < 300):
                pytest.skip("Could not create additional revision for void test")

        # Check initial voided state
        project_id = _get_project_id(client)
        docs = _request(client, "GET", "/documents", params={"project_id": project_id})
        doc = next((d for d in docs["payload"] if d["doc_id"] == doc_id), None)
        if doc:
            initial_voided = doc.get("voided", False)
            assert initial_voided is False, "Document should not be voided initially"

        # Delete the document (should void it)
        result = _request(client, "DELETE", f"/documents/{doc_id}")
        assert result["status"] == 204, f"Expected 204 status, got {result['status']}"

        # Verify the document is not listed after soft delete unless show_voided is set
        docs_after = _request(client, "GET", "/documents", params={"project_id": project_id})
        doc_after = next((d for d in docs_after["payload"] if d["doc_id"] == doc_id), None)
        assert doc_after is None, "Voided documents should be excluded from list responses"

        docs_after_voided = _request(
            client,
            "GET",
            "/documents",
            params={"project_id": project_id, "show_voided": True},
        )
        doc_after_voided = next(
            (d for d in docs_after_voided["payload"] if d["doc_id"] == doc_id), None
        )
        assert doc_after_voided is not None, "Voided documents should be included when requested"

        revisions_after = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert revisions_after["status"] == 404


@pytest.mark.api_smoke
def test_delete_document_not_found():
    """Test deleting a non-existent document returns 404."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, "DELETE", "/documents/999999")
        assert result["status"] == 404
