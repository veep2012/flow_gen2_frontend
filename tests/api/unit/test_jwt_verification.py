from datetime import datetime, timedelta, timezone

import jwt
import pytest

from api.utils import database


def _build_token(
    *,
    secret: str,
    issuer: str,
    audience: str,
    acronym: str | None = "FDQC",
    exp_delta: timedelta = timedelta(minutes=5),
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": issuer,
        "aud": audience,
        "exp": now + exp_delta,
        "iat": now,
    }
    if acronym is not None:
        payload["acronym"] = acronym
    return jwt.encode(payload, secret, algorithm="HS256")


def test_decode_bearer_token_validates_hs256_token(monkeypatch) -> None:
    issuer = "https://issuer.example/realms/flow"
    audience = "flow-api"
    secret = "test-shared-secret-at-least-32-bytes"
    token = _build_token(secret=secret, issuer=issuer, audience=audience)

    monkeypatch.setenv("AUTH_JWT_ISSUER_URL", issuer)
    monkeypatch.setenv("AUTH_JWT_AUDIENCE", audience)
    monkeypatch.setenv("AUTH_JWT_SHARED_SECRET", secret)
    monkeypatch.setenv("AUTH_JWT_ALLOWED_ALGORITHMS", "HS256")

    payload = database._decode_bearer_token(token)

    assert payload["acronym"] == "FDQC"


def test_decode_bearer_token_rejects_wrong_audience(monkeypatch) -> None:
    issuer = "https://issuer.example/realms/flow"
    audience = "flow-api"
    secret = "test-shared-secret-at-least-32-bytes"
    token = _build_token(secret=secret, issuer=issuer, audience="wrong-audience")

    monkeypatch.setenv("AUTH_JWT_ISSUER_URL", issuer)
    monkeypatch.setenv("AUTH_JWT_AUDIENCE", audience)
    monkeypatch.setenv("AUTH_JWT_SHARED_SECRET", secret)
    monkeypatch.setenv("AUTH_JWT_ALLOWED_ALGORITHMS", "HS256")

    with pytest.raises(jwt.InvalidTokenError):
        database._decode_bearer_token(token)


def test_decode_bearer_token_rejects_wrong_issuer(monkeypatch) -> None:
    issuer = "https://issuer.example/realms/flow"
    audience = "flow-api"
    secret = "test-shared-secret-at-least-32-bytes"
    token = _build_token(
        secret=secret, issuer="https://issuer.example/realms/other", audience=audience
    )

    monkeypatch.setenv("AUTH_JWT_ISSUER_URL", issuer)
    monkeypatch.setenv("AUTH_JWT_AUDIENCE", audience)
    monkeypatch.setenv("AUTH_JWT_SHARED_SECRET", secret)
    monkeypatch.setenv("AUTH_JWT_ALLOWED_ALGORITHMS", "HS256")

    with pytest.raises(jwt.InvalidTokenError):
        database._decode_bearer_token(token)


def test_decode_bearer_token_rejects_expired_token(monkeypatch) -> None:
    issuer = "https://issuer.example/realms/flow"
    audience = "flow-api"
    secret = "test-shared-secret-at-least-32-bytes"
    token = _build_token(
        secret=secret,
        issuer=issuer,
        audience=audience,
        exp_delta=timedelta(minutes=-5),
    )

    monkeypatch.setenv("AUTH_JWT_ISSUER_URL", issuer)
    monkeypatch.setenv("AUTH_JWT_AUDIENCE", audience)
    monkeypatch.setenv("AUTH_JWT_SHARED_SECRET", secret)
    monkeypatch.setenv("AUTH_JWT_ALLOWED_ALGORITHMS", "HS256")

    with pytest.raises(jwt.InvalidTokenError):
        database._decode_bearer_token(token)


def test_decode_bearer_token_rejects_invalid_signature(monkeypatch) -> None:
    issuer = "https://issuer.example/realms/flow"
    audience = "flow-api"
    token = _build_token(
        secret="different-shared-secret-at-least-32-bytes",
        issuer=issuer,
        audience=audience,
    )

    monkeypatch.setenv("AUTH_JWT_ISSUER_URL", issuer)
    monkeypatch.setenv("AUTH_JWT_AUDIENCE", audience)
    monkeypatch.setenv("AUTH_JWT_SHARED_SECRET", "test-shared-secret-at-least-32-bytes")
    monkeypatch.setenv("AUTH_JWT_ALLOWED_ALGORITHMS", "HS256")

    with pytest.raises(jwt.InvalidTokenError):
        database._decode_bearer_token(token)
