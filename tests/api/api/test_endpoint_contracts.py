import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import jwt
import pytest

from api.schemas.distribution_lists import DistributionListOut
from api.schemas.documents import DocOut, DocRevisionOut
from api.schemas.files import FileOut
from api.schemas.notifications import NotificationOut
from api.schemas.people import UserOut

_DEFAULT_TEST_USER_ACRONYM = os.getenv("TEST_USER_ACRONYM", "FDQC")
_TEST_JWT_ISSUER = os.getenv("AUTH_JWT_ISSUER_URL", "https://flow-ci.invalid/issuer")
_TEST_JWT_AUDIENCE = os.getenv("AUTH_JWT_AUDIENCE", "flow-api")
_TEST_JWT_SHARED_SECRET = os.getenv(
    "AUTH_JWT_SHARED_SECRET", "ci-test-jwt-secret-at-least-32-bytes"
)


def _build_base_url() -> str:
    base = os.getenv("API_BASE", "http://localhost:4175").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{base}{prefix}"


def _merge_default_auth(kwargs: dict) -> dict:
    merged = dict(kwargs)
    if merged.pop("auth", True):
        headers = dict(merged.get("headers") or {})
        headers.setdefault("X-User-Id", _DEFAULT_TEST_USER_ACRONYM)
        merged["headers"] = headers
    return merged


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    url = f"{_build_base_url()}{path}"
    response = client.request(method, url, **_merge_default_auth(kwargs))
    payload = None
    if response.content and "application/json" in response.headers.get("content-type", ""):
        payload = response.json()
    return {"status": response.status_code, "payload": payload}


def _jwt_auth_headers(user_acronym: str) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "iss": _TEST_JWT_ISSUER,
            "aud": _TEST_JWT_AUDIENCE,
            "exp": now + timedelta(minutes=5),
            "iat": now,
            "acronym": user_acronym,
        },
        _TEST_JWT_SHARED_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _invalid_jwt_auth_headers(user_acronym: str) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "iss": _TEST_JWT_ISSUER,
            "aud": _TEST_JWT_AUDIENCE,
            "exp": now + timedelta(minutes=5),
            "iat": now,
            "acronym": user_acronym,
        },
        "wrong-secret-at-least-32-bytes-long",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _expected_keys(model) -> set[str]:
    return set(model.model_fields.keys())


def _assert_contract(item: dict, model) -> None:
    assert set(item.keys()) == _expected_keys(model)


def _user_acronym_map(payload: list[dict] | None) -> dict[int, str]:
    mapping: dict[int, str] = {}
    if not payload:
        return mapping
    for row in payload:
        if not isinstance(row, dict):
            continue
        user_id = row.get("user_id")
        user_acronym = row.get("user_acronym")
        if user_id is not None and user_acronym:
            mapping[user_id] = user_acronym
    return mapping


def _resolve_test_users(client: httpx.Client) -> tuple[int, int, dict[int, str]]:
    users = _request(client, "GET", "/people/users")
    if not (200 <= users["status"] < 300) or not users["payload"]:
        pytest.skip("No users available for endpoint contract tests")
    user_ids = [row.get("user_id") for row in users["payload"] if isinstance(row, dict)]
    user_ids = [uid for uid in user_ids if uid is not None]
    if len(user_ids) < 2:
        pytest.skip("Need at least two users for endpoint contract tests")
    user_map = _user_acronym_map(users["payload"])
    return user_ids[0], 2, user_map


def _get_project_doc_revision(client: httpx.Client) -> tuple[int, int, int]:
    projects = _request(client, "GET", "/lookups/projects")
    if not (200 <= projects["status"] < 300) or not projects["payload"]:
        pytest.skip("No projects available for endpoint contract tests")
    project_id = projects["payload"][0]["project_id"]

    docs = _request(client, "GET", "/documents", params={"project_id": project_id})
    if not (200 <= docs["status"] < 300) or not docs["payload"]:
        pytest.skip("No documents available for endpoint contract tests")
    doc_id = docs["payload"][0]["doc_id"]

    revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
    if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
        pytest.skip("No revisions available for endpoint contract tests")
    rev_id = revisions["payload"][0]["rev_id"]
    return project_id, doc_id, rev_id


def _ensure_contract_file(client: httpx.Client, rev_id: int) -> int:
    listed = _request(client, "GET", "/files", params={"rev_id": rev_id})
    if 200 <= listed["status"] < 300 and listed["payload"]:
        return listed["payload"][0]["id"]

    suffix = uuid.uuid4().hex[:6]
    upload = _request(
        client,
        "POST",
        "/files/",
        files={"file": (f"contract-{suffix}.pdf", b"contract", "application/pdf")},
        data={"rev_id": str(rev_id)},
    )
    assert upload["status"] == 201
    return upload["payload"]["id"]


