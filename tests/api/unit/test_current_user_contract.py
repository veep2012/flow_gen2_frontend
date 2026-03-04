from fastapi.testclient import TestClient

from api.main import app
from api.routers import people as people_router
from api.utils.database import get_db

SCENARIO_DOC_PATH = "documentation/test_scenarios/current_user_api_test_scenarios.md"
TEST_SCENARIO_MAP = {
    "test_current_user_returns_valid_user": ["TS-CU-001"],
    "test_current_user_missing_session_user_returns_401": ["TS-CU-002"],
    "test_current_user_filtered_by_visibility_returns_404": ["TS-CU-003"],
    "test_current_user_inactive_user_returns_404": ["TS-CU-004"],
}


class _DummyMappingsResult:
    def __init__(self, row):
        self._row = row

    def one_or_none(self):
        return self._row


class _DummyExecuteResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return _DummyMappingsResult(self._row)


class _DummySession:
    def __init__(self, row):
        self._row = row

    def execute(self, *_args, **_kwargs):
        return _DummyExecuteResult(self._row)


def _override_get_db(row):
    def _inner():
        yield _DummySession(row)

    return _inner


def _make_client(*, current_user_id, row):
    app.dependency_overrides[get_db] = _override_get_db(row)
    original = people_router.get_effective_user_id
    people_router.get_effective_user_id = lambda _db: current_user_id
    client = TestClient(app)
    return client, original


def _cleanup(original_get_effective_user_id) -> None:
    people_router.get_effective_user_id = original_get_effective_user_id
    app.dependency_overrides.clear()


def test_current_user_returns_valid_user() -> None:
    """Scenario IDs: TS-CU-001."""
    row = {
        "user_id": 2,
        "person_id": 1,
        "user_acronym": "FDQC",
        "role_id": 4,
        "person_name": "Flow DCC",
        "role_name": "DCC User",
        "duty_id": 1,
        "duty_name": "Engineer",
    }
    client, original = _make_client(current_user_id=2, row=row)
    try:
        response = client.get("/api/v1/people/users/current_user")
    finally:
        _cleanup(original)

    assert response.status_code == 200
    assert response.json() == row


def test_current_user_missing_session_user_returns_401() -> None:
    """Scenario IDs: TS-CU-002."""
    client, original = _make_client(current_user_id=None, row=None)
    try:
        response = client.get("/api/v1/people/users/current_user")
    finally:
        _cleanup(original)

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_current_user_filtered_by_visibility_returns_404() -> None:
    """Scenario IDs: TS-CU-003."""
    client, original = _make_client(current_user_id=77, row=None)
    try:
        response = client.get("/api/v1/people/users/current_user")
    finally:
        _cleanup(original)

    assert response.status_code == 404
    assert response.json() == {"detail": "Current user not found"}


def test_current_user_inactive_user_returns_404() -> None:
    """Scenario IDs: TS-CU-004."""
    client, original = _make_client(current_user_id=88, row=None)
    try:
        response = client.get("/api/v1/people/users/current_user")
    finally:
        _cleanup(original)

    assert response.status_code == 404
    assert response.json() == {"detail": "Current user not found"}


def test_current_user_traceability_contract() -> None:
    doc_text = open(SCENARIO_DOC_PATH, encoding="utf-8").read()
    for test_name, scenario_ids in TEST_SCENARIO_MAP.items():
        assert test_name in doc_text, f"Missing mapped test in scenario doc: {test_name}"
        for scenario_id in scenario_ids:
            assert scenario_id in doc_text, f"Missing scenario ID in scenario doc: {scenario_id}"
