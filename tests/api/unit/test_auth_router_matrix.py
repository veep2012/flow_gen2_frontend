from fastapi.testclient import TestClient

from api.main import app
from api.routers import people as people_router
from api.utils.database import get_db

SCENARIO_DOC_PATH = "documentation/test_scenarios/auth_router_matrix_api_test_scenarios.md"
TEST_SCENARIO_MAP = {
    "test_documents_router_requires_identity": ["TS-ARM-001"],
    "test_files_router_requires_identity": ["TS-ARM-002"],
    "test_files_commented_router_requires_identity": ["TS-ARM-003"],
    "test_written_comments_router_requires_identity": ["TS-ARM-004"],
    "test_notifications_router_requires_identity": ["TS-ARM-005"],
    "test_distribution_lists_router_requires_identity": ["TS-ARM-006"],
    "test_current_user_endpoint_requires_identity": ["TS-ARM-007"],
}


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


def _assert_auth_required(path: str, **kwargs) -> None:
    app.dependency_overrides[get_db] = _override_get_db
    original = people_router.get_effective_user_id
    people_router.get_effective_user_id = lambda _db: None
    client = TestClient(app)
    try:
        response = client.get(path, **kwargs)
    finally:
        people_router.get_effective_user_id = original
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_documents_router_requires_identity() -> None:
    """Scenario IDs: TS-ARM-001."""
    _assert_auth_required("/api/v1/documents/1/revisions")


def test_files_router_requires_identity() -> None:
    """Scenario IDs: TS-ARM-002."""
    _assert_auth_required("/api/v1/files", params={"rev_id": 1})


def test_files_commented_router_requires_identity() -> None:
    """Scenario IDs: TS-ARM-003."""
    _assert_auth_required("/api/v1/files/commented/list", params={"file_id": 1})


def test_written_comments_router_requires_identity() -> None:
    """Scenario IDs: TS-ARM-004."""
    _assert_auth_required("/api/v1/documents/revisions/1/comments")


def test_notifications_router_requires_identity() -> None:
    """Scenario IDs: TS-ARM-005."""
    _assert_auth_required("/api/v1/notifications", params={"recipient_user_id": 1})


def test_distribution_lists_router_requires_identity() -> None:
    """Scenario IDs: TS-ARM-006."""
    _assert_auth_required("/api/v1/distribution-lists")


def test_current_user_endpoint_requires_identity() -> None:
    """Scenario IDs: TS-ARM-007."""
    _assert_auth_required("/api/v1/people/users/current_user")


def test_auth_router_matrix_traceability_contract() -> None:
    doc_text = open(SCENARIO_DOC_PATH, encoding="utf-8").read()
    for test_name, scenario_ids in TEST_SCENARIO_MAP.items():
        assert test_name in doc_text, f"Missing mapped test in scenario doc: {test_name}"
        for scenario_id in scenario_ids:
            assert scenario_id in doc_text, f"Missing scenario ID in scenario doc: {scenario_id}"