@pytest.mark.api_smoke
def test_critical_list_endpoints_match_response_models():
    """Scenario IDs: TS-CTR-001."""
    with httpx.Client(timeout=10) as client:
        recipient_user_id, superuser_id, user_map = _resolve_test_users(client)
        project_id, doc_id, rev_id = _get_project_doc_revision(client)
        tracked_file_id = _ensure_contract_file(client, rev_id)

        suffix = str(int(time.time() * 1000))[-6:]
        created_dl = _request(
            client,
            "POST",
            "/distribution-lists",
            json={"distribution_list_name": f"CTR DL {suffix}"},
        )
        assert created_dl["status"] == 201
        tracked_dist_id = created_dl["payload"]["dist_id"]

        created_notification = _request(
            client,
            "POST",
            "/notifications",
            headers={"X-User-Id": user_map[superuser_id]},
            json={
                "title": "Contract notification",
                "body": "Contract notification body",
                "rev_id": rev_id,
                "recipient_user_ids": [recipient_user_id],
                "recipient_dist_ids": [],
            },
        )
        assert created_notification["status"] == 201
        tracked_notification_id = created_notification["payload"]["notification_id"]

        documents = _request(client, "GET", "/documents", params={"project_id": project_id})
        assert documents["status"] == 200
        _assert_contract(documents["payload"][0], DocOut)

        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert revisions["status"] == 200
        _assert_contract(revisions["payload"][0], DocRevisionOut)

        files = _request(client, "GET", "/files", params={"rev_id": rev_id})
        assert files["status"] == 200
        tracked_file = next(
            (row for row in files["payload"] if row.get("id") == tracked_file_id), None
        )
        assert tracked_file is not None
        _assert_contract(tracked_file, FileOut)

        notifications = _request(
            client,
            "GET",
            "/notifications",
            params={"recipient_user_id": recipient_user_id},
        )
        assert notifications["status"] == 200
        tracked_notification = next(
            (
                row
                for row in notifications["payload"]
                if row.get("notification_id") == tracked_notification_id
            ),
            None,
        )
        assert tracked_notification is not None
        _assert_contract(tracked_notification, NotificationOut)

        distribution_lists = _request(client, "GET", "/distribution-lists")
        assert distribution_lists["status"] == 200
        tracked_dist = next(
            (row for row in distribution_lists["payload"] if row.get("dist_id") == tracked_dist_id),
            None,
        )
        assert tracked_dist is not None
        _assert_contract(tracked_dist, DistributionListOut)


@pytest.mark.api_smoke
def test_current_user_detail_matches_response_model():
    """Scenario IDs: TS-CTR-002."""
    with httpx.Client(timeout=10) as client:
        response = _request(client, "GET", "/people/users/current_user")
        assert response["status"] == 200
        _assert_contract(response["payload"], UserOut)


@pytest.mark.api_smoke
def test_current_user_trusted_header_takes_precedence_over_x_user_id():
    """Scenario IDs: TS-CTR-003."""
    with httpx.Client(timeout=10) as client:
        first_user_id, second_user_id, user_map = _resolve_test_users(client)
        if first_user_id == second_user_id:
            pytest.skip("Need two distinct users for trusted-header precedence test")
        trusted_user = user_map.get(second_user_id)
        less_trusted_user = user_map.get(first_user_id)
        if not trusted_user or not less_trusted_user:
            pytest.skip("Need user acronyms for trusted-header precedence test")

        response = _request(
            client,
            "GET",
            "/people/users/current_user",
            auth=False,
            headers={
                "X-User-Id": less_trusted_user,
                "X-Auth-User": trusted_user,
            },
        )

        assert response["status"] == 200
        _assert_contract(response["payload"], UserOut)
        assert response["payload"]["user_id"] == second_user_id
        assert response["payload"]["user_acronym"] == trusted_user


@pytest.mark.api_smoke
def test_current_user_invalid_trusted_header_fails_closed_even_with_valid_x_user_id():
    """Scenario IDs: TS-CTR-004."""
    with httpx.Client(timeout=10) as client:
        first_user_id, _second_user_id, user_map = _resolve_test_users(client)
        less_trusted_user = user_map.get(first_user_id)
        if not less_trusted_user:
            pytest.skip("Need a user acronym for trusted-header fail-closed test")

        response = _request(
            client,
            "GET",
            "/people/users/current_user",
            auth=False,
            headers={
                "X-User-Id": less_trusted_user,
                "X-Auth-User": "NOTREAL",
            },
        )

        assert response["status"] == 401
        assert response["payload"] == {"detail": "Authentication required"}


@pytest.mark.api_smoke
def test_current_user_valid_bearer_jwt_resolves_identity():
    """Scenario IDs: TS-CTR-005."""
    with httpx.Client(timeout=10) as client:
        first_user_id, _second_user_id, user_map = _resolve_test_users(client)
        user_acronym = user_map.get(first_user_id)
        if not user_acronym:
            pytest.skip("Need a user acronym for bearer JWT contract test")

        response = _request(
            client,
            "GET",
            "/people/users/current_user",
            auth=False,
            headers=_jwt_auth_headers(user_acronym),
        )

        assert response["status"] == 200
        _assert_contract(response["payload"], UserOut)
        assert response["payload"]["user_id"] == first_user_id
        assert response["payload"]["user_acronym"] == user_acronym


@pytest.mark.api_smoke
def test_current_user_invalid_bearer_jwt_fails_closed_even_with_trusted_header():
    """Scenario IDs: TS-CTR-006."""
    with httpx.Client(timeout=10) as client:
        first_user_id, second_user_id, user_map = _resolve_test_users(client)
        jwt_user = user_map.get(first_user_id)
        trusted_user = user_map.get(second_user_id)
        if not jwt_user or not trusted_user:
            pytest.skip("Need user acronyms for bearer JWT fail-closed test")

        headers = _invalid_jwt_auth_headers(jwt_user)
        headers["X-Auth-User"] = trusted_user

        response = _request(
            client,
            "GET",
            "/people/users/current_user",
            auth=False,
            headers=headers,
        )

        assert response["status"] == 401
        assert response["payload"] == {"detail": "Authentication required"}
