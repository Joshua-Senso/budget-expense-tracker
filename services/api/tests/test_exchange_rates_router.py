from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.features.exchange_rates.models import ExchangeRate
from app.features.exchange_rates.service import ExchangeRateNotFoundError
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


def _authed_client(monkeypatch) -> tuple[TestClient, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    return client, make_token(private_key)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_rate(**kwargs: Any) -> ExchangeRate:
    defaults: dict[str, Any] = {
        "id": "fx-1",
        "user_id": "user-123",
        "household_id": None,
        "from_currency": "USD",
        "to_currency": "PHP",
        "rate": Decimal("56.00"),
        "updated_by": "user-123",
        "created_at": datetime(2026, 7, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 7, 1, tzinfo=UTC),
    }
    return ExchangeRate(**{**defaults, **kwargs})


# --- list ---


def test_list_exchange_rates_requires_auth(monkeypatch) -> None:
    client, _ = _authed_client(monkeypatch)

    response = client.get("/exchange-rates")

    assert response.status_code == 401


def test_list_exchange_rates_returns_rates(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.exchange_rates.router.service.list_exchange_rates",
        lambda db, user_id, household_id: [_make_rate()],
    )
    client, token = _authed_client(monkeypatch)

    response = client.get("/exchange-rates", headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json()[0]["from_currency"] == "USD"


def test_list_exchange_rates_returns_404_when_not_a_household_member(
    monkeypatch,
) -> None:
    def raise_access_error(db, user_id, household_id):
        raise HouseholdAccessError(household_id)

    monkeypatch.setattr(
        "app.features.exchange_rates.router.service.list_exchange_rates",
        raise_access_error,
    )
    client, token = _authed_client(monkeypatch)

    response = client.get(
        "/exchange-rates",
        params={"household_id": "house-1"},
        headers=_auth_header(token),
    )

    assert response.status_code == 404


# --- upsert ---


def test_upsert_exchange_rate_returns_200(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.exchange_rates.router.service.upsert_exchange_rate",
        lambda db, user_id, household_id, from_currency, to_currency, rate: (
            _make_rate()
        ),
    )
    client, token = _authed_client(monkeypatch)

    response = client.put(
        "/exchange-rates",
        headers=_auth_header(token),
        json={"from_currency": "USD", "to_currency": "PHP", "rate": "56.00"},
    )

    assert response.status_code == 200
    assert response.json()["rate"] == "56.00"


def test_upsert_exchange_rate_rejects_unsupported_currency(monkeypatch) -> None:
    client, token = _authed_client(monkeypatch)

    response = client.put(
        "/exchange-rates",
        headers=_auth_header(token),
        json={"from_currency": "XXX", "to_currency": "PHP", "rate": "56.00"},
    )

    assert response.status_code == 422


def test_upsert_exchange_rate_rejects_non_positive_rate(monkeypatch) -> None:
    client, token = _authed_client(monkeypatch)

    response = client.put(
        "/exchange-rates",
        headers=_auth_header(token),
        json={"from_currency": "USD", "to_currency": "PHP", "rate": "0"},
    )

    assert response.status_code == 422


def test_upsert_exchange_rate_requires_auth(monkeypatch) -> None:
    client, _ = _authed_client(monkeypatch)

    response = client.put(
        "/exchange-rates",
        json={"from_currency": "USD", "to_currency": "PHP", "rate": "56.00"},
    )

    assert response.status_code == 401


def test_upsert_exchange_rate_returns_404_when_not_a_household_member(
    monkeypatch,
) -> None:
    def raise_access_error(db, user_id, household_id, from_currency, to_currency, rate):
        raise HouseholdAccessError(household_id)

    monkeypatch.setattr(
        "app.features.exchange_rates.router.service.upsert_exchange_rate",
        raise_access_error,
    )
    client, token = _authed_client(monkeypatch)

    response = client.put(
        "/exchange-rates",
        headers=_auth_header(token),
        json={
            "from_currency": "USD",
            "to_currency": "PHP",
            "rate": "56.00",
            "household_id": "house-1",
        },
    )

    assert response.status_code == 404


# --- delete ---


def test_delete_exchange_rate_returns_404_when_not_found(monkeypatch) -> None:
    def raise_not_found(db, user_id, exchange_rate_id):
        raise ExchangeRateNotFoundError(exchange_rate_id)

    monkeypatch.setattr(
        "app.features.exchange_rates.router.service.delete_exchange_rate",
        raise_not_found,
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/exchange-rates/fx-1", headers=_auth_header(token))

    assert response.status_code == 404


def test_delete_exchange_rate_returns_204(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.exchange_rates.router.service.delete_exchange_rate",
        lambda db, user_id, exchange_rate_id: None,
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/exchange-rates/fx-1", headers=_auth_header(token))

    assert response.status_code == 204


def test_delete_exchange_rate_returns_403_when_not_owner_of_shared_row(
    monkeypatch,
) -> None:
    def raise_role_error(db, user_id, exchange_rate_id):
        raise HouseholdRoleError("house-1")

    monkeypatch.setattr(
        "app.features.exchange_rates.router.service.delete_exchange_rate",
        raise_role_error,
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/exchange-rates/fx-1", headers=_auth_header(token))

    assert response.status_code == 403


def test_delete_exchange_rate_requires_auth(monkeypatch) -> None:
    client, _ = _authed_client(monkeypatch)

    response = client.delete("/exchange-rates/fx-1")

    assert response.status_code == 401
