import logging

import pytest

from api.utils import database


class _DummySession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_validate_startup_app_user_mode_rejects_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_USER", "ZAML")

    with pytest.raises(
        RuntimeError,
        match=r"APP_USER cannot be enabled when APP_ENV=production",
    ):
        database.validate_startup_app_user_mode()


def test_validate_startup_app_user_mode_rejects_invalid_format(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("APP_USER", "zaml1")

    with pytest.raises(
        RuntimeError,
        match=r"APP_USER has invalid format\. Expected 2-12 uppercase letters",
    ):
        database.validate_startup_app_user_mode()


def test_validate_startup_app_user_mode_logs_header_only_banner(monkeypatch, caplog) -> None:
    monkeypatch.delenv("APP_USER", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    caplog.set_level(logging.INFO)

    database.validate_startup_app_user_mode()

    assert (
        "startup_identity_mode=request_header_only app_env=production "
        "identity_source=Authorization>X-Auth-User" in caplog.text
    )


def test_validate_startup_app_user_mode_logs_nonprod_header_banner(monkeypatch, caplog) -> None:
    monkeypatch.delenv("APP_USER", raising=False)
    monkeypatch.setenv("APP_ENV", "local")
    caplog.set_level(logging.INFO)

    database.validate_startup_app_user_mode()

    assert (
        "startup_identity_mode=request_header_only app_env=local "
        "identity_source=Authorization>X-Auth-User>X-User-Id" in caplog.text
    )


def test_validate_startup_app_user_mode_logs_bootstrap_banner(monkeypatch, caplog) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("APP_USER", "ZAML")
    monkeypatch.setattr(
        database, "_resolve_user_id", lambda _db, raw_value: "1" if raw_value == "ZAML" else None
    )
    monkeypatch.setattr(database, "SessionLocal", lambda: _DummySession())
    caplog.set_level(logging.INFO)

    database.validate_startup_app_user_mode()

    assert (
        "startup_identity_mode=app_user_bootstrap app_env=local identity_source=APP_USER "
        "app_user=ZAML"
    ) in caplog.text
