from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.routers import files_commented


class _DummyResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def one(self):
        return self._row


class _DummySession:
    def __init__(self) -> None:
        self.execute_calls: list[str] = []
        self.commit_calls = 0
        self.rollback_calls = 0

    def execute(self, statement, params=None):
        self.execute_calls.append(str(statement))
        return _DummyResult({"id": 3, "s3_uid": "commented/object.pdf"})

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1


def test_delete_commented_file_skips_db_delete_when_minio_remove_fails(monkeypatch) -> None:
    """Scenario IDs: TS-FC-017."""
    db = _DummySession()
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    monkeypatch.setattr(files_commented, "get_effective_user_id", lambda _db: 7)
    monkeypatch.setattr(
        files_commented,
        "_build_minio_client",
        lambda: (SimpleNamespace(remove_object=lambda *_args, **_kwargs: None), "flow-test"),
    )

    def _fail_remove(operation: str, _endpoint: str, _func):
        if operation == "remove_object":
            raise HTTPException(status_code=500, detail="Internal Server Error")
        return _func()

    monkeypatch.setattr(files_commented, "_minio_with_retry", _fail_remove)

    with pytest.raises(HTTPException, match="Internal Server Error"):
        files_commented.delete_commented_file(3, request, db)

    assert len(db.execute_calls) == 1
    assert "workflow.get_deletable_file_commented" in db.execute_calls[0]
    assert db.commit_calls == 0
    assert db.rollback_calls == 0
