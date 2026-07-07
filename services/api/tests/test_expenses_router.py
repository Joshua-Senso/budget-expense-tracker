from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.features.currency.service import ExchangeRateRequiredError
from app.features.expenses.models import Expense
from app.features.expenses.service import CategoryOwnershipError, ExpenseNotFoundError
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


def _make_expense(**kwargs: Any) -> Expense:
    defaults: dict[str, Any] = {
        "id": "exp-1",
        "user_id": "user-123",
        "household_id": None,
        "category_id": "cat-1",
        "description": "Lunch",
        "amount": Decimal("150.00"),
        "currency": "PHP",
        "base_amount": Decimal("150.00"),
        "exchange_rate": Decimal("1"),
        "spent_on": date(2026, 7, 1),
        "created_at": datetime(2026, 7, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 7, 1, tzinfo=UTC),
    }
    return Expense(**{**defaults, **kwargs})


# --- list ---


def test_list_expenses_requires_auth(monkeypatch) -> None:
    client, _ = _authed_client(monkeypatch)

    response = client.get("/expenses")

    assert response.status_code == 401


def test_list_expenses_returns_expenses(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.expenses.router.service.list_expenses",
        lambda db, user_id, year, month, household_id: [_make_expense()],
    )
    client, token = _authed_client(monkeypatch)

    response = client.get("/expenses", headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json()[0]["id"] == "exp-1"


def test_list_expenses_returns_404_when_not_a_household_member(monkeypatch) -> None:
    def raise_access_error(db, user_id, year, month, household_id):
        raise HouseholdAccessError(household_id)

    monkeypatch.setattr(
        "app.features.expenses.router.service.list_expenses", raise_access_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.get(
        "/expenses", params={"household_id": "house-1"}, headers=_auth_header(token)
    )

    assert response.status_code == 404


# --- create ---


def test_create_expense_returns_201(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.expenses.router.service.create_expense",
        lambda db, user_id, category_id, description, amount, currency, spent_on, household_id=None, exchange_rate=None: (
            _make_expense()
        ),
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses",
        headers=_auth_header(token),
        json={
            "category_id": "cat-1",
            "description": "Lunch",
            "amount": "150.00",
            "currency": "PHP",
            "spent_on": "2026-07-01",
        },
    )

    assert response.status_code == 201


def test_create_expense_returns_404_when_category_not_owned(monkeypatch) -> None:
    def raise_category_error(
        db,
        user_id,
        category_id,
        description,
        amount,
        currency,
        spent_on,
        household_id=None,
        exchange_rate=None,
    ):
        raise CategoryOwnershipError(category_id)

    monkeypatch.setattr(
        "app.features.expenses.router.service.create_expense", raise_category_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses",
        headers=_auth_header(token),
        json={
            "category_id": "cat-1",
            "description": "Lunch",
            "amount": "150.00",
            "currency": "PHP",
            "spent_on": "2026-07-01",
        },
    )

    assert response.status_code == 404


def test_create_expense_returns_404_when_not_a_household_member(monkeypatch) -> None:
    def raise_access_error(
        db,
        user_id,
        category_id,
        description,
        amount,
        currency,
        spent_on,
        household_id=None,
        exchange_rate=None,
    ):
        raise HouseholdAccessError(household_id)

    monkeypatch.setattr(
        "app.features.expenses.router.service.create_expense", raise_access_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses",
        headers=_auth_header(token),
        json={
            "category_id": "cat-1",
            "description": "Lunch",
            "amount": "150.00",
            "currency": "PHP",
            "spent_on": "2026-07-01",
            "household_id": "house-1",
        },
    )

    assert response.status_code == 404


def test_create_expense_returns_422_when_exchange_rate_missing(monkeypatch) -> None:
    def raise_rate_required(
        db,
        user_id,
        category_id,
        description,
        amount,
        currency,
        spent_on,
        household_id=None,
        exchange_rate=None,
    ):
        raise ExchangeRateRequiredError(currency, "PHP")

    monkeypatch.setattr(
        "app.features.expenses.router.service.create_expense", raise_rate_required
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses",
        headers=_auth_header(token),
        json={
            "category_id": "cat-1",
            "description": "Lunch",
            "amount": "100.00",
            "currency": "USD",
            "spent_on": "2026-07-01",
        },
    )

    assert response.status_code == 422
    assert "USD" in response.json()["detail"]


# --- update ---


def test_update_expense_returns_404_when_not_found(monkeypatch) -> None:
    def raise_not_found(
        db,
        user_id,
        expense_id,
        category_id,
        description,
        amount,
        currency,
        spent_on,
        exchange_rate=None,
    ):
        raise ExpenseNotFoundError(expense_id)

    monkeypatch.setattr(
        "app.features.expenses.router.service.update_expense", raise_not_found
    )
    client, token = _authed_client(monkeypatch)

    response = client.patch(
        "/expenses/exp-1", headers=_auth_header(token), json={"description": "Hacked"}
    )

    assert response.status_code == 404


def test_update_expense_returns_403_when_not_owner_of_shared_row(monkeypatch) -> None:
    def raise_role_error(
        db,
        user_id,
        expense_id,
        category_id,
        description,
        amount,
        currency,
        spent_on,
        exchange_rate=None,
    ):
        raise HouseholdRoleError("house-1")

    monkeypatch.setattr(
        "app.features.expenses.router.service.update_expense", raise_role_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.patch(
        "/expenses/exp-1",
        headers=_auth_header(token),
        json={"description": "Edited by member"},
    )

    assert response.status_code == 403


# --- delete ---


def test_delete_expense_returns_404_when_not_found(monkeypatch) -> None:
    def raise_not_found(db, user_id, expense_id, scope="row"):
        raise ExpenseNotFoundError(expense_id)

    monkeypatch.setattr(
        "app.features.expenses.router.service.delete_expense", raise_not_found
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/expenses/exp-1", headers=_auth_header(token))

    assert response.status_code == 404


def test_delete_expense_returns_403_when_not_owner_of_shared_row(monkeypatch) -> None:
    def raise_role_error(db, user_id, expense_id, scope="row"):
        raise HouseholdRoleError("house-1")

    monkeypatch.setattr(
        "app.features.expenses.router.service.delete_expense", raise_role_error
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/expenses/exp-1", headers=_auth_header(token))

    assert response.status_code == 403
