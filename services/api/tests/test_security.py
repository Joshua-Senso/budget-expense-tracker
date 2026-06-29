from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt import PyJWKSetError

from app.main import create_app


@dataclass(frozen=True)
class SigningKey:
    key: Any


class FakeJwkClient:
    def __init__(self, public_key: Any) -> None:
        self.public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        del token
        return SigningKey(self.public_key)


class BrokenJwkClient:
    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        del token
        raise PyJWKSetError("malformed jwks")


def make_token(private_key: Any, **claims: object) -> str:
    payload = {
        "sub": "user-123",
        "iss": "http://localhost:4000",
        "aud": "expense-api",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        **claims,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def make_client_with_jwk(monkeypatch, public_key: Any) -> TestClient:
    monkeypatch.setattr(
        "app.core.security.get_jwk_client",
        lambda jwks_url: FakeJwkClient(public_key),
    )
    return TestClient(create_app())


def test_protected_route_rejects_unauthenticated_request() -> None:
    client = TestClient(create_app())

    response = client.get("/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_route_rejects_invalid_token(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())

    response = client.get("/me", headers={"Authorization": "Bearer not-a-token"})

    assert response.status_code == 401


def test_protected_route_rejects_expired_token(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key, exp=datetime.now(UTC) - timedelta(minutes=1))

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_protected_route_rejects_wrong_audience(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key, aud="other-api")

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_protected_route_rejects_wrong_issuer(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key, iss="http://malicious.example")

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_protected_route_rejects_empty_subject(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key, sub="")

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_protected_route_rejects_wrong_algorithm(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": "http://localhost:4000",
            "aud": "expense-api",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "shared-secret-at-least-32-bytes-long",
        algorithm="HS256",
    )

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_protected_route_rejects_malformed_jwks(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.core.security.get_jwk_client",
        lambda jwks_url: BrokenJwkClient(),
    )
    client = TestClient(create_app())
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = make_token(private_key)

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_protected_route_returns_authenticated_user_id(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key)

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123"}
