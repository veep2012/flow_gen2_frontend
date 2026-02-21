import os
import time
from concurrent import futures

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


def _create_document(client: httpx.Client) -> tuple[int, int | None]:
    areas = _request(client, "GET", "/lookups/areas")
    area_id = _extract_first_id(areas["payload"], ["area_id"]) if areas["status"] < 300 else None
    units = _request(client, "GET", "/lookups/units")
    unit_id = _extract_first_id(units["payload"], ["unit_id"]) if units["status"] < 300 else None
    doc_types = _request(client, "GET", "/documents/doc_types")
    type_id = (
        _extract_first_id(doc_types["payload"], ["type_id"]) if doc_types["status"] < 300 else None
    )
    rev_codes = _request(client, "GET", "/documents/revision_overview")
    rev_code_id = (
        _extract_first_id(rev_codes["payload"], ["rev_code_id"])
        if rev_codes["status"] < 300
        else None
    )
    persons = _request(client, "GET", "/people/persons")
    person_id = (
        _extract_first_id(persons["payload"], ["person_id"]) if persons["status"] < 300 else None
    )
    project_id = _get_project_id(client)
    if None in (area_id, unit_id, type_id, rev_code_id, person_id):
        pytest.skip("Missing reference data for document creation test")
    suffix = str(int(time.time() * 1000))[-6:]
    payload = {
        "doc_name_unique": f"DOC-{suffix}",
        "title": f"Test Document {suffix}",
        "project_id": project_id,
        "type_id": type_id,
        "area_id": area_id,
        "unit_id": unit_id,
        "rev_code_id": rev_code_id,
        "rev_author_id": person_id,
        "rev_originator_id": person_id,
        "rev_modifier_id": person_id,
        "transmital_current_revision": f"TR-{suffix}",
        "planned_start_date": "2024-01-01T00:00:00Z",
        "planned_finish_date": "2024-12-31T23:59:59Z",
    }
    created = _request(client, "POST", "/documents", json=payload)
    if created["status"] != 201:
        pytest.skip("Document creation failed for delete test")
    doc_id = created["payload"]["doc_id"]

    distribution_lists = _request(client, "GET", "/distribution-lists")
    if not (200 <= distribution_lists["status"] < 300):
        pytest.skip("Distribution lists unavailable for document-linked DL assertion")
    linked_dl = next(
        (
            row
            for row in distribution_lists["payload"]
            if isinstance(row, dict) and row.get("doc_id") == doc_id
        ),
        None,
    )
    assert linked_dl is not None, "Expected auto-created document-linked distribution list"
    assert linked_dl.get("distribution_list_name") == f"DL_{payload['doc_name_unique']}"

    return doc_id, project_id


def _get_final_status_ids(client: httpx.Client) -> set[int]:
    statuses = _request(client, "GET", "/lookups/doc_rev_statuses")
    if not (200 <= statuses["status"] < 300):
        return set()
    return {
        status["rev_status_id"]
        for status in statuses["payload"]
        if isinstance(status, dict) and status.get("final") is True
    }


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

        final_status_ids = _get_final_status_ids(client)
        cancellable = next(
            (
                rev
                for rev in revisions["payload"]
                if rev.get("rev_status_id") not in final_status_ids
            ),
            None,
        )
        if not cancellable:
            pytest.skip("No cancellable revision available for cancel revision test")
        rev_id = cancellable.get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for cancel revision test")

        # Check initial state - cancelled_date should be None
        initial_canceled_date = cancellable.get("canceled_date")
        assert initial_canceled_date is None, "canceled_date should be None initially"

        # Cancel the revision
        result = _request(client, "PATCH", f"/documents/revisions/{rev_id}/cancel")
        assert 200 <= result["status"] < 300, f"Expected 2xx status, got {result['status']}"
        assert result["payload"]["rev_id"] == rev_id
        assert result["payload"]["canceled_date"] is not None, "canceled_date should be set"

        # Cancel again should be idempotent
        second_result = _request(client, "PATCH", f"/documents/revisions/{rev_id}/cancel")
        assert 200 <= second_result["status"] < 300
        assert second_result["payload"]["canceled_date"] == result["payload"]["canceled_date"]

        # Verify the change persisted
        updated_revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert 200 <= updated_revisions["status"] < 300
        updated_rev = next((r for r in updated_revisions["payload"] if r["rev_id"] == rev_id), None)
        assert updated_rev is not None
        assert updated_rev["canceled_date"] is not None, "canceled_date should persist"


