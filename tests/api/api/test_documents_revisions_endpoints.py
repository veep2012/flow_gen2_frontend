import os
import time
import uuid

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

_DEFAULT_TEST_USER_ACRONYM = os.getenv("TEST_USER_ACRONYM", "FDQC")


def _build_base_url() -> str:
    base = os.getenv("API_BASE", "http://localhost:4175").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{base}{prefix}"


def _build_admin_database_url() -> str:
    explicit_admin = os.getenv("TEST_DB_ADMIN_URL")
    if explicit_admin:
        return explicit_admin

    user = os.getenv("TEST_DB_ADMIN_USER", "postgres")
    password = os.getenv("TEST_DB_ADMIN_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    db_name = os.getenv("TEST_DB_NAME", os.getenv("POSTGRES_DB", "flow_db_test"))
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


def _merge_default_auth(kwargs: dict) -> dict:
    merged = dict(kwargs)
    if merged.pop("auth", True):
        headers = dict(merged.get("headers") or {})
        headers.setdefault("X-User-Id", _DEFAULT_TEST_USER_ACRONYM)
        merged["headers"] = headers
    return merged


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    url = f"{_build_base_url()}{path}"
    start = time.perf_counter()
    response = client.request(method, url, **_merge_default_auth(kwargs))
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


def _ensure_file_for_revision(client: httpx.Client, rev_id: int) -> None:
    listed = _request(client, "GET", "/files", params={"rev_id": rev_id})
    if 200 <= listed["status"] < 300 and listed["payload"]:
        return
    suffix = uuid.uuid4().hex[:6]
    upload = _request(
        client,
        "POST",
        "/files/",
        files={"file": (f"rev-{rev_id}-{suffix}.pdf", b"test", "application/pdf")},
        data={"rev_id": str(rev_id)},
    )
    assert 200 <= upload["status"] < 300, f"file upload failed: {upload['status']}"


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


def _get_statuses(client: httpx.Client) -> list[dict] | None:
    result = _request(client, "GET", "/lookups/doc_rev_statuses")
    if not (200 <= result["status"] < 300):
        return None
    if not isinstance(result["payload"], list):
        return None
    return result["payload"]


def _get_start_status_id(client: httpx.Client) -> int | None:
    statuses = _get_statuses(client)
    if not statuses:
        return None
    for status in statuses:
        if status.get("start"):
            return status.get("rev_status_id")
    return None


def _get_final_status_id(client: httpx.Client) -> int | None:
    statuses = _get_statuses(client)
    if not statuses:
        return None
    for status in statuses:
        if status.get("final"):
            return status.get("rev_status_id")
    return None


def _get_revision_overview_steps(client: httpx.Client) -> list[dict] | None:
    result = _request(client, "GET", "/documents/revision_overview")
    if not (200 <= result["status"] < 300):
        return None
    if not isinstance(result["payload"], list):
        return None
    return result["payload"]


def _get_person_id(client: httpx.Client) -> int | None:
    result = _request(client, "GET", "/people/persons")
    if not (200 <= result["status"] < 300):
        return None
    return _extract_first_id(result["payload"], ["person_id"])


def _build_document_create_payload(
    client: httpx.Client,
    *,
    prefix: str,
    rev_code_id: int | None = None,
) -> dict:
    areas = _request(client, "GET", "/lookups/areas")
    units = _request(client, "GET", "/lookups/units")
    doc_types = _request(client, "GET", "/documents/doc_types")
    person_id = _get_person_id(client)
    project_id = _get_project_id(client)
    area_id = _extract_first_id(areas["payload"], ["area_id"]) if areas["status"] < 300 else None
    unit_id = _extract_first_id(units["payload"], ["unit_id"]) if units["status"] < 300 else None
    type_id = (
        _extract_first_id(doc_types["payload"], ["type_id"]) if doc_types["status"] < 300 else None
    )
    if None in (area_id, unit_id, type_id, person_id):
        pytest.skip("Missing reference data for document creation test")

    suffix = uuid.uuid4().hex[:6].upper()
    payload = {
        "doc_name_unique": f"{prefix}-{suffix}",
        "title": f"Revision Test {suffix}",
        "project_id": project_id,
        "type_id": type_id,
        "area_id": area_id,
        "unit_id": unit_id,
        "rev_author_id": person_id,
        "rev_originator_id": person_id,
        "rev_modifier_id": person_id,
        "transmital_current_revision": f"TR-{suffix}",
        "planned_start_date": "2024-01-01T00:00:00Z",
        "planned_finish_date": "2024-12-31T23:59:59Z",
    }
    if rev_code_id is not None:
        payload["rev_code_id"] = rev_code_id
    return payload


def _create_document_with_revision(
    client: httpx.Client,
    *,
    prefix: str,
    rev_code_id: int | None = None,
) -> tuple[int, dict]:
    created = _request(
        client,
        "POST",
        "/documents",
        json=_build_document_create_payload(client, prefix=prefix, rev_code_id=rev_code_id),
    )
    assert created["status"] == 201
    doc_id = created["payload"]["doc_id"]
    revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
    assert revisions["status"] == 200
    assert revisions["payload"]
    return doc_id, revisions["payload"][0]


def _mark_revision_final_and_sync_doc(doc_id: int, rev_id: int, final_status_id: int) -> None:
    engine = create_engine(_build_admin_database_url())
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE core.doc_revision
                SET rev_status_id = :final_status_id
                WHERE rev_id = :rev_id
                """
            ),
            {"final_status_id": final_status_id, "rev_id": rev_id},
        )
        conn.execute(
            text(
                """
                UPDATE core.doc
                SET rev_actual_id = :rev_id,
                    rev_current_id = :rev_id
                WHERE doc_id = :doc_id
                """
            ),
            {"doc_id": doc_id, "rev_id": rev_id},
        )


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
def test_documents_revisions_require_session_identity():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for auth guard test")

        result = _request(
            client,
            "GET",
            f"/documents/{doc_id}/revisions",
            headers={"X-User-Id": ""},
            auth=False,
        )
        assert result["status"] == 401
        assert result["payload"] == {"detail": "Authentication required"}


@pytest.mark.api_smoke
def test_documents_revisions_update():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for revisions update test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for revisions update test")
        statuses = _get_statuses(client)
        if not statuses:
            pytest.skip("No statuses available for revisions update test")
        status_map = {
            status["rev_status_id"]: status for status in statuses if "rev_status_id" in status
        }
        candidate = None
        for rev in revisions["payload"]:
            status = status_map.get(rev.get("rev_status_id"))
            if status and status.get("final"):
                continue
            candidate = rev
            break
        if candidate is None:
            pytest.skip("No non-final revision available for revisions update test")
        rev_id = candidate.get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for revisions update test")
        updated = _request(
            client,
            "PUT",
            f"/documents/revisions/{rev_id}",
            json={
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
        updated = _request(client, "PUT", f"/documents/revisions/{rev_id}", json={})
        assert updated["status"] == 400


@pytest.mark.api_smoke
def test_documents_revisions_update_missing_revision():
    with httpx.Client(timeout=10) as client:
        updated = _request(
            client,
            "PUT",
            "/documents/revisions/999999",
            json={"transmital_current_revision": "TR-MISSING"},
        )
        assert updated["status"] == 404


@pytest.mark.api_smoke
def test_documents_revisions_update_rejects_status_change():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for revisions update status test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for revisions update status test")
        rev_id = revisions["payload"][0].get("rev_id")
        rev_status_id = revisions["payload"][0].get("rev_status_id")
        if rev_id is None or rev_status_id is None:
            pytest.skip("No revision status available for status update rejection test")
        updated = _request(
            client,
            "PUT",
            f"/documents/revisions/{rev_id}",
            json={"rev_status_id": rev_status_id},
        )
        assert updated["status"] == 422


@pytest.mark.api_smoke
def test_documents_revisions_update_rejects_rev_code_change():
    with httpx.Client(timeout=10) as client:
        _, revision = _create_document_with_revision(client, prefix="DOC-REV-UPD")
        rev_id = revision["rev_id"]
        updated = _request(
            client,
            "PUT",
            f"/documents/revisions/{rev_id}",
            json={"rev_code_id": revision["rev_code_id"]},
        )
        assert updated["status"] == 422


@pytest.mark.api_smoke
def test_documents_update_rejects_workflow_managed_revision_pointers():
    with httpx.Client(timeout=10) as client:
        doc_id, base_revision = _create_document_with_revision(client, prefix="DOC-UPD-PTR")
        updated = _request(
            client,
            "PUT",
            f"/documents/{doc_id}",
            json={
                "rev_actual_id": base_revision["rev_id"],
                "rev_current_id": base_revision["rev_id"],
            },
        )
        assert updated["status"] == 422


@pytest.mark.api_smoke
def test_documents_create_defaults_initial_revision_code_to_start():
    with httpx.Client(timeout=10) as client:
        overview = _get_revision_overview_steps(client)
        if not overview:
            pytest.skip("No revision overview configured")
        start_step = next((step for step in overview if step.get("start") is True), None)
        if start_step is None:
            pytest.skip("No start revision overview step configured")

        doc_id, revision = _create_document_with_revision(client, prefix="DOC-REV-DEFAULT")
        assert revision["doc_id"] == doc_id
        assert revision["rev_code_id"] == start_step["rev_code_id"]


@pytest.mark.api_smoke
def test_documents_revisions_supersede():
    with httpx.Client(timeout=10) as client:
        doc_id, base_revision = _create_document_with_revision(client, prefix="DOC-REV-SUPERSEDE")
        statuses = _get_statuses(client)
        if not statuses:
            pytest.skip("No statuses available for supersede test")
        status_map = {
            status["rev_status_id"]: status for status in statuses if "rev_status_id" in status
        }
        current_status = status_map.get(base_revision["rev_status_id"])
        if current_status is None or current_status.get("next_rev_status_id") is None:
            pytest.skip("No non-final successor status available for supersede test")
        _ensure_file_for_revision(client, base_revision["rev_id"])
        advanced = _request(
            client,
            "POST",
            f"/documents/revisions/{base_revision['rev_id']}/status-transitions",
            json={"direction": "forward"},
        )
        assert advanced["status"] == 200
        advanced_payload = advanced["payload"]
        advanced_status = status_map.get(advanced_payload["rev_status_id"])
        if advanced_status is None or advanced_status.get("final"):
            pytest.skip("Need a non-final non-start source revision for supersede test")
        payload = {
            "rev_author_id": advanced_payload["rev_author_id"],
            "rev_originator_id": advanced_payload["rev_originator_id"],
            "rev_modifier_id": advanced_payload["rev_modifier_id"],
            "transmital_current_revision": f"TR-SUP-{doc_id}",
            "planned_start_date": advanced_payload["planned_start_date"],
            "planned_finish_date": advanced_payload["planned_finish_date"],
        }
        created = _request(
            client,
            "POST",
            f"/documents/revisions/{advanced_payload['rev_id']}/supersede",
            json=payload,
        )
        assert created["status"] == 200
        assert created["payload"]["doc_id"] == doc_id
        assert created["payload"]["seq_num"] == advanced_payload["seq_num"] + 1
        assert created["payload"]["rev_code_id"] == advanced_payload["rev_code_id"]
        start_status_id = _get_start_status_id(client)
        if start_status_id is not None:
            assert created["payload"]["rev_status_id"] == start_status_id

        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert revisions["status"] == 200
        prior_revision = next(
            (
                rev
                for rev in revisions["payload"]
                if rev.get("rev_id") == advanced_payload["rev_id"]
            ),
            None,
        )
        assert prior_revision is not None
        assert prior_revision["superseded"] is True


@pytest.mark.api_smoke
def test_documents_revisions_supersede_rejects_final_source():
    with httpx.Client(timeout=10) as client:
        final_status_id = _get_final_status_id(client)
        if final_status_id is None:
            pytest.skip("No final status configured")
        doc_id, revision = _create_document_with_revision(client, prefix="DOC-REV-SUPERSEDE-FINAL")
        _mark_revision_final_and_sync_doc(doc_id, revision["rev_id"], final_status_id)
        payload = {
            "rev_author_id": revision["rev_author_id"],
            "rev_originator_id": revision["rev_originator_id"],
            "rev_modifier_id": revision["rev_modifier_id"],
            "transmital_current_revision": f"TR-SUP-FINAL-{doc_id}",
            "planned_start_date": revision["planned_start_date"],
            "planned_finish_date": revision["planned_finish_date"],
        }
        created = _request(
            client,
            "POST",
            f"/documents/revisions/{revision['rev_id']}/supersede",
            json=payload,
        )
        assert created["status"] == 409


@pytest.mark.api_smoke
def test_documents_revisions_overview_transition_from_final():
    with httpx.Client(timeout=10) as client:
        overview = _get_revision_overview_steps(client)
        start_status_id = _get_start_status_id(client)
        final_status_id = _get_final_status_id(client)
        if not overview or start_status_id is None or final_status_id is None:
            pytest.skip("Revision overview or statuses are unavailable")

        start_step = next((step for step in overview if step.get("start") is True), None)
        if start_step is None or start_step.get("next_rev_code_id") is None:
            pytest.skip("No transitionable start revision overview step available")

        doc_id, revision = _create_document_with_revision(
            client, prefix="DOC-REV-OVERVIEW", rev_code_id=start_step["rev_code_id"]
        )
        source_rev_id = revision["rev_id"]
        _mark_revision_final_and_sync_doc(doc_id, source_rev_id, final_status_id)

        transitioned = _request(
            client,
            "POST",
            f"/documents/revisions/{source_rev_id}/overview-transition",
            json={},
        )
        assert transitioned["status"] == 200
        assert transitioned["payload"]["doc_id"] == doc_id
        assert transitioned["payload"]["seq_num"] == revision["seq_num"] + 1
        assert transitioned["payload"]["rev_code_id"] == start_step["next_rev_code_id"]
        assert transitioned["payload"]["rev_status_id"] == start_status_id

        engine = create_engine(_build_admin_database_url())
        with engine.begin() as conn:
            doc_row = (
                conn.execute(
                    text(
                        """
                    SELECT rev_actual_id, rev_current_id
                    FROM core.doc
                    WHERE doc_id = :doc_id
                    """
                    ),
                    {"doc_id": doc_id},
                )
                .mappings()
                .one()
            )
            source_row = (
                conn.execute(
                    text(
                        """
                    SELECT rev_code_id, rev_status_id
                    FROM core.doc_revision
                    WHERE rev_id = :rev_id
                    """
                    ),
                    {"rev_id": source_rev_id},
                )
                .mappings()
                .one()
            )

        assert doc_row["rev_actual_id"] == source_rev_id
        assert doc_row["rev_current_id"] == transitioned["payload"]["rev_id"]
        assert source_row["rev_code_id"] == start_step["rev_code_id"]
        assert source_row["rev_status_id"] == final_status_id


@pytest.mark.api_smoke
def test_documents_revisions_overview_transition_from_non_start_code():
    with httpx.Client(timeout=10) as client:
        overview = _get_revision_overview_steps(client)
        final_status_id = _get_final_status_id(client)
        if not overview or final_status_id is None:
            pytest.skip("Revision overview or final status unavailable")

        candidate_step = next(
            (
                step
                for step in overview
                if not step.get("start") and step.get("next_rev_code_id") is not None
            ),
            None,
        )
        if candidate_step is None:
            pytest.skip("No non-start revision overview step available")

        doc_id, revision = _create_document_with_revision(
            client, prefix="DOC-REV-SKIP", rev_code_id=candidate_step["rev_code_id"]
        )
        assert revision["rev_code_id"] == candidate_step["rev_code_id"]

        _mark_revision_final_and_sync_doc(doc_id, revision["rev_id"], final_status_id)
        transitioned = _request(
            client,
            "POST",
            f"/documents/revisions/{revision['rev_id']}/overview-transition",
            json={},
        )
        assert transitioned["status"] == 200
        assert transitioned["payload"]["rev_code_id"] == candidate_step["next_rev_code_id"]


@pytest.mark.api_smoke
def test_documents_revisions_overview_transition_rejects_non_final_source():
    with httpx.Client(timeout=10) as client:
        _, revision = _create_document_with_revision(client, prefix="DOC-REV-NONFINAL")
        transitioned = _request(
            client,
            "POST",
            f"/documents/revisions/{revision['rev_id']}/overview-transition",
            json={},
        )
        assert transitioned["status"] == 409


@pytest.mark.api_smoke
def test_documents_revisions_status_transition_forward():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for status transition test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for status transition test")
        statuses = _get_statuses(client)
        if not statuses:
            pytest.skip("No statuses available for status transition test")
        status_map = {
            status["rev_status_id"]: status for status in statuses if "rev_status_id" in status
        }
        candidate = None
        for rev in revisions["payload"]:
            status = status_map.get(rev.get("rev_status_id"))
            if not status:
                continue
            if rev.get("superseded"):
                continue
            if status.get("final") or status.get("next_rev_status_id") is None:
                continue
            candidate = (rev, status)
            break
        if candidate is None:
            pytest.skip("No non-final revision available for forward transition test")
        rev, status = candidate
        rev_id = rev["rev_id"]
        next_id = status["next_rev_status_id"]
        _ensure_file_for_revision(client, rev_id)
        result = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/status-transitions",
            json={"direction": "forward"},
        )
        assert 200 <= result["status"] < 300
        assert result["payload"]["rev_id"] == rev_id
        assert result["payload"]["rev_status_id"] == next_id


@pytest.mark.api_smoke
def test_documents_revisions_status_transition_back():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for status transition back test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for status transition back test")
        statuses = _get_statuses(client)
        if not statuses:
            pytest.skip("No statuses available for status transition back test")
        status_map = {
            status["rev_status_id"]: status for status in statuses if "rev_status_id" in status
        }
        prev_map = {}
        for status in statuses:
            next_id = status.get("next_rev_status_id")
            if next_id is not None:
                prev_map[next_id] = status.get("rev_status_id")
        candidate = None
        for rev in revisions["payload"]:
            status = status_map.get(rev.get("rev_status_id"))
            if not status:
                continue
            if rev.get("superseded"):
                continue
            predecessor_count = sum(
                1
                for candidate_status in statuses
                if candidate_status.get("next_rev_status_id") == status.get("rev_status_id")
            )
            prev_id = prev_map.get(status.get("rev_status_id"))
            if status.get("start") or not status.get("revertible"):
                continue
            if prev_id is None:
                continue
            if predecessor_count != 1:
                continue
            candidate = (rev, prev_id)
            break
        if candidate is None:
            pytest.skip("No revertible revision available for back transition test")
        rev, prev_id = candidate
        rev_id = rev["rev_id"]
        result = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/status-transitions",
            json={"direction": "back"},
        )
        assert 200 <= result["status"] < 300
        assert result["payload"]["rev_id"] == rev_id
        assert result["payload"]["rev_status_id"] == prev_id


@pytest.mark.api_smoke
def test_documents_revisions_status_transition_invalid_direction():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for invalid direction test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for invalid direction test")
        rev_id = revisions["payload"][0].get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for invalid direction test")
        result = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/status-transitions",
            json={"direction": "sideways"},
        )
        assert result["status"] == 422


@pytest.mark.api_smoke
def test_documents_revisions_status_transition_already_final():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for final status test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for final status test")
        statuses = _get_statuses(client)
        if not statuses:
            pytest.skip("No statuses available for final status test")
        status_map = {
            status["rev_status_id"]: status for status in statuses if "rev_status_id" in status
        }
        candidate = None
        for rev in revisions["payload"]:
            status = status_map.get(rev.get("rev_status_id"))
            if not status:
                continue
            if status.get("final") or status.get("next_rev_status_id") is None:
                candidate = rev
                break
        if candidate is None:
            pytest.skip("No final revision available for final status test")
        rev_id = candidate.get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for final status test")
        result = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/status-transitions",
            json={"direction": "forward"},
        )
        assert result["status"] == 409


@pytest.mark.api_smoke
def test_documents_revisions_status_transition_not_revertible():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for not revertible test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for not revertible test")
        statuses = _get_statuses(client)
        if not statuses:
            pytest.skip("No statuses available for not revertible test")
        status_map = {
            status["rev_status_id"]: status for status in statuses if "rev_status_id" in status
        }
        candidate = None
        for rev in revisions["payload"]:
            status = status_map.get(rev.get("rev_status_id"))
            if not status:
                continue
            if status.get("start"):
                continue
            if status.get("revertible") is False:
                candidate = rev
                break
        if candidate is None:
            pytest.skip("No non-revertible revision available for back transition test")
        rev_id = candidate.get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for not revertible test")
        result = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/status-transitions",
            json={"direction": "back"},
        )
        assert result["status"] == 409


@pytest.mark.api_smoke
def test_documents_revisions_status_transition_already_start():
    with httpx.Client(timeout=10) as client:
        doc_id = _get_doc_id(client)
        if doc_id is None:
            pytest.skip("No document available for start status test")
        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for start status test")
        statuses = _get_statuses(client)
        if not statuses:
            pytest.skip("No statuses available for start status test")
        start_status_ids = {
            status["rev_status_id"]
            for status in statuses
            if status.get("start") is True and "rev_status_id" in status
        }
        candidate = next(
            (
                rev
                for rev in revisions["payload"]
                if rev.get("rev_status_id") in start_status_ids and not rev.get("superseded")
            ),
            None,
        )
        if candidate is None:
            pytest.skip("No start-status revision available for start status test")
        rev_id = candidate.get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for start status test")
        result = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/status-transitions",
            json={"direction": "back"},
        )
        assert result["status"] == 409


@pytest.mark.api_smoke
def test_documents_revisions_status_graph_rejects_ambiguous_predecessor():
    engine = create_engine(_build_admin_database_url())
    token = uuid.uuid4().hex[:6].upper()
    with engine.begin() as conn:
        target_status_id = conn.execute(
            text(
                """
                SELECT rev_status_id
                FROM ref.doc_rev_statuses
                WHERE start IS NOT TRUE
                  AND final IS NOT TRUE
                ORDER BY rev_status_id
                LIMIT 1
                """
            )
        ).scalar_one()
        ui_behavior_id = conn.execute(
            text(
                """
                SELECT ui_behavior_id
                FROM ref.doc_rev_status_ui_behaviors
                ORDER BY ui_behavior_id
                LIMIT 1
                """
            )
        ).scalar_one()

        with pytest.raises(DBAPIError):
            with conn.begin_nested():
                conn.execute(
                    text(
                        """
                        INSERT INTO ref.doc_rev_statuses (
                            rev_status_name,
                            ui_behavior_id,
                            next_rev_status_id,
                            revertible,
                            editable,
                            final,
                            start
                        ) VALUES (
                            :rev_status_name,
                            :ui_behavior_id,
                            :next_rev_status_id,
                            TRUE,
                            TRUE,
                            FALSE,
                            FALSE
                        )
                        """
                    ),
                    {
                        "rev_status_name": f"QA-AMB-{token}",
                        "ui_behavior_id": ui_behavior_id,
                        "next_rev_status_id": target_status_id,
                    },
                )
