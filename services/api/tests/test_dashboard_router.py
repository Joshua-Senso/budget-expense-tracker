from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.main import create_app


class SigningKey:
    def __init__(self, key: Any) -> None:
        self.key = key


class FakeJwkClient:
    def __init__(self, public_key: Any) -> None:
        self.public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        del token
        return SigningKey(self.public_key)


def make_client_with_jwk(monkeypatch, public_key: Any) -> TestClient:
    monkeypatch.setattr(
        "app.core.security.get_jwk_client",
        lambda jwks_url: FakeJwkClient(public_key),
    )
    return TestClient(create_app())


def make_token(private_key: Any) -> str:
    payload = {
        "sub": "user-123",
        "iss": "http://localhost:4000",
        "aud": "expense-api",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def test_yearly_overview_rejects_year_zero_as_validation_error(monkeypatch) -> None:
    # Regression guard: "0000" used to pass the path pattern and reach
    # int("0000") == 0, and date(0, 1, 1) raises ValueError -> unhandled 500.
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key)

    response = client.get(
        "/dashboard/yearly/0000", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


def test_yearly_overview_rejects_non_numeric_year(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key)

    response = client.get(
        "/dashboard/yearly/abcd", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422
