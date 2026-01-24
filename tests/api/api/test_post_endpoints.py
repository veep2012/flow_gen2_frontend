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
    if response.content:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
    return {
        "status": response.status_code,
        "payload": payload,
        "duration_ms": duration_ms,
    }


def _ensure_list(result: dict) -> list:
    if result["status"] == 404:
        return []
    assert 200 <= result["status"] < 300, f"list failed: {result['status']}"
    assert isinstance(result["payload"], list), "payload is not a list"
    return result["payload"]


def _extract_first_id(items: list, keys: list[str]) -> int | None:
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in keys:
            value = item.get(key)
            if value is not None:
                return value
    return None


@pytest.mark.api_smoke
def test_post_lookups_areas_disciplines_projects_units_jobpacks():
    suffix = uuid.uuid4().hex[:8]
    with httpx.Client(timeout=10) as client:
        # Areas
        area_payload = {"area_name": f"Area {suffix}", "area_acronym": f"A{suffix[:2]}"}
        created = _request(client, "POST", "/lookups/areas", json=area_payload)
        assert 200 <= created["status"] < 300, f"areas insert failed: {created['status']}"
        area_id = created["payload"].get("area_id")
        updated = _request(
            client,
            "PUT",
            f"/lookups/areas/{area_id}",
            json={"area_name": f"Area {suffix} Updated"},
        )
        assert 200 <= updated["status"] < 300, f"areas update failed: {updated['status']}"
        deleted = _request(client, "DELETE", f"/lookups/areas/{area_id}")
        assert 200 <= deleted["status"] < 300, f"areas delete failed: {deleted['status']}"

        # Disciplines
        discipline_payload = {
            "discipline_name": f"Discipline {suffix}",
            "discipline_acronym": f"D{suffix[:2]}",
        }
        created = _request(client, "POST", "/lookups/disciplines", json=discipline_payload)
        assert 200 <= created["status"] < 300, f"disciplines insert failed: {created['status']}"
        discipline_id = created["payload"].get("discipline_id")
        updated = _request(
            client,
            "PUT",
            f"/lookups/disciplines/{discipline_id}",
            json={
                "discipline_name": f"Discipline {suffix} Updated",
            },
        )
        assert 200 <= updated["status"] < 300, f"disciplines update failed: {updated['status']}"
        deleted = _request(
            client,
            "DELETE",
            f"/lookups/disciplines/{discipline_id}",
        )
        assert 200 <= deleted["status"] < 300, f"disciplines delete failed: {deleted['status']}"

        # Projects
        project_payload = {"project_name": f"Project {suffix}"}
        created = _request(client, "POST", "/lookups/projects", json=project_payload)
        assert 200 <= created["status"] < 300, f"projects insert failed: {created['status']}"
        project_id = created["payload"].get("project_id")
        updated = _request(
            client,
            "PUT",
            f"/lookups/projects/{project_id}",
            json={"project_name": f"Project {suffix} Updated"},
        )
        assert 200 <= updated["status"] < 300, f"projects update failed: {updated['status']}"
        deleted = _request(client, "DELETE", f"/lookups/projects/{project_id}")
        assert 200 <= deleted["status"] < 300, f"projects delete failed: {deleted['status']}"

        # Units
        unit_payload = {"unit_name": f"Unit {suffix}"}
        created = _request(client, "POST", "/lookups/units", json=unit_payload)
        assert 200 <= created["status"] < 300, f"units insert failed: {created['status']}"
        unit_id = created["payload"].get("unit_id")
        updated = _request(
            client,
            "PUT",
            f"/lookups/units/{unit_id}",
            json={"unit_name": f"Unit {suffix} Updated"},
        )
        assert 200 <= updated["status"] < 300, f"units update failed: {updated['status']}"
        deleted = _request(client, "DELETE", f"/lookups/units/{unit_id}")
        assert 200 <= deleted["status"] < 300, f"units delete failed: {deleted['status']}"

        # Jobpacks
        jobpack_payload = {"jobpack_name": f"Jobpack {suffix}"}
        created = _request(client, "POST", "/lookups/jobpacks", json=jobpack_payload)
        assert 200 <= created["status"] < 300, f"jobpacks insert failed: {created['status']}"
        jobpack_id = created["payload"].get("jobpack_id")
        updated = _request(
            client,
            "PUT",
            f"/lookups/jobpacks/{jobpack_id}",
            json={"jobpack_name": f"Jobpack {suffix} Updated"},
        )
        assert 200 <= updated["status"] < 300, f"jobpacks update failed: {updated['status']}"
        deleted = _request(
            client,
            "DELETE",
            f"/lookups/jobpacks/{jobpack_id}",
        )
        assert 200 <= deleted["status"] < 300, f"jobpacks delete failed: {deleted['status']}"


