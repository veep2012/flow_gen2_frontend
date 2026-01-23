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
    }


def _ensure_list(result: dict) -> list:
    if result["status"] == 404:
        return []
    assert 200 <= result["status"] < 300, f"list failed: {result['status']}"
    return result["payload"]


def _pick_id(items: list, key: str) -> int | None:
    for item in items:
        if isinstance(item, dict) and item.get(key) is not None:
            return item[key]
    return None


@pytest.mark.api_smoke
def test_audit_fields_document_and_revision():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        areas = _ensure_list(_request(client, "GET", "/lookups/areas"))
        units = _ensure_list(_request(client, "GET", "/lookups/units"))
        projects = _ensure_list(_request(client, "GET", "/lookups/projects"))
        doc_types = _ensure_list(_request(client, "GET", "/documents/doc_types"))
        rev_codes = _ensure_list(_request(client, "GET", "/documents/revision_overview"))
        people = _ensure_list(_request(client, "GET", "/people/persons"))

        area_id = _pick_id(areas, "area_id")
        unit_id = _pick_id(units, "unit_id")
        project_id = _pick_id(projects, "project_id")
        type_id = _pick_id(doc_types, "type_id")
        rev_code_id = _pick_id(rev_codes, "rev_code_id")
        person_id = _pick_id(people, "person_id")

        if None in (area_id, unit_id, project_id, type_id, rev_code_id, person_id):
            pytest.skip("Missing reference data for audit field test")

        payload = {
            "doc_name_unique": f"DOC-AUD-{suffix}",
            "title": f"Audit Document {suffix}",
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

        created = _request(
            client,
            "POST",
            "/documents",
            headers={"X-User-Id": "1"},
            json=payload,
        )
        assert 200 <= created["status"] < 300, f"document create failed: {created['status']}"
        doc = created["payload"]
        assert doc.get("created_by") == 1
        assert doc.get("updated_by") == 1
        assert doc.get("created_at") is not None
        assert doc.get("updated_at") is not None

        doc_id = doc.get("doc_id")
        assert doc_id is not None

        updated = _request(
            client,
            "PUT",
            f"/documents/{doc_id}",
            headers={"X-User-Id": "2"},
            json={"doc_id": doc_id, "title": f"Audit Document Updated {suffix}"},
        )
        assert 200 <= updated["status"] < 300, f"document update failed: {updated['status']}"
        updated_doc = updated["payload"]
        assert updated_doc.get("created_by") == 1
        assert updated_doc.get("updated_by") == 2
        assert updated_doc.get("updated_at") is not None
        assert updated_doc.get("updated_at") != doc.get("updated_at")

        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert 200 <= revisions["status"] < 300
        assert revisions["payload"], "expected at least one revision"
        rev = revisions["payload"][0]
        assert rev.get("created_by") == 1
        assert rev.get("updated_by") == 1
        assert rev.get("created_at") is not None
        assert rev.get("updated_at") is not None

        rev_id = rev.get("rev_id")
        assert rev_id is not None
        rev_update = _request(
            client,
            "PUT",
            f"/documents/revisions/{rev_id}",
            headers={"X-User-Id": "3"},
            json={"rev_id": rev_id, "transmital_current_revision": f"TR-AUD-{suffix}"},
        )
        assert 200 <= rev_update["status"] < 300
        rev_out = rev_update["payload"]
        assert rev_out.get("updated_by") == 3
        assert rev_out.get("updated_at") is not None


@pytest.mark.api_smoke
def test_audit_fields_files_and_commented():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        projects = _ensure_list(_request(client, "GET", "/lookups/projects"))
        project_id = _pick_id(projects, "project_id")
        if project_id is None:
            pytest.skip("No projects available for files audit test")

        docs = _request(client, "GET", "/documents", params={"project_id": project_id})
        if not (200 <= docs["status"] < 300) or not docs["payload"]:
            pytest.skip("No documents available for files audit test")
        doc_id = _pick_id(docs["payload"], "doc_id")
        if doc_id is None:
            pytest.skip("No doc_id available for files audit test")

        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for files audit test")
        rev_id = revisions["payload"][0].get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for files audit test")

        file_payload = {
            "file": (f"audit-{suffix}.pdf", b"%PDF-1.4\n%AUDIT\n", "application/pdf"),
        }
        created_file = _request(
            client,
            "POST",
            "/files/",
            headers={"X-User-Id": "1"},
            files=file_payload,
            data={"rev_id": str(rev_id)},
        )
        assert 200 <= created_file["status"] < 300, f"file create failed: {created_file['status']}"
        file_row = created_file["payload"]
        assert file_row.get("created_by") == 1
        assert file_row.get("updated_by") == 1
        assert file_row.get("created_at") is not None
        assert file_row.get("updated_at") is not None

        file_id = file_row.get("id") or file_row.get("file_id")
        if file_id is None:
            pytest.skip("No file_id returned for files audit test")

        commented_payload = {
            "file": (f"commented-{suffix}.pdf", b"%PDF-1.4\n%COMMENTED\n", "application/pdf"),
        }
        created_commented = _request(
            client,
            "POST",
            "/files/commented/",
            headers={"X-User-Id": "2"},
            files=commented_payload,
            data={"file_id": str(file_id), "user_id": "1"},
        )
        assert (
            200 <= created_commented["status"] < 300
        ), f"commented file create failed: {created_commented['status']}"
        commented_row = created_commented["payload"]
        assert commented_row.get("created_by") == 2
        assert commented_row.get("updated_by") == 2
        assert commented_row.get("created_at") is not None
        assert commented_row.get("updated_at") is not None
