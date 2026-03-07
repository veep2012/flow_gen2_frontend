"""Database configuration and session management."""

import json
import logging
import os
import re
import time
from functools import lru_cache
from typing import Any, Iterable, cast
from urllib.error import URLError
from urllib.request import urlopen

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import InvalidTokenError, PyJWKClient
from jwt import exceptions as jwt_exceptions
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
_AUTH_MODE_JWT = "jwt_bearer"
_AUTH_MODE_HEADER = "x_user_id_header"
_AUTH_MODE_TRUSTED_HEADER = "trusted_identity_header"
_AUTH_MODE_BOOTSTRAP = "app_user_bootstrap"
_AUTH_MODE_NONE = "missing_identity"
_TRUSTED_IDENTITY_HEADER = os.getenv("TRUSTED_IDENTITY_HEADER", "X-Auth-User")
_PYJWK_CLIENT_EXCEPTIONS = tuple(
    exc
    for exc in (
        getattr(jwt_exceptions, "PyJWKClientError", None),
        getattr(jwt_exceptions, "PyJWKClientConnectionError", None),
    )
    if exc is not None
)
_JWKS_FETCH_EXCEPTIONS = (json.JSONDecodeError, URLError, *_PYJWK_CLIENT_EXCEPTIONS)


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
            "startup_identity_mode=request_header_only app_env=%s identity_source=%s",
            env or "unknown",
            f"Authorization>{_TRUSTED_IDENTITY_HEADER}>X-User-Id",
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


def _jwt_issuer_url() -> str | None:
    value = os.getenv("AUTH_JWT_ISSUER_URL", "").strip()
    return value or None


def _jwt_audience() -> str | None:
    value = os.getenv("AUTH_JWT_AUDIENCE", "").strip()
    return value or None


def _jwt_shared_secret() -> str | None:
    value = os.getenv("AUTH_JWT_SHARED_SECRET", "").strip()
    return value or None


def _jwt_jwks_url() -> str | None:
    value = os.getenv("AUTH_JWT_JWKS_URL", "").strip()
    return value or None


def _jwt_identity_claims() -> tuple[str, ...]:
    raw = os.getenv("AUTH_JWT_IDENTITY_CLAIMS", "acronym,preferred_username,sub")
    claims = [claim.strip() for claim in raw.split(",") if claim.strip()]
    return tuple(claims or ["acronym", "preferred_username", "sub"])


def _jwt_algorithms() -> tuple[str, ...]:
    raw = os.getenv("AUTH_JWT_ALLOWED_ALGORITHMS", "RS256")
    values = [algorithm.strip() for algorithm in raw.split(",") if algorithm.strip()]
    return tuple(values or ["RS256"])


@lru_cache(maxsize=8)
def _discover_openid_configuration(issuer_url: str) -> dict[str, Any]:
    well_known_url = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
    with urlopen(well_known_url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _effective_jwks_url() -> str:
    explicit = _jwt_jwks_url()
    if explicit:
        return explicit

    issuer_url = _jwt_issuer_url()
    if not issuer_url:
        raise RuntimeError("AUTH_JWT_ISSUER_URL is required for JWT verification")

    config = _discover_openid_configuration(issuer_url)
    jwks_uri = config.get("jwks_uri")
    if not isinstance(jwks_uri, str) or not jwks_uri.strip():
        raise RuntimeError("OIDC discovery response did not provide jwks_uri")
    return jwks_uri


@lru_cache(maxsize=8)
def _jwt_jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _record_jwt_validation_failure(request: Request, *, reason: str) -> None:
    request.state.auth_mode = _AUTH_MODE_JWT
    request.state.auth_identity_present = False
    increment_counter("flow_auth_jwt_validation_failures_total", reason=reason)
    _log_auth_event(
        logging.WARNING,
        "jwt_validation_failure",
        request,
        reason=reason,
    )


def _extract_bearer_token(authorization_value: str) -> str:
    parts = authorization_value.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise ValueError("Malformed Authorization header")
    return parts[1].strip()


def _decode_bearer_token(token: str) -> dict[str, Any]:
    issuer_url = _jwt_issuer_url()
    audience = _jwt_audience()
    if not issuer_url or not audience:
        raise RuntimeError("JWT verification is not fully configured")

    algorithms = list(_jwt_algorithms())
    options = cast(Any, {"require": ["exp", "iss", "aud"]})
    shared_secret = _jwt_shared_secret()
    if shared_secret:
        return jwt.decode(
            token,
            shared_secret,
            algorithms=algorithms,
            audience=audience,
            issuer=issuer_url,
            options=options,
        )

    signing_key = _jwt_jwk_client(_effective_jwks_url()).get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=algorithms,
        audience=audience,
        issuer=issuer_url,
        options=options,
    )


def _identity_claim_from_payload(payload: dict[str, Any]) -> str | None:
    for claim_name in _jwt_identity_claims():
        value = payload.get(claim_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _resolve_bearer_identity(request: Request) -> str | None:
    authorization_value = request.headers.get("Authorization")
    if authorization_value is None:
        return None

    try:
        token = _extract_bearer_token(authorization_value)
        payload = _decode_bearer_token(token)
    except ValueError:
        _record_jwt_validation_failure(request, reason="malformed_authorization_header")
        raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL) from None
    except RuntimeError:
        _record_jwt_validation_failure(request, reason="jwt_verifier_unconfigured")
        raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL) from None
    except _JWKS_FETCH_EXCEPTIONS:
        _record_jwt_validation_failure(request, reason="jwks_fetch_failed")
        raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL) from None
    except InvalidTokenError:
        _record_jwt_validation_failure(request, reason="invalid_token")
        raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL) from None

    identity = _identity_claim_from_payload(payload)
    if identity is None:
        _record_jwt_validation_failure(request, reason="missing_identity_claim")
        raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL)
    return identity


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
    bearer_identity = _resolve_bearer_identity(request)
    header_value = request.headers.get("X-User-Id")
    trusted_header_value = request.headers.get(_TRUSTED_IDENTITY_HEADER)
    if bearer_identity is not None:
        raw_user_value = bearer_identity
        auth_mode = _AUTH_MODE_JWT
        header_name = "Authorization"
    elif trusted_header_value and trusted_header_value.strip():
        raw_user_value = trusted_header_value.strip()
        auth_mode = _AUTH_MODE_TRUSTED_HEADER
        header_name = _TRUSTED_IDENTITY_HEADER
    elif header_value is not None:
        raw_user_value = header_value.strip()
        auth_mode = _AUTH_MODE_HEADER if raw_user_value else _AUTH_MODE_NONE
        header_name = "X-User-Id"
    else:
        raw_user_value = _configured_app_user() or ""
        auth_mode = _AUTH_MODE_BOOTSTRAP if raw_user_value else _AUTH_MODE_NONE
        header_name = "APP_USER"

    user_value = ""
    if raw_user_value:
        user_value = _resolve_user_id(db, raw_user_value) or ""
        if not user_value:
            request.state.auth_mode = auth_mode
            request.state.auth_identity_present = False
            if auth_mode == _AUTH_MODE_JWT:
                _record_jwt_validation_failure(request, reason="unknown_internal_user")
                raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL)
            increment_counter(
                "flow_auth_identity_header_parse_failures_total",
                auth_mode=auth_mode,
            )
            _log_auth_event(
                logging.WARNING,
                "identity_header_parse_failure",
                request,
                header_name=header_name,
            )
            if auth_mode == _AUTH_MODE_TRUSTED_HEADER:
                raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL)
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