@pytest.mark.api_smoke
def test_post_documents_metadata():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        disciplines = _ensure_list(_request(client, "GET", "/lookups/disciplines"))
        discipline_id = _extract_first_id(disciplines, ["discipline_id"])
        if discipline_id is None:
            pytest.skip("No discipline available for doc type insert")

        doc_type_payload = {
            "doc_type_name": f"DocType {suffix}",
            "ref_discipline_id": discipline_id,
            "doc_type_acronym": f"T{suffix[:2]}",
        }
        created = _request(client, "POST", "/documents/doc_types", json=doc_type_payload)
        assert 200 <= created["status"] < 300, f"doc types insert failed: {created['status']}"
        type_id = created["payload"].get("type_id")
        updated = _request(
            client,
            "PUT",
            f"/documents/doc_types/{type_id}",
            json={"doc_type_name": f"DocType {suffix} Updated"},
        )
        assert 200 <= updated["status"] < 300, f"doc types update failed: {updated['status']}"
        deleted = _request(client, "DELETE", f"/documents/doc_types/{type_id}")
        assert 200 <= deleted["status"] < 300, f"doc types delete failed: {deleted['status']}"

        milestone_payload = {"milestone_name": f"Milestone {suffix}", "progress": 10}
        created = _request(client, "POST", "/documents/doc_rev_milestones", json=milestone_payload)
        assert 200 <= created["status"] < 300, f"milestones insert failed: {created['status']}"
        milestone_id = created["payload"].get("milestone_id")
        updated = _request(
            client,
            "PUT",
            f"/documents/doc_rev_milestones/{milestone_id}",
            json={"progress": 20},
        )
        assert 200 <= updated["status"] < 300, f"milestones update failed: {updated['status']}"
        deleted = _request(
            client,
            "DELETE",
            f"/documents/doc_rev_milestones/{milestone_id}",
        )
        assert 200 <= deleted["status"] < 300, f"milestones delete failed: {deleted['status']}"

        revision_payload = {
            "rev_code_name": f"REV {suffix}",
            "rev_code_acronym": f"R{suffix[:2]}",
            "rev_description": f"Revision {suffix}",
            "percentage": 5,
        }
        created = _request(client, "POST", "/documents/revision_overview", json=revision_payload)
        assert (
            200 <= created["status"] < 300
        ), f"revision overview insert failed: {created['status']}"
        rev_code_id = created["payload"].get("rev_code_id")
        updated = _request(
            client,
            "PUT",
            f"/documents/revision_overview/{rev_code_id}",
            json={"percentage": 15},
        )
        assert (
            200 <= updated["status"] < 300
        ), f"revision overview update failed: {updated['status']}"
        deleted = _request(
            client,
            "DELETE",
            f"/documents/revision_overview/{rev_code_id}",
        )
        assert (
            200 <= deleted["status"] < 300
        ), f"revision overview delete failed: {deleted['status']}"

        behavior_payload = {
            "ui_behavior_name": f"Behavior {suffix}",
            "ui_behavior_file": f"Behavior{suffix}File.jsx",
        }
        created = _request(
            client, "POST", "/lookups/doc_rev_status_ui_behaviors", json=behavior_payload
        )
        assert 200 <= created["status"] < 300, f"ui behavior insert failed: {created['status']}"
        behavior_id = created["payload"].get("ui_behavior_id")
        assert behavior_id is not None, "ui behavior insert missing id"

        statuses = _ensure_list(_request(client, "GET", "/lookups/doc_rev_statuses"))
        final_status_id = _extract_first_id(
            [s for s in statuses if isinstance(s, dict) and s.get("final")],
            ["rev_status_id"],
        )
        if final_status_id is None:
            pytest.skip("No final status available for rev status insert")

        status_payload = {
            "rev_status_name": f"Status {suffix}",
            "ui_behavior_id": behavior_id,
            "next_rev_status_id": final_status_id,
            "revertible": True,
            "editable": True,
            "final": False,
            "start": False,
        }
        created = _request(client, "POST", "/lookups/doc_rev_statuses", json=status_payload)
        assert 200 <= created["status"] < 300, f"rev status insert failed: {created['status']}"
        status_id = created["payload"].get("rev_status_id")
        assert status_id is not None, "rev status insert missing id"
        updated = _request(
            client,
            "PUT",
            f"/lookups/doc_rev_statuses/{status_id}",
            json={"rev_status_name": f"Status {suffix} Updated"},
        )
        assert 200 <= updated["status"] < 300, f"rev status update failed: {updated['status']}"
        deleted = _request(client, "DELETE", f"/lookups/doc_rev_statuses/{status_id}")
        assert 200 <= deleted["status"] < 300, f"rev status delete failed: {deleted['status']}"
        deleted = _request(client, "DELETE", f"/lookups/doc_rev_status_ui_behaviors/{behavior_id}")
        assert 200 <= deleted["status"] < 300, f"ui behavior delete failed: {deleted['status']}"


