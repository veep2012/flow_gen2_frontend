import logging

import pytest
from fastapi import HTTPException

from api.utils import database
from api.utils.observability import render_prometheus_text, reset_metrics

SCENARIO_DOC_PATH = "documentation/test_scenarios/auth_precedence_matrix_api_test_scenarios.md"
TEST_SCENARIO_MAP = {
    "test_jwt_identity_takes_precedence_over_disagreeing_trusted_header": ["TS-APM-001"],
    "test_trusted_header_resolves_when_bearer_token_missing": ["TS-APM-002"],
    "test_malformed_authorization_header_increments_metric_and_logs": ["TS-APM-003"],
    "test_validate_startup_app_user_mode_rejects_production": ["TS-APM-004"],
    "test_blank_trusted_header_falls_back_to_x_user_id_in_local": ["TS-APM-005"],
    "test_blank_x_user_id_keeps_request_anonymous_without_parse_failure": ["TS-APM-006"],
    "test_invalid_trusted_header_rejection_logs_and_counts_parse_failure": ["TS-APM-007"],
}


class _DummySession:
    def __init__(self) -> None:
        self.info: dict[str, str] = {}

    def in_transaction(self) -> bool:
        return False


def _make_request(*, headers: dict[str, str] | None = None):
    return type(
        "RequestStub",
        (),
        {
            "headers": dict(headers or {}),
            "state": type("StateStub", (), {"request_id": "req-123"})(),
            "method": "GET",
            "url": type("UrlStub", (), {"path": "/api/v1/people/users/current_user"})(),
            "scope": {},
        },
    )()


def test_jwt_identity_takes_precedence_over_disagreeing_trusted_header(monkeypatch) -> None:
    """Scenario IDs: TS-APM-001."""
    request = _make_request(
        headers={
            "Authorization": "Bearer token",
            "X-Auth-User": "TRUSTED",
            "X-User-Id": "HEADER",
        }
    )
    db = _DummySession()
    seen_values: list[str] = []

    monkeypatch.setattr(database, "_decode_bearer_token", lambda _token: {"acronym": "JWTUSER"})

    def _resolve_user_id(_db, raw_value: str) -> str | None:
        seen_values.append(raw_value)
        return {"JWTUSER": "7", "TRUSTED": "8", "HEADER": "9"}.get(raw_value)

    monkeypatch.setattr(database, "_resolve_user_id", _resolve_user_id)

    database._set_app_user(db, request)

    assert request.state.auth_mode == "jwt_bearer"
    assert request.state.auth_identity_present is True
    assert db.info["effective_user_id"] == "7"
    assert seen_values == ["JWTUSER"]


def test_trusted_header_resolves_when_bearer_token_missing(monkeypatch) -> None:
    """Scenario IDs: TS-APM-002."""
    request = _make_request(headers={"X-Auth-User": "TRUSTED"})
    db = _DummySession()
    monkeypatch.setattr(
        database,
        "_resolve_user_id",
        lambda _db, raw_value: "8" if raw_value == "TRUSTED" else None,
    )

    database._set_app_user(db, request)

    assert request.state.auth_mode == "trusted_identity_header"
    assert request.state.auth_identity_present is True
    assert db.info["effective_user_id"] == "8"


def test_blank_trusted_header_falls_back_to_x_user_id_in_local(monkeypatch) -> None:
    """Scenario IDs: TS-APM-005."""
    request = _make_request(headers={"X-Auth-User": "   ", "X-User-Id": "FDQC"})
    db = _DummySession()
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setattr(
        database,
        "_resolve_user_id",
        lambda _db, raw_value: "4" if raw_value == "FDQC" else None,
    )

    database._set_app_user(db, request)

    assert request.state.auth_mode == "x_user_id_header"
    assert request.state.auth_identity_present is True
    assert db.info["effective_user_id"] == "4"


def test_blank_x_user_id_keeps_request_anonymous_without_parse_failure(monkeypatch) -> None:
    """Scenario IDs: TS-APM-006."""
    reset_metrics()
    request = _make_request(headers={"X-User-Id": "   "})
    db = _DummySession()
    monkeypatch.setenv("APP_ENV", "local")

    def _unexpected_resolve(_db, _raw_value):
        raise AssertionError("Blank X-User-Id should not be resolved")

    monkeypatch.setattr(database, "_resolve_user_id", _unexpected_resolve)

    database._set_app_user(db, request)

    metrics = render_prometheus_text()
    assert request.state.auth_mode == "missing_identity"
    assert request.state.auth_identity_present is False
    assert db.info["effective_user_id"] == ""
    assert (
        'flow_auth_identity_header_parse_failures_total{auth_mode="x_user_id_header"}'
        not in metrics
    )


def test_invalid_trusted_header_rejection_logs_and_counts_parse_failure(
    monkeypatch, caplog
) -> None:
    """Scenario IDs: TS-APM-007."""
    reset_metrics()
    request = _make_request(headers={"X-Auth-User": "NOTREAL"})
    db = _DummySession()
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr(database, "_resolve_user_id", lambda _db, _raw_value: None)

    with pytest.raises(HTTPException, match="Authentication required") as exc:
        database._set_app_user(db, request)

    assert exc.value.status_code == 401
    metrics = render_prometheus_text()
    assert (
        'flow_auth_identity_header_parse_failures_total{auth_mode="trusted_identity_header"} 1'
        in metrics
    )
    assert (
        "event=identity_header_parse_failure request_id=req-123 "
        "auth_mode=trusted_identity_header method=GET "
        "path=/api/v1/people/users/current_user header_name=X-Auth-User" in caplog.text
    )


def test_auth_precedence_matrix_traceability_contract() -> None:
    doc_text = open(SCENARIO_DOC_PATH, encoding="utf-8").read()
    for test_name, scenario_ids in TEST_SCENARIO_MAP.items():
        assert test_name in doc_text, f"Missing mapped test in scenario doc: {test_name}"
        for scenario_id in scenario_ids:
            assert scenario_id in doc_text, f"Missing scenario ID in scenario doc: {scenario_id}"