@pytest.mark.api_smoke
def test_cancel_revision_not_cancellable():
    with httpx.Client(timeout=10) as client:
        final_status_ids = _get_final_status_ids(client)
        if not final_status_ids:
            pytest.skip("No final revision status available for cancel test")
        project_id = _get_project_id(client)
        if project_id is None:
            pytest.skip("No project available for cancel test")
        docs = _request(client, "GET", "/documents", params={"project_id": project_id})
        if not (200 <= docs["status"] < 300):
            pytest.skip("No documents available for cancel test")
        rev_id = None
        for doc in docs["payload"]:
            doc_id = doc.get("doc_id")
            if doc_id is None:
                continue
            revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
            if not (200 <= revisions["status"] < 300):
                continue
            match = next(
                (
                    rev
                    for rev in revisions["payload"]
                    if rev.get("rev_status_id") in final_status_ids
                ),
                None,
            )
            if match:
                rev_id = match["rev_id"]
                break
        if rev_id is None:
            pytest.skip("No final-status revision available for cancel test")
        result = _request(client, "PATCH", f"/documents/revisions/{rev_id}/cancel")
        assert result["status"] == 409


@pytest.mark.api_smoke
def test_cancel_revision_not_found():
    """Test canceling a non-existent revision returns 404."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, "PATCH", "/documents/revisions/999999/cancel")
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_delete_document_hard_delete_cascade():
    with httpx.Client(timeout=10) as client:
        doc_id, project_id = _create_document(client)
        result = _request(client, "DELETE", f"/documents/{doc_id}")
        assert result["status"] == 200
        assert result["payload"]["result"] == "deleted"
        if project_id is not None:
            docs_after = _request(client, "GET", "/documents", params={"project_id": project_id})
            assert not any(d.get("doc_id") == doc_id for d in docs_after["payload"])
        revisions_after = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert revisions_after["status"] == 404


@pytest.mark.api_smoke
def test_delete_document_void():
    """Test deleting a document with multiple revisions sets voided to true."""
    with httpx.Client(timeout=10) as client:
        doc_id, project_id = _create_document(client)
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for delete document test")
        base_revision = revisions["payload"][0]
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
        docs = _request(client, "GET", "/documents", params={"project_id": project_id})
        doc = next((d for d in docs["payload"] if d["doc_id"] == doc_id), None)
        if doc:
            initial_voided = doc.get("voided", False)
            assert initial_voided is False, "Document should not be voided initially"

        # Delete the document (should void it)
        result = _request(client, "DELETE", f"/documents/{doc_id}")
        assert result["status"] == 200, f"Expected 200 status, got {result['status']}"
        assert result["payload"]["result"] == "voided"

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
def test_delete_document_void_idempotent():
    with httpx.Client(timeout=10) as client:
        doc_id, _ = _create_document(client)
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for delete idempotency test")
        base_revision = revisions["payload"][0]
        create_result = _request(
            client,
            "POST",
            f"/documents/{doc_id}/revisions",
            json={
                "rev_code_id": base_revision["rev_code_id"],
                "rev_author_id": base_revision["rev_author_id"],
                "rev_originator_id": base_revision["rev_originator_id"],
                "rev_modifier_id": base_revision["rev_modifier_id"],
                "transmital_current_revision": "TR-TEST-DELETE-IDEMP",
                "planned_start_date": base_revision["planned_start_date"],
                "planned_finish_date": base_revision["planned_finish_date"],
                "rev_status_id": base_revision["rev_status_id"],
            },
        )
        if not (200 <= create_result["status"] < 300):
            pytest.skip("Could not create additional revision for delete idempotency test")
        first = _request(client, "DELETE", f"/documents/{doc_id}")
        assert first["status"] == 200
        assert first["payload"]["result"] == "voided"
        second = _request(client, "DELETE", f"/documents/{doc_id}")
        assert second["status"] == 200
        assert second["payload"]["result"] == "voided"


@pytest.mark.api_smoke
def test_delete_document_concurrent_requests():
    with httpx.Client(timeout=10) as client:
        doc_id, _ = _create_document(client)

    def _delete_doc() -> int:
        with httpx.Client(timeout=10) as delete_client:
            return _request(delete_client, "DELETE", f"/documents/{doc_id}")["status"]

    with futures.ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: _delete_doc(), range(2)))
    assert all(status in (200, 404) for status in statuses)
    assert 200 in statuses


@pytest.mark.api_smoke
def test_delete_document_not_found():
    """Test deleting a non-existent document returns 404."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, "DELETE", "/documents/999999")
        assert result["status"] == 404
