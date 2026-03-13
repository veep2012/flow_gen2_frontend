import uuid

import httpx
import pytest

from tests.api.api.comments_test_helpers import (
    _get_second_test_user,
    _get_test_revision_id,
    _get_test_user,
    _request,
    _upload_base_file,
)


@pytest.mark.api_smoke
def test_files_commented_list():
    """Test listing commented files by file_id."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, "GET", "/files/commented/list", params={"file_id": 1})
        assert 200 <= result["status"] < 300
        assert isinstance(result["payload"], list)


@pytest.mark.api_smoke
def test_files_commented_list_with_user_filter():
    """Test listing commented files by file_id and user_id."""
    with httpx.Client(timeout=10) as client:
        result = _request(
            client, "GET", "/files/commented/list", params={"file_id": 1, "user_id": 1}
        )
        assert 200 <= result["status"] < 300
        assert isinstance(result["payload"], list)


@pytest.mark.api_smoke
def test_files_commented_list_missing_file_id():
    """Test listing commented files without file_id should fail."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, "GET", "/files/commented/list")
        assert result["status"] == 422


@pytest.mark.api_smoke
def test_files_commented_require_session_identity():
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "GET",
            "/files/commented/list",
            params={"file_id": 1},
            headers={"X-User-Id": ""},
            auth=False,
        )
        assert result["status"] == 401
        assert result["payload"] == {"detail": "Authentication required"}


@pytest.mark.api_smoke
def test_files_commented_insert_and_download():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, user_acronym = _get_test_user(client)
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
            data={"file_id": str(base_file["id"])},
            headers={"X-User-Id": user_acronym},
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
            client, "GET", "/files/commented/download", params={"id": commented_id}
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
        user_id, user_acronym = _get_test_user(client)
        base_file = _upload_base_file(client, rev_id, suffix, "pdf", "application/pdf")

        insert = _request(
            client,
            "POST",
            "/files/commented/",
            data={"file_id": str(base_file["id"])},
            headers={"X-User-Id": user_acronym},
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
            client, "GET", "/files/commented/download", params={"id": commented_id}
        )
        assert 200 <= downloaded["status"] < 300
        assert downloaded["content"] == base_file["content"]
        content_disposition = downloaded["headers"].get("content-disposition", "")
        assert insert["payload"]["filename"] in content_disposition

        _request(client, "DELETE", f"/files/commented/{commented_id}")
        _request(client, "DELETE", f"/files/{base_file['id']}")


@pytest.mark.api_smoke
def test_files_commented_replace():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, user_acronym = _get_test_user(client)
        base_file = _upload_base_file(client, rev_id, suffix, "pdf", "application/pdf")

        created = _request(
            client,
            "POST",
            "/files/commented/",
            files={
                "file": (
                    f"commented-{suffix}.pdf",
                    f"commented-original-{suffix}".encode(),
                    "application/pdf",
                )
            },
            data={"file_id": str(base_file["id"])},
            headers={"X-User-Id": user_acronym},
        )
        assert created["status"] == 201
        commented_id = created["payload"]["id"]
        old_s3_uid = created["payload"]["s3_uid"]

        replacement_content = f"commented-replaced-{suffix}".encode()
        replaced = _request(
            client,
            "POST",
            f"/files/commented/{commented_id}/replace",
            files={
                "file": (
                    f"commented-replaced-{suffix}.pdf",
                    replacement_content,
                    "application/pdf",
                )
            },
            headers={"X-User-Id": user_acronym},
        )
        assert replaced["status"] == 200
        assert replaced["payload"]["id"] == commented_id
        assert replaced["payload"]["file_id"] == base_file["id"]
        assert replaced["payload"]["user_id"] == user_id
        assert replaced["payload"]["s3_uid"] != old_s3_uid
        assert replaced["payload"]["mimetype"] == base_file["mimetype"]

        downloaded = _request(
            client, "GET", "/files/commented/download", params={"id": commented_id}
        )
        assert 200 <= downloaded["status"] < 300
        assert downloaded["content"] == replacement_content

        _request(client, "DELETE", f"/files/commented/{commented_id}")
        _request(client, "DELETE", f"/files/{base_file['id']}")


@pytest.mark.api_smoke
def test_files_commented_replace_forbidden_for_non_owner():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        owner_user_id, owner_acronym = _get_test_user(client)
        other_user = _get_second_test_user(client, owner_user_id)
        if other_user is None:
            pytest.skip("Need two non-superuser users for forbidden replace check")
        _, other_acronym = other_user
        base_file = _upload_base_file(client, rev_id, suffix, "pdf", "application/pdf")

        created = _request(
            client,
            "POST",
            "/files/commented/",
            files={
                "file": (
                    f"commented-{suffix}.pdf",
                    f"commented-original-{suffix}".encode(),
                    "application/pdf",
                )
            },
            data={"file_id": str(base_file["id"])},
            headers={"X-User-Id": owner_acronym},
        )
        assert created["status"] == 201
        commented_id = created["payload"]["id"]
        old_s3_uid = created["payload"]["s3_uid"]

        forbidden = _request(
            client,
            "POST",
            f"/files/commented/{commented_id}/replace",
            files={
                "file": (
                    f"commented-forbidden-{suffix}.pdf",
                    f"commented-forbidden-{suffix}".encode(),
                    "application/pdf",
                )
            },
            headers={"X-User-Id": other_acronym},
        )
        assert forbidden["status"] in {403, 404}

        listed = _request(
            client,
            "GET",
            "/files/commented/list",
            params={"file_id": base_file["id"], "user_id": owner_user_id},
            headers={"X-User-Id": owner_acronym},
        )
        assert listed["status"] == 200
        row = next(item for item in listed["payload"] if item["id"] == commented_id)
        assert row["s3_uid"] == old_s3_uid

        _request(
            client,
            "DELETE",
            f"/files/commented/{commented_id}",
            headers={"X-User-Id": owner_acronym},
        )
        _request(
            client, "DELETE", f"/files/{base_file['id']}", headers={"X-User-Id": owner_acronym}
        )


@pytest.mark.api_smoke
def test_files_commented_insert_duplicate():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, user_acronym = _get_test_user(client)
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
            data={"file_id": str(base_file["id"])},
            headers={"X-User-Id": user_acronym},
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
            data={"file_id": str(base_file["id"])},
            headers={"X-User-Id": user_acronym},
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
        result = _request(client, "GET", "/files/commented/download", params={"id": 999999})
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_files_commented_insert_missing_fields():
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "POST",
            "/files/commented/",
            files={"file": ("missing.pdf", b"content", "application/pdf")},
        )
        assert result["status"] == 422


@pytest.mark.api_smoke
def test_files_commented_insert_nonexistent_file():
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "POST",
            "/files/commented/",
            files={"file": ("missing.pdf", b"content", "application/pdf")},
            data={"file_id": "999999"},
        )
        assert result["status"] == 404


@pytest.mark.api_smoke
def test_files_commented_insert_mimetype_mismatch():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        _, user_acronym = _get_test_user(client)
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
            data={"file_id": str(base_file["id"])},
            headers={"X-User-Id": user_acronym},
        )
        assert mismatch["status"] in [400, 415]

        _request(client, "DELETE", f"/files/{base_file['id']}")


@pytest.mark.api_smoke
def test_files_commented_replace_nonexistent():
    with httpx.Client(timeout=10) as client:
        result = _request(
            client,
            "POST",
            "/files/commented/999999/replace",
            files={"file": ("replace.pdf", b"content", "application/pdf")},
        )
        assert result["status"] == 404
