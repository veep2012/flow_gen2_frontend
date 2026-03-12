import httpx
import pytest

from tests.api.api.comments_test_helpers import (
    _get_second_test_user,
    _get_test_revision_id,
    _get_test_user,
    _request,
)


@pytest.mark.api_smoke
def test_written_comments_crud():
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, user_acronym = _get_test_user(client)

        created = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/comments",
            json={"comment_text": "Please verify section B-B."},
            headers={"X-User-Id": user_acronym},
        )
        assert created["status"] == 201
        comment_id = created["payload"]["id"]
        assert created["payload"]["rev_id"] == rev_id
        assert created["payload"]["user_id"] == user_id
        assert created["payload"]["comment_text"] == "Please verify section B-B."

        listed = _request(
            client,
            "GET",
            f"/documents/revisions/{rev_id}/comments",
            params={"user_id": user_id},
        )
        assert 200 <= listed["status"] < 300
        assert any(item.get("id") == comment_id for item in listed["payload"])

        deleted = _request(
            client,
            "DELETE",
            f"/documents/revisions/comments/{comment_id}",
            headers={"X-User-Id": user_acronym},
        )
        assert deleted["status"] == 204


@pytest.mark.api_smoke
def test_written_comments_validation():
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)

        missing_text = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/comments",
            json={},
        )
        assert missing_text["status"] == 422

        blank_text = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/comments",
            json={"comment_text": "   "},
        )
        assert blank_text["status"] == 400


@pytest.mark.api_smoke
def test_written_comments_require_session_identity():
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        denied = _request(
            client,
            "GET",
            f"/documents/revisions/{rev_id}/comments",
            headers={"X-User-Id": ""},
            auth=False,
        )
        assert denied["status"] == 401
        assert denied["payload"] == {"detail": "Authentication required"}


@pytest.mark.api_smoke
def test_written_comments_missing_revision():
    with httpx.Client(timeout=10) as client:
        _, user_acronym = _get_test_user(client)

        missing_rev = _request(
            client,
            "POST",
            "/documents/revisions/999999/comments",
            json={"comment_text": "missing revision"},
            headers={"X-User-Id": user_acronym},
        )
        assert missing_rev["status"] == 404


@pytest.mark.api_smoke
def test_written_comments_create_rejects_user_id_field():
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, user_acronym = _get_test_user(client)

        rejected = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/comments",
            json={"user_id": user_id, "comment_text": "should fail"},
            headers={"X-User-Id": user_acronym},
        )
        assert rejected["status"] == 422


@pytest.mark.api_smoke
def test_written_comments_delete_forbidden_non_author():
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        author_user_id, author_acronym = _get_test_user(client)
        other_user = _get_second_test_user(client, author_user_id)
        if other_user is None:
            pytest.skip("Need two users for forbidden written comment delete check")
        _, other_acronym = other_user

        created = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/comments",
            json={"comment_text": "author-only delete check"},
            headers={"X-User-Id": author_acronym},
        )
        assert created["status"] == 201
        comment_id = created["payload"]["id"]

        forbidden = _request(
            client,
            "DELETE",
            f"/documents/revisions/comments/{comment_id}",
            headers={"X-User-Id": other_acronym},
        )
        assert forbidden["status"] == 403

        _request(
            client,
            "DELETE",
            f"/documents/revisions/comments/{comment_id}",
            headers={"X-User-Id": author_acronym},
        )


@pytest.mark.api_smoke
def test_written_comments_update():
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        user_id, user_acronym = _get_test_user(client)

        created = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/comments",
            json={"comment_text": "initial text"},
            headers={"X-User-Id": user_acronym},
        )
        assert created["status"] == 201
        comment_id = created["payload"]["id"]

        updated = _request(
            client,
            "PUT",
            f"/documents/revisions/comments/{comment_id}",
            json={"comment_text": "updated text"},
            headers={"X-User-Id": user_acronym},
        )
        assert updated["status"] == 200
        assert updated["payload"]["id"] == comment_id
        assert updated["payload"]["comment_text"] == "updated text"

        _request(
            client,
            "DELETE",
            f"/documents/revisions/comments/{comment_id}",
            headers={"X-User-Id": user_acronym},
        )


@pytest.mark.api_smoke
def test_written_comments_update_forbidden_non_author():
    with httpx.Client(timeout=10) as client:
        rev_id = _get_test_revision_id(client)
        author_user_id, author_acronym = _get_test_user(client)
        other_user = _get_second_test_user(client, author_user_id)
        if other_user is None:
            pytest.skip("Need two non-superuser users for forbidden update check")
        _, other_acronym = other_user

        created = _request(
            client,
            "POST",
            f"/documents/revisions/{rev_id}/comments",
            json={"comment_text": "initial text"},
            headers={"X-User-Id": author_acronym},
        )
        assert created["status"] == 201
        comment_id = created["payload"]["id"]

        forbidden = _request(
            client,
            "PUT",
            f"/documents/revisions/comments/{comment_id}",
            json={"comment_text": "forbidden update"},
            headers={"X-User-Id": other_acronym},
        )
        assert forbidden["status"] == 403

        _request(
            client,
            "DELETE",
            f"/documents/revisions/comments/{comment_id}",
            headers={"X-User-Id": author_acronym},
        )
