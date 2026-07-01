from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.features.expenses.models import Expense
from app.features.expenses.service import (
    CategoryOwnershipError,
    ExpenseNotFoundError,
    create_expense,
    delete_expense,
    list_expenses,
    update_expense,
)


def _mock_db() -> MagicMock:
    return MagicMock()


def _make_expense(**kwargs) -> Expense:
    defaults = {
        "id": "exp-1",
        "user_id": "user-1",
        "category_id": "cat-1",
        "description": "Lunch",
        "amount": Decimal("150.00"),
        "currency": "PHP",
        "spent_on": date(2026, 7, 1),
        "household_id": None,
    }
    exp = MagicMock(spec=Expense)
    for k, v in {**defaults, **kwargs}.items():
        setattr(exp, k, v)
    return exp


# --- list_expenses ---


def test_list_expenses_returns_all_for_user() -> None:
    db = _mock_db()
    expenses = [_make_expense(), _make_expense(id="exp-2", description="Dinner")]
    db.execute.return_value.scalars.return_value.all.return_value = expenses

    result = list_expenses(db, "user-1")

    assert result == expenses


def test_list_expenses_empty() -> None:
    db = _mock_db()
    db.execute.return_value.scalars.return_value.all.return_value = []

    result = list_expenses(db, "user-1")

    assert result == []


# --- create_expense ---


def test_create_expense_happy_path() -> None:
    db = _mock_db()
    db.scalar.return_value = "cat-1"

    result = create_expense(
        db, "user-1", "cat-1", "Lunch", Decimal("150"), "PHP", date(2026, 7, 1)
    )

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert result.user_id == "user-1"
    assert result.category_id == "cat-1"
    assert result.description == "Lunch"
    assert result.amount == Decimal("150")
    assert result.currency == "PHP"


def test_create_expense_category_not_owned_raises() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    with pytest.raises(CategoryOwnershipError):
        create_expense(
            db, "user-1", "cat-other", "Lunch", Decimal("150"), "PHP", date(2026, 7, 1)
        )

    db.add.assert_not_called()


# --- update_expense ---


def test_update_expense_happy_path() -> None:
    db = _mock_db()
    exp = _make_expense()
    db.execute.return_value.scalar_one_or_none.return_value = exp

    result = update_expense(db, "user-1", "exp-1", description="Dinner")

    assert exp.description == "Dinner"
    db.commit.assert_called_once()
    assert result is exp


def test_update_expense_not_found_raises() -> None:
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(ExpenseNotFoundError):
        update_expense(db, "user-1", "missing-id", description="Dinner")


def test_update_expense_category_ownership_checked() -> None:
    db = _mock_db()
    exp = _make_expense()
    db.execute.return_value.scalar_one_or_none.return_value = exp
    db.scalar.return_value = None

    with pytest.raises(CategoryOwnershipError):
        update_expense(db, "user-1", "exp-1", category_id="cat-other")


def test_update_expense_no_fields_is_noop() -> None:
    db = _mock_db()
    exp = _make_expense()
    db.execute.return_value.scalar_one_or_none.return_value = exp

    result = update_expense(db, "user-1", "exp-1")

    db.commit.assert_called_once()
    assert result is exp
    assert exp.description == "Lunch"


# --- delete_expense ---


def test_delete_expense_happy_path() -> None:
    db = _mock_db()
    exp = _make_expense()
    db.execute.return_value.scalar_one_or_none.return_value = exp

    delete_expense(db, "user-1", "exp-1")

    db.delete.assert_called_once_with(exp)
    db.commit.assert_called_once()


def test_delete_expense_not_found_raises() -> None:
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(ExpenseNotFoundError):
        delete_expense(db, "user-1", "missing-id")

    db.delete.assert_not_called()