@pytest.mark.api_smoke
def test_post_people_roles_persons_users_permissions():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        created_role = _request(
            client, "POST", "/people/roles", json={"role_name": f"Role {suffix}"}
        )
        assert 200 <= created_role["status"] < 300, f"roles insert failed: {created_role['status']}"
        role_id = created_role["payload"].get("role_id")
        updated = _request(
            client,
            "PUT",
            f"/people/roles/{role_id}",
            json={"role_name": f"Role {suffix} Updated"},
        )
        assert 200 <= updated["status"] < 300, f"roles update failed: {updated['status']}"

        created_person = _request(
            client,
            "POST",
            "/people/persons",
            json={"person_name": f"Person {suffix}", "photo_s3_uid": f"photo-{suffix}"},
        )
        assert (
            200 <= created_person["status"] < 300
        ), f"persons insert failed: {created_person['status']}"
        person_id = created_person["payload"].get("person_id")
        updated = _request(
            client,
            "PUT",
            f"/people/persons/{person_id}",
            json={"person_name": f"Person {suffix} Updated"},
        )
        assert 200 <= updated["status"] < 300, f"persons update failed: {updated['status']}"

        created_user = _request(
            client,
            "POST",
            "/people/users",
            json={"person_id": person_id, "user_acronym": f"U{suffix[:3]}", "role_id": role_id},
        )
        assert 200 <= created_user["status"] < 300, f"users insert failed: {created_user['status']}"
        user_id = created_user["payload"].get("user_id")
        updated = _request(
            client,
            "PUT",
            f"/people/users/{user_id}",
            json={"user_acronym": f"U{suffix[:3]}X"},
        )
        assert 200 <= updated["status"] < 300, f"users update failed: {updated['status']}"

        projects = _ensure_list(_request(client, "GET", "/lookups/projects"))
        disciplines = _ensure_list(_request(client, "GET", "/lookups/disciplines"))
        project_id = _extract_first_id(projects, ["project_id"])
        discipline_id = _extract_first_id(disciplines, ["discipline_id"])
        if project_id is None and discipline_id is None:
            pytest.skip("No project or discipline available for permissions")

        permission_payload = {"user_id": user_id}
        if project_id is not None:
            permission_payload["project_id"] = project_id
        else:
            permission_payload["discipline_id"] = discipline_id

        created_perm = _request(client, "POST", "/people/permissions", json=permission_payload)
        assert (
            200 <= created_perm["status"] < 300
        ), f"permissions insert failed: {created_perm['status']}"
        permission_id = created_perm["payload"].get("permission_id")
        update_payload = {
            "user_id": user_id,
        }
        if project_id is not None:
            update_payload["project_id"] = project_id
            update_payload["new_project_id"] = project_id
        else:
            update_payload["discipline_id"] = discipline_id
            update_payload["new_discipline_id"] = discipline_id
        updated = _request(
            client,
            "PUT",
            f"/people/permissions/{permission_id}",
            json=update_payload,
        )
        assert 200 <= updated["status"] < 300, f"permissions update failed: {updated['status']}"
        deleted = _request(client, "DELETE", f"/people/permissions/{permission_id}")
        assert 200 <= deleted["status"] < 300, f"permissions delete failed: {deleted['status']}"

        deleted_user = _request(client, "DELETE", f"/people/users/{user_id}")
        assert 200 <= deleted_user["status"] < 300, f"users delete failed: {deleted_user['status']}"

        deleted_person = _request(client, "DELETE", f"/people/persons/{person_id}")
        assert (
            200 <= deleted_person["status"] < 300
        ), f"persons delete failed: {deleted_person['status']}"

        deleted_role = _request(client, "DELETE", f"/people/roles/{role_id}")
        assert 200 <= deleted_role["status"] < 300, f"roles delete failed: {deleted_role['status']}"


