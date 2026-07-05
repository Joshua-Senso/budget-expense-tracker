from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.features.recurring.models import RecurringExpense
from app.features.recurring.service import (
    CategoryOwnershipError,
    RecurringExpenseNotFoundError,
)
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


def _make_recurring(**kwargs: Any) -> RecurringExpense:
    defaults: dict[str, Any] = {
        "id": "rec-1",
        "user_id": "user-123",
        "household_id": None,
        "category_id": "cat-1",
        "description": "Netflix",
        "amount": Decimal("500.00"),
        "currency": "PHP",
        "start_on": date(2026, 1, 1),
        "frequency": "monthly",
        "is_active": True,
        "end_on": None,
        "created_at": datetime(2026, 7, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 7, 1, tzinfo=UTC),
    }
    return RecurringExpense(**{**defaults, **kwargs})


# --- list ---


def test_list_recurring_expenses_requires_auth(monkeypatch) -> None:
    client, _ = _authed_client(monkeypatch)

    response = client.get("/recurring")

    assert response.status_code == 401


def test_list_recurring_expenses_returns_404_when_not_a_household_member(
    monkeypatch,
) -> None:
    def raise_access_error(db, user_id, household_id):
        raise HouseholdAccessError(household_id)

    monkeypatch.setattr(
        "app.features.recurring.router.service.list_recurring_expenses",
        raise_access_error,
    )
    client, token = _authed_client(monkeypatch)

    response = client.get(
        "/recurring", params={"household_id": "house-1"}, headers=_auth_header(token)
    )

    assert response.status_code == 404


# --- create ---


def test_create_recurring_expense_returns_201(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.recurring.router.service.create_recurring_expense",
        lambda db, user_id, category_id, description, amount, currency, start_on, end_on, household_id=None: (
            _make_recurring()
        ),
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/recurring",
        headers=_auth_header(token),
        json={
            "category_id": "cat-1",
            "description": "Netflix",
            "amount": "500.00",
            "currency": "PHP",
            "start_on": "2026-01-01",
        },
    )

    assert response.status_code == 201


def test_create_recurring_expense_returns_404_when_category_not_owned(
    monkeypatch,
) -> None:
    def raise_category_error(
        db,
        user_id,
        category_id,
        description,
        amount,
        currency,
        start_on,
        end_on,
        household_id=None,
    ):
        raise CategoryOwnershipError(category_id)

    monkeypatch.setattr(
        "app.features.recurring.router.service.create_recurring_expense",
        raise_category_error,
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/recurring",
        headers=_auth_header(token),
        json={
            "category_id": "cat-1",
            "description": "Netflix",
            "amount": "500.00",
            "currency": "PHP",
            "start_on": "2026-01-01",
        },
    )

    assert response.status_code == 404


def test_create_recurring_expense_returns_404_when_not_a_household_member(
    monkeypatch,
) -> None:
    def raise_access_error(
        db,
        user_id,
        category_id,
        description,
        amount,
        currency,
        start_on,
        end_on,
        household_id=None,
    ):
        raise HouseholdAccessError(household_id)

    monkeypatch.setattr(
        "app.features.recurring.router.service.create_recurring_expense",
        raise_access_error,
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/recurring",
        headers=_auth_header(token),
        json={
            "category_id": "cat-1",
            "description": "Netflix",
            "amount": "500.00",
            "currency": "PHP",
            "start_on": "2026-01-01",
            "household_id": "house-1",
        },
    )

    assert response.status_code == 404


# --- stop (deactivate) ---


def test_stop_recurring_expense_returns_404_when_not_found(monkeypatch) -> None:
    def raise_not_found(db, user_id, recurring_id, year, month):
        raise RecurringExpenseNotFoundError(recurring_id)

    monkeypatch.setattr(
        "app.features.recurring.router.service.deactivate_recurring_expense",
        raise_not_found,
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/recurring/rec-1/2026-07", headers=_auth_header(token))

    assert response.status_code == 404


def test_stop_recurring_expense_returns_403_when_not_owner_of_shared_row(
    monkeypatch,
) -> None:
    def raise_role_error(db, user_id, recurring_id, year, month):
        raise HouseholdRoleError("house-1")

    monkeypatch.setattr(
        "app.features.recurring.router.service.deactivate_recurring_expense",
        raise_role_error,
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete("/recurring/rec-1/2026-07", headers=_auth_header(token))

    assert response.status_code == 403
