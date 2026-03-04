from api.utils import database


class _DummyConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []

    def execute(self, statement, params):
        self.calls.append((str(statement), params))


class _DummySession:
    def __init__(self, value: str | None = None) -> None:
        self.info = {}
        if value is not None:
            self.info[database._IDENTITY_SESSION_INFO_KEY] = value


def test_apply_transaction_identity_uses_transaction_local_scope() -> None:
    conn = _DummyConnection()

    database._apply_transaction_identity(conn, "42")

    assert conn.calls == [
        ("SELECT set_config('app.user', :user_id, true)", {"user_id": "42"}),
        ("SELECT set_config('app.user_id', :user_id, true)", {"user_id": "42"}),
    ]


def test_sync_identity_on_transaction_begin_clears_missing_identity() -> None:
    conn = _DummyConnection()
    session = _DummySession()

    database._sync_identity_on_transaction_begin(session, None, conn)

    assert conn.calls == [
        ("SELECT set_config('app.user', :user_id, true)", {"user_id": ""}),
        ("SELECT set_config('app.user_id', :user_id, true)", {"user_id": ""}),
    ]
