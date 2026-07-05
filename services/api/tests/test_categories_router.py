from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.features.categories.models import UserCategory
from app.features.categories.service import CategoryNotFoundError
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


def _make_category(**kwargs: Any) -> UserCategory:
    defaults: dict[str, Any] = {
        "id": "cat-1",
        "user_id": "user-123",
        "household_id": None,
        "name": "Groceries",
        "color": "#F59E0B",
        "expense_group": "card",
        "created_at": datetime(2026, 7, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 7, 1, tzinfo=UTC),
    }
    return UserCategory(**{**defaults, **kwargs})


# --- list ---


def test_list_categories_requires_auth(monkeypatch) -> None:
    client, _ = _authed_client(monkeypatch)

    response = client.get("/categories")

    assert response.status_code == 401


def test_list_categories_returns_categories(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.categories.router.service.list_categories",
        lambda db, user_id, household_id: [_make_category()],
    )
    client, token = _authed_client(monkeypatch)

    response = client.get("/categories", headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json()[0]["id"] == "cat-1"


def test_list_categories_returns_404_when_not_a_household_member(monkeypatch) -> None:
    def raise_access_error(db, user_id, household_id):
        raise HouseholdAccessError(household_id)

    monkeypatch.setattr(
        "app.features.categories.router.service.list_categories", raise_access_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.get(
        "/categories", params={"household_id": "house-1"}, headers=_auth_header(token)
    )

    assert response.status_code == 404


# --- create ---


def test_create_category_returns_201(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.categories.router.service.create_category",
        lambda db, user_id, name, color, expense_group, household_id=None: (
            _make_category()
        ),
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/categories",
        headers=_auth_header(token),
        json={"name": "Groceries", "color": "#F59E0B", "expense_group": "card"},
    )

    assert response.status_code == 201


def test_create_category_returns_404_when_not_a_household_member(monkeypatch) -> None:
    def raise_access_error(db, user_id, name, color, expense_group, household_id=None):
        raise HouseholdAccessError(household_id)

    monkeypatch.setattr(
        "app.features.categories.router.service.create_category", raise_access_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/categories",
        headers=_auth_header(token),
        json={
            "name": "Sneaky",
            "color": "#000000",
            "expense_group": "other",
            "household_id": "house-1",
        },
    )

    assert response.status_code == 404


# --- update ---


def test_update_category_returns_404_when_not_found(monkeypatch) -> None:
    def raise_not_found(
        db, user_id, category_id, name=None, color=None, expense_group=None
    ):
        raise CategoryNotFoundError(category_id)

    monkeypatch.setattr(
        "app.features.categories.router.service.update_category", raise_not_found
    )
    client, token = _authed_client(monkeypatch)

    response = client.patch(
        "/categories/cat-1", headers=_auth_header(token), json={"name": "Hacked"}
    )

    assert response.status_code == 404


def test_update_category_returns_403_when_not_owner_of_shared_row(monkeypatch) -> None:
    def raise_role_error(
        db, user_id, category_id, name=None, color=None, expense_group=None
    ):
        raise HouseholdRoleError("house-1")

    monkeypatch.setattr(
        "app.features.categories.router.service.update_category", raise_role_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.patch(
        "/categories/cat-1",
        headers=_auth_header(token),
        json={"name": "Renamed by member"},
    )

    assert response.status_code == 403


# --- delete ---


def test_delete_category_returns_404_when_not_found(monkeypatch) -> None:
    def raise_not_found(db, user_id, category_id):
        raise CategoryNotFoundError(category_id)

    monkeypatch.setattr(
        "app.features.categories.router.service.delete_category", raise_not_found
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/categories/cat-1", headers=_auth_header(token))

    assert response.status_code == 404


def test_delete_category_returns_403_when_not_owner_of_shared_row(monkeypatch) -> None:
    def raise_role_error(db, user_id, category_id):
        raise HouseholdRoleError("house-1")

    monkeypatch.setattr(
        "app.features.categories.router.service.delete_category", raise_role_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/categories/cat-1", headers=_auth_header(token))

    assert response.status_code == 403
