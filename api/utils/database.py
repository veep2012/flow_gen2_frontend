"""Database configuration and session management."""

import os
import time
from typing import Iterable

from fastapi import HTTPException, Request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

_APP_USER_ALLOWED_ENVS = {"local", "dev", "development", "test", "testing", "ci", "ci_test"}
_APP_USER_BLOCKED_ENVS = {"prod", "production", "stage", "staging"}
_APP_USER_DB_WAIT_SEC = int(os.getenv("APP_USER_DB_WAIT_SEC", "30"))
_APP_USER_DB_WAIT_POLL_SEC = float(os.getenv("APP_USER_DB_WAIT_POLL_SEC", "1"))


def _build_database_url() -> str:
    explicit = os.getenv("APP_DATABASE_URL")
    if explicit:
        return os.path.expandvars(explicit)

    user = os.getenv("APP_DB_USER", "app_user")
    password = os.getenv("APP_DB_PASSWORD", "app_pass")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "flow_db")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


DATABASE_URL = _build_database_url()

# Force schema resolution to new layout.
engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"options": "-c search_path=workflow,core,ref,audit"},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _current_app_env() -> str:
    return os.getenv("APP_ENV", os.getenv("ENV", "")).strip().lower()


def _configured_app_user() -> str | None:
    value = os.getenv("APP_USER", "").strip()
    return value or None


def _resolve_user_id(db: Session, raw_value: str) -> str | None:
    user_id = db.execute(
        text(
            """
            SELECT user_id
            FROM workflow.v_users
            WHERE lower(user_acronym) = lower(:raw_value)
            LIMIT 1
            """
        ),
        {"raw_value": raw_value},
    ).scalar_one_or_none()
    if user_id is not None:
        return str(user_id)
    return None


def validate_startup_app_user_mode() -> None:
    """
    Enforce APP_USER as local/non-production-only and validate configured user existence.
    """
    app_user = _configured_app_user()
    if app_user is None:
        return

    env = _current_app_env()
    if env in _APP_USER_BLOCKED_ENVS or env not in _APP_USER_ALLOWED_ENVS:
        raise RuntimeError(
            "APP_USER is enabled in a non-allowed environment. "
            "Use APP_USER only in local/dev/test/ci environments."
        )

    deadline = time.monotonic() + max(_APP_USER_DB_WAIT_SEC, 0)
    while True:
        try:
            with SessionLocal() as db:
                resolved = _resolve_user_id(db, app_user)
                if resolved is None:
                    raise RuntimeError(
                        "APP_USER must reference existing workflow.v_users.user_acronym"
                    )
                return
        except OperationalError as exc:
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "Database not ready while validating APP_USER during startup"
                ) from exc
            time.sleep(max(_APP_USER_DB_WAIT_POLL_SEC, 0.1))


def _set_app_user(db: Session, request: Request) -> None:
    header_value = request.headers.get("X-User-Id")
    if header_value is None:
        raw_user_value = _configured_app_user() or ""
    else:
        raw_user_value = header_value.strip()
    user_value = ""
    if raw_user_value:
        user_value = _resolve_user_id(db, raw_user_value) or ""
        if not user_value:
            raise HTTPException(
                status_code=400,
                detail="Invalid X-User-Id header. Expected existing user_acronym.",
            )
    if user_value:
        db.execute(
            text("SELECT set_config('app.user', :user_id, false)"),
            {"user_id": user_value},
        )
        db.execute(
            text("SELECT set_config('app.user_id', :user_id, false)"),
            {"user_id": user_value},
        )
    else:
        db.execute(text("SELECT set_config('app.user', '', false)"))
        db.execute(text("SELECT set_config('app.user_id', '', false)"))


def get_db(request: Request) -> Iterable[Session]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        _set_app_user(db, request)
        yield db
    finally:
        db.close()