@pytest.mark.api_smoke
def test_post_doc_rev_status_constraints():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        created = _request(
            client,
            "POST",
            "/lookups/doc_rev_status_ui_behaviors",
            json={
                "ui_behavior_name": f"Behavior {suffix} Constraints",
                "ui_behavior_file": f"Behavior{suffix}ConstraintsFile.jsx",
            },
        )
        assert 200 <= created["status"] < 300, f"ui behavior insert failed: {created['status']}"
        behavior_id = created["payload"].get("ui_behavior_id")

        invalid_final = _request(
            client,
            "POST",
            "/lookups/doc_rev_statuses",
            json={
                "rev_status_name": f"Status {suffix} Invalid Final",
                "ui_behavior_id": behavior_id,
                "next_rev_status_id": 99999,
                "revertible": False,
                "editable": False,
                "final": True,
            },
        )
        assert invalid_final["status"] == 400, "final status with next should be rejected"

        invalid_non_final = _request(
            client,
            "POST",
            "/lookups/doc_rev_statuses",
            json={
                "rev_status_name": f"Status {suffix} Missing Next",
                "ui_behavior_id": behavior_id,
                "next_rev_status_id": None,
                "revertible": True,
                "editable": True,
                "final": False,
            },
        )
        assert (
            invalid_non_final["status"] == 400
        ), "non-final status without next should be rejected"

        statuses = _ensure_list(_request(client, "GET", "/lookups/doc_rev_statuses"))
        final_status_id = _extract_first_id(
            [s for s in statuses if isinstance(s, dict) and s.get("final")],
            ["rev_status_id"],
        )
        if final_status_id is None:
            pytest.skip("No final status available for update constraint test")

        created = _request(
            client,
            "POST",
            "/lookups/doc_rev_statuses",
            json={
                "rev_status_name": f"Status {suffix} Update Guard",
                "ui_behavior_id": behavior_id,
                "next_rev_status_id": final_status_id,
                "revertible": True,
                "editable": True,
                "final": False,
                "start": False,
            },
        )
        assert created["status"] in (200, 201), "status insert failed for update tests"
        created_id = created["payload"].get("rev_status_id")
        assert created_id is not None, "status insert missing id for update tests"

        invalid_update_final = _request(
            client,
            "PUT",
            f"/lookups/doc_rev_statuses/{created_id}",
            json={"final": True},
        )
        assert (
            invalid_update_final["status"] == 400
        ), "final update without clearing next should be rejected"

        invalid_update_next = _request(
            client,
            "PUT",
            f"/lookups/doc_rev_statuses/{created_id}",
            json={"next_rev_status_id": None},
        )
        assert invalid_update_next["status"] == 400, "next cleared without final should be rejected"

        invalid_update_final_flags = _request(
            client,
            "PUT",
            f"/lookups/doc_rev_statuses/{created_id}",
            json={
                "final": True,
                "next_rev_status_id": None,
                "revertible": True,
                "editable": True,
            },
        )
        assert (
            invalid_update_final_flags["status"] == 400
        ), "final update with editable/revertible should be rejected"

        final_status = next((s for s in statuses if isinstance(s, dict) and s.get("final")), None)
        non_final_status = next(
            (s for s in statuses if isinstance(s, dict) and not s.get("final")), None
        )
        if final_status and non_final_status:
            invalid_final_add_next = _request(
                client,
                "PUT",
                f"/lookups/doc_rev_statuses/{final_status.get('rev_status_id')}",
                json={
                    "next_rev_status_id": non_final_status.get("rev_status_id"),
                },
            )
            assert (
                invalid_final_add_next["status"] == 400
            ), "final status should not accept a next status"

        has_final = any(isinstance(s, dict) and s.get("final") for s in statuses)
        valid_update = _request(
            client,
            "PUT",
            f"/lookups/doc_rev_statuses/{created_id}",
            json={
                "final": True,
                "next_rev_status_id": None,
                "revertible": False,
                "editable": False,
            },
        )
        if has_final:
            assert valid_update["status"] == 400, "second final status should be rejected"
        else:
            assert valid_update["status"] in (200, 201), "valid update failed"

        deleted = _request(client, "DELETE", f"/lookups/doc_rev_statuses/{created_id}")
        assert 200 <= deleted["status"] < 300, f"status delete failed: {deleted['status']}"

        deleted = _request(client, "DELETE", f"/lookups/doc_rev_status_ui_behaviors/{behavior_id}")
        assert 200 <= deleted["status"] < 300, f"ui behavior delete failed: {deleted['status']}"


