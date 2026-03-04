import logging

from fastapi.testclient import TestClient

from api.main import app
from api.utils.database import REQUEST_ID_HEADER, get_db


class _DummyMappingsResult:
    def one(self) -> dict[str, None]:
        return {"user_id": None}


class _DummyExecuteResult:
    def mappings(self) -> _DummyMappingsResult:
        return _DummyMappingsResult()


class _DummySession:
    def execute(self, *_args, **_kwargs) -> _DummyExecuteResult:
        return _DummyExecuteResult()


def _override_get_db():
    yield _DummySession()


def test_missing_identity_logs_security_event_with_request_id(caplog) -> None:
    app.dependency_overrides[get_db] = _override_get_db
    caplog.set_level(logging.WARNING)
    client = TestClient(app)

    response = client.get("/api/v1/notifications", params={"recipient_user_id": 1})

    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert REQUEST_ID_HEADER in response.headers

    request_id = response.headers[REQUEST_ID_HEADER]
    assert request_id
    assert (
        f"event=missing_effective_identity request_id={request_id} auth_mode=unknown method=GET "
        "path=/api/v1/notifications"
    ) in caplog.text
