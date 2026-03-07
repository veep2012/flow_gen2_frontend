import logging
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.main import app
from api.routers import people as people_router
from api.utils import database
from api.utils.observability import render_prometheus_text, reset_metrics


class _DummySession:
    def __init__(self) -> None:
        self.info: dict[str, str] = {}

    def in_transaction(self) -> bool:
        return False


def _make_request(
    *,
    header_value: str | None = None,
    headers: dict[str, str] | None = None,
) -> SimpleNamespace:
    request_headers = dict(headers or {})
    if header_value is not None:
        request_headers["X-User-Id"] = header_value
    return SimpleNamespace(
        headers=request_headers,
        state=SimpleNamespace(request_id="req-123"),
        method="GET",
        url=SimpleNamespace(path="/api/v1/people/users/current_user"),
        scope={},
    )


def test_identity_header_parse_failure_increments_metric_and_logs(monkeypatch, caplog) -> None:
    reset_metrics()
    request = _make_request(header_value="NOTREAL")
    db = _DummySession()
    monkeypatch.setattr(database, "_resolve_user_id", lambda _db, _raw_value: None)
    caplog.set_level(logging.WARNING)

    with pytest.raises(
        HTTPException,
        match="Invalid X-User-Id header. Expected existing user_acronym.",
    ):
        database._set_app_user(db, request)

    metrics = render_prometheus_text()
    assert (
        'flow_auth_identity_header_parse_failures_total{auth_mode="x_user_id_header"} 1' in metrics
    )
    assert (
        "event=identity_header_parse_failure request_id=req-123 auth_mode=x_user_id_header "
        "method=GET path=/api/v1/people/users/current_user header_name=X-User-Id" in caplog.text
    )


def test_malformed_authorization_header_increments_metric_and_logs(caplog) -> None:
    reset_metrics()
    request = _make_request(headers={"Authorization": "Token not-a-bearer"})
    db = _DummySession()
    caplog.set_level(logging.WARNING)

    with pytest.raises(HTTPException, match="Authentication required"):
        database._set_app_user(db, request)

    metrics = render_prometheus_text()
    assert (
        'flow_auth_jwt_validation_failures_total{reason="malformed_authorization_header"} 1'
        in metrics
    )
    assert (
        "event=jwt_validation_failure request_id=req-123 auth_mode=jwt_bearer "
        "method=GET path=/api/v1/people/users/current_user reason=malformed_authorization_header"
        in caplog.text
    )


def test_valid_bearer_token_sets_effective_identity(monkeypatch) -> None:
    request = _make_request(headers={"Authorization": "Bearer token"})
    db = _DummySession()
    monkeypatch.setattr(database, "_decode_bearer_token", lambda _token: {"acronym": "FDQC"})
    monkeypatch.setattr(
        database, "_resolve_user_id", lambda _db, raw_value: "7" if raw_value == "FDQC" else None
    )

    database._set_app_user(db, request)

    assert request.state.auth_mode == "jwt_bearer"
    assert request.state.auth_identity_present is True
    assert db.info["effective_user_id"] == "7"


def test_current_user_resolution_failures_increment_metrics_and_logs(caplog) -> None:
    reset_metrics()
    caplog.set_level(logging.WARNING)
    original = people_router.get_effective_user_id
    original_get_db = people_router.get_db

    class _NoRowSession:
        def execute(self, *_args, **_kwargs):
            return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: None))

    def _override_get_db():
        yield _NoRowSession()

    app.dependency_overrides[original_get_db] = _override_get_db
    people_router.get_effective_user_id = lambda _db: 77
    client = TestClient(app)
    try:
        response = client.get("/api/v1/people/users/current_user")
        metrics_response = client.get("/metrics")
    finally:
        people_router.get_effective_user_id = original
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert metrics_response.status_code == 200
    body = metrics_response.text
    assert (
        'flow_auth_current_user_resolution_failures_total{reason="unresolved_read_model"} 1' in body
    )
    assert (
        'flow_auth_denied_by_rls_total{auth_mode="unknown",'
        'endpoint="/api/v1/people/users/current_user",status_code="404"} 1' in body
    )
    request_id = response.headers[database.REQUEST_ID_HEADER]
    assert (
        "event=current_user_resolution_failure "
        f"request_id={request_id} auth_mode=unknown method=GET "
        "path=/api/v1/people/users/current_user reason=unresolved_read_model" in caplog.text
    )


def test_trusted_identity_header_unresolved_fails_closed(monkeypatch) -> None:
    request = _make_request()
    request.headers = {"X-Auth-User": "NOTREAL"}
    db = _DummySession()
    monkeypatch.setattr(database, "_resolve_user_id", lambda _db, _raw_value: None)

    with pytest.raises(HTTPException, match="Authentication required") as exc:
        database._set_app_user(db, request)

    assert exc.value.status_code == 401


def test_unknown_internal_user_from_jwt_fails_closed(monkeypatch, caplog) -> None:
    reset_metrics()
    request = _make_request(headers={"Authorization": "Bearer token"})
    db = _DummySession()
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr(database, "_decode_bearer_token", lambda _token: {"acronym": "NOTREAL"})
    monkeypatch.setattr(database, "_resolve_user_id", lambda _db, _raw_value: None)

    with pytest.raises(HTTPException, match="Authentication required") as exc:
        database._set_app_user(db, request)

    assert exc.value.status_code == 401
    metrics = render_prometheus_text()
    assert 'flow_auth_jwt_validation_failures_total{reason="unknown_internal_user"} 1' in metrics
    assert (
        "event=jwt_validation_failure request_id=req-123 auth_mode=jwt_bearer "
        "method=GET path=/api/v1/people/users/current_user reason=unknown_internal_user"
        in caplog.text
    )