@pytest.mark.api_smoke
def test_post_doc_rev_status_start_constraint():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        behaviors = _ensure_list(_request(client, "GET", "/lookups/doc_rev_status_ui_behaviors"))
        behavior_id = _extract_first_id(behaviors, ["ui_behavior_id"])
        if behavior_id is None:
            pytest.skip("No UI behavior available for start constraint test")

        statuses = _ensure_list(_request(client, "GET", "/lookups/doc_rev_statuses"))
        final_status_id = _extract_first_id(
            [s for s in statuses if isinstance(s, dict) and s.get("final")],
            ["rev_status_id"],
        )
        if final_status_id is None:
            pytest.skip("No final status available for start constraint test")

        has_start = any(isinstance(s, dict) and s.get("start") for s in statuses)
        created = _request(
            client,
            "POST",
            "/lookups/doc_rev_statuses",
            json={
                "rev_status_name": f"Status {suffix} Start",
                "ui_behavior_id": behavior_id,
                "next_rev_status_id": final_status_id,
                "revertible": True,
                "editable": True,
                "final": False,
                "start": True,
            },
        )
        if has_start:
            assert created["status"] == 400, "start status should be unique"
            return
        assert created["status"] in (200, 201), "start status insert failed"
        created_id = created["payload"].get("rev_status_id")
        assert created_id is not None, "start status insert missing id"

        duplicate = _request(
            client,
            "POST",
            "/lookups/doc_rev_statuses",
            json={
                "rev_status_name": f"Status {suffix} Start Duplicate",
                "ui_behavior_id": behavior_id,
                "next_rev_status_id": final_status_id,
                "revertible": True,
                "editable": True,
                "final": False,
                "start": True,
            },
        )
        assert duplicate["status"] == 400, "second start status should be rejected"

        deleted = _request(client, "DELETE", f"/lookups/doc_rev_statuses/{created_id}")
        assert 200 <= deleted["status"] < 300, f"start status delete failed: {deleted['status']}"


