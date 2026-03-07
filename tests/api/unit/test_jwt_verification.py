from datetime import datetime, timedelta, timezone

import jwt
import pytest

from api.utils import database


def _build_token(*, secret: str, issuer: str, audience: str, acronym: str = "FDQC") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": issuer,
        "aud": audience,
        "exp": now + timedelta(minutes=5),
        "iat": now,
        "acronym": acronym,
    }
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
