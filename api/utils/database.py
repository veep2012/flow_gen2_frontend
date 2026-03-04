"""Database configuration and session management."""

import logging
import os
import re
import time
from typing import Iterable

from fastapi import Depends, HTTPException, Request
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from api.utils.observability import increment_counter

logger = logging.getLogger(__name__)

_APP_USER_ALLOWED_ENVS = {"local", "dev", "development", "test", "testing", "ci", "ci_test"}
_APP_USER_BLOCKED_ENVS = {"prod", "production", "stage", "staging"}
_APP_USER_PATTERN = re.compile(r"^[A-Z]{2,12}$")
_APP_USER_DB_WAIT_SEC = int(os.getenv("APP_USER_DB_WAIT_SEC", "30"))
_APP_USER_DB_WAIT_POLL_SEC = float(os.getenv("APP_USER_DB_WAIT_POLL_SEC", "1"))
REQUEST_ID_HEADER = "X-Request-Id"
MISSING_IDENTITY_DETAIL = "Authentication required"
_IDENTITY_SESSION_INFO_KEY = "effective_user_id"
_AUTH_MODE_HEADER = "x_user_id_header"
_AUTH_MODE_BOOTSTRAP = "app_user_bootstrap"
_AUTH_MODE_NONE = "missing_identity"


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


def _validate_app_user_format(app_user: str) -> None:
    if _APP_USER_PATTERN.fullmatch(app_user):
        return
    raise RuntimeError(
        "APP_USER has invalid format. Expected 2-12 uppercase letters " "(example: 'ZAML')."
    )


def _log_startup_identity_mode(*, env: str, app_user: str | None) -> None:
    if app_user is None:
        logger.info(
            "startup_identity_mode=request_header_only app_env=%s identity_source=X-User-Id",
            env or "unknown",
        )
        return

    logger.info(
        "startup_identity_mode=app_user_bootstrap app_env=%s identity_source=APP_USER app_user=%s",
        env,
        app_user,
    )


def _resolve_user_id(db: Session, raw_value: str) -> str | None:
    user_id = db.execute(
        text(
            """
            SELECT user_id
            FROM workflow.v_users
            -- Explicitly ignore NULL acronyms; case-insensitive match applies to real values only.
            WHERE user_acronym IS NOT NULL
              AND lower(user_acronym) = lower(:raw_value)
            LIMIT 1
            """
        ),
        {"raw_value": raw_value},
    ).scalar_one_or_none()
    if user_id is not None:
        return str(user_id)
    return None


def get_auth_mode(request: Request) -> str:
    value = getattr(request.state, "auth_mode", "")
    return value if isinstance(value, str) and value else "unknown"


def get_endpoint_label(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return request.url.path


def _log_auth_event(level: int, event: str, request: Request, **fields: str) -> None:
    base_fields = {
        "event": event,
        "request_id": get_request_id(request),
        "auth_mode": get_auth_mode(request),
        "method": request.method,
        "path": request.url.path,
        **{key: str(value) for key, value in fields.items()},
    }
    message = " ".join(f"{key}={value}" for key, value in base_fields.items())
    logger.log(level, message)


def record_current_user_resolution_failure(request: Request, *, reason: str) -> None:
    increment_counter("flow_auth_current_user_resolution_failures_total", reason=reason)
    _log_auth_event(
        logging.WARNING,
        "current_user_resolution_failure",
        request,
        reason=reason,
    )


def _apply_transaction_identity(connection, user_id: str) -> None:
    connection.execute(text("SELECT set_config('app.user', :user_id, true)"), {"user_id": user_id})
    connection.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"), {"user_id": user_id}
    )


def _session_identity_value(db: Session) -> str:
    value = db.info.get(_IDENTITY_SESSION_INFO_KEY, "")
    return value if isinstance(value, str) else ""


@event.listens_for(Session, "after_begin")
def _sync_identity_on_transaction_begin(session: Session, _transaction, connection) -> None:
    # Re-apply identity at transaction scope so pooled connections cannot leak
    # prior request identity across commits, rollbacks, or checkouts.
    _apply_transaction_identity(connection, _session_identity_value(session))


def validate_startup_app_user_mode() -> None:
    """
    Enforce APP_USER as local/non-production-only and validate configured user existence.
    """
    app_user = _configured_app_user()
    env = _current_app_env()
    if app_user is None:
        _log_startup_identity_mode(env=env, app_user=None)
        return

    if env in _APP_USER_BLOCKED_ENVS or env not in _APP_USER_ALLOWED_ENVS:
        raise RuntimeError(
            f"APP_USER cannot be enabled when APP_ENV={env or 'unknown'}. "
            "Use APP_USER only in local/dev/test/ci environments."
        )
    _validate_app_user_format(app_user)

    poll_sec = max(_APP_USER_DB_WAIT_POLL_SEC, 0.1)
    wait_sec = max(_APP_USER_DB_WAIT_SEC, 0)
    deadline = time.monotonic() + wait_sec
    max_attempts = max(int(wait_sec / poll_sec) + 1, 1)
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            with SessionLocal() as db:
                resolved = _resolve_user_id(db, app_user)
                if resolved is None:
                    raise RuntimeError(
                        "APP_USER must reference existing workflow.v_users.user_acronym"
                    )
                _log_startup_identity_mode(env=env, app_user=app_user)
                return
        except OperationalError as exc:
            if time.monotonic() >= deadline or attempts >= max_attempts:
                raise RuntimeError(
                    f"Database not ready while validating APP_USER during startup "
                    f"(attempts={attempts}, max_attempts={max_attempts})"
                ) from exc
            time.sleep(poll_sec)


def _set_app_user(db: Session, request: Request) -> None:
    header_value = request.headers.get("X-User-Id")
    if header_value is None:
        raw_user_value = _configured_app_user() or ""
        auth_mode = _AUTH_MODE_BOOTSTRAP if raw_user_value else _AUTH_MODE_NONE
    else:
        raw_user_value = header_value.strip()
        auth_mode = _AUTH_MODE_HEADER if raw_user_value else _AUTH_MODE_NONE
    user_value = ""
    if raw_user_value:
        user_value = _resolve_user_id(db, raw_user_value) or ""
        if not user_value:
            request.state.auth_mode = auth_mode
            request.state.auth_identity_present = False
            increment_counter(
                "flow_auth_identity_header_parse_failures_total",
                auth_mode=auth_mode,
            )
            _log_auth_event(
                logging.WARNING,
                "identity_header_parse_failure",
                request,
                header_name="X-User-Id",
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid X-User-Id header. Expected existing user_acronym.",
            )
    request.state.auth_mode = auth_mode
    request.state.auth_identity_present = bool(user_value)
    db.info[_IDENTITY_SESSION_INFO_KEY] = user_value
    if db.in_transaction():
        _apply_transaction_identity(db.connection(), user_value)


def get_request_id(request: Request) -> str:
    value = getattr(request.state, "request_id", "")
    return value if isinstance(value, str) and value else "unknown"


def get_effective_user_id(db: Session) -> int | None:
    row = (
        db.execute(
            text("SELECT NULLIF(current_setting('app.user', true), '')::SMALLINT AS user_id")
        )
        .mappings()
        .one()
    )
    return row["user_id"]


def get_db(request: Request) -> Iterable[Session]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        _set_app_user(db, request)
        yield db
    finally:
        db.close()


def require_effective_identity(request: Request, db: Session = Depends(get_db)) -> int:
    user_id = get_effective_user_id(db)
    if user_id is not None:
        return user_id

    _log_auth_event(logging.WARNING, "missing_effective_identity", request)
    raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL)