@pytest.mark.api_smoke
def test_post_documents_create_with_start_status():
    suffix = uuid.uuid4().hex[:8]
    with httpx.Client(timeout=10) as client:
        # Get required references
        areas = _ensure_list(_request(client, "GET", "/lookups/areas"))
        area_id = _extract_first_id(areas, ["area_id"])
        if area_id is None:
            pytest.skip("No area available for document create test")

        units = _ensure_list(_request(client, "GET", "/lookups/units"))
        unit_id = _extract_first_id(units, ["unit_id"])
        if unit_id is None:
            pytest.skip("No unit available for document create test")

        doc_types = _ensure_list(_request(client, "GET", "/documents/doc_types"))
        type_id = _extract_first_id(doc_types, ["type_id"])
        if type_id is None:
            pytest.skip("No doc type available for document create test")

        rev_codes = _ensure_list(_request(client, "GET", "/documents/revision_overview"))
        rev_code_id = _extract_first_id(rev_codes, ["rev_code_id"])
        if rev_code_id is None:
            pytest.skip("No revision code available for document create test")

        persons = _ensure_list(_request(client, "GET", "/people/persons"))
        person_id = _extract_first_id(persons, ["person_id"])
        if person_id is None:
            pytest.skip("No person available for document create test")

        statuses = _ensure_list(_request(client, "GET", "/lookups/doc_rev_statuses"))
        start_status = next(
            (s for s in statuses if isinstance(s, dict) and s.get("start") is True), None
        )
        if start_status is None:
            pytest.skip("No start status available for document create test")

        # Create a new document
        doc_payload = {
            "doc_name_unique": f"DOC-{suffix}",
            "title": f"Test Document {suffix}",
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
        created = _request(client, "POST", "/documents", json=doc_payload)
        assert created["status"] == 201, f"document create failed: {created['status']}"
        assert created["payload"].get("doc_id") is not None, "doc_id missing from response"
        assert created["payload"].get("doc_name_unique") == f"DOC-{suffix}"
        assert created["payload"].get("rev_current_id") is not None, "rev_current_id missing"
        assert (
            created["payload"].get("rev_status_id") == start_status["rev_status_id"]
        ), "revision status should be the start status"
        assert created["payload"].get("rev_seq_num") == 1, "initial revision seq_num should be 1"

        # Clean up: delete the document
        # Note: Document deletion endpoint may not exist, so we'll skip cleanup
        # If there's a delete endpoint, uncomment the following line:
        # _request(client, "DELETE", f"/documents/{created['payload']['doc_id']}")


@pytest.mark.api_smoke
def test_documents_update_rejects_doc_id_in_body():
    suffix = uuid.uuid4().hex[:8]
    with httpx.Client(timeout=10) as client:
        areas = _ensure_list(_request(client, "GET", "/lookups/areas"))
        area_id = _extract_first_id(areas, ["area_id"])
        if area_id is None:
            pytest.skip("No area available for document update id test")

        units = _ensure_list(_request(client, "GET", "/lookups/units"))
        unit_id = _extract_first_id(units, ["unit_id"])
        if unit_id is None:
            pytest.skip("No unit available for document update id test")

        doc_types = _ensure_list(_request(client, "GET", "/documents/doc_types"))
        type_id = _extract_first_id(doc_types, ["type_id"])
        if type_id is None:
            pytest.skip("No doc type available for document update id test")

        rev_codes = _ensure_list(_request(client, "GET", "/documents/revision_overview"))
        rev_code_id = _extract_first_id(rev_codes, ["rev_code_id"])
        if rev_code_id is None:
            pytest.skip("No revision code available for document update id test")

        persons = _ensure_list(_request(client, "GET", "/people/persons"))
        person_id = _extract_first_id(persons, ["person_id"])
        if person_id is None:
            pytest.skip("No person available for document update id test")

        doc_payload = {
            "doc_name_unique": f"DOC-ID-{suffix}",
            "title": f"Test Document {suffix}",
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
        created = _request(client, "POST", "/documents", json=doc_payload)
        assert created["status"] == 201, f"document create failed: {created['status']}"
        doc_id = created["payload"].get("doc_id")
        assert doc_id is not None, "doc_id missing from response"

        updated = _request(
            client,
            "PUT",
            f"/documents/{doc_id}",
            json={"doc_id": doc_id, "title": f"Test Document {suffix} Updated"},
        )
        assert updated["status"] == 422
