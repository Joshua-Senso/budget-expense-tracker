from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.features.recurring.models import RecurringExpense
from app.features.recurring.service import (
    CategoryOwnershipError,
    RecurringExpenseNotFoundError,
    create_recurring_expense,
    deactivate_recurring_expense,
    list_recurring_expenses,
    project_month,
)


def _mock_db() -> MagicMock:
    return MagicMock()


def _make_rule(**kwargs) -> RecurringExpense:
    defaults = {
        "id": "rec-1",
        "user_id": "user-1",
        "category_id": "cat-1",
        "description": "Netflix",
        "amount": Decimal("500.00"),
        "currency": "PHP",
        "start_on": date(2026, 1, 15),
        "frequency": "monthly",
        "is_active": True,
        "end_on": None,
        "household_id": None,
    }
    rule = MagicMock(spec=RecurringExpense)
    for k, v in {**defaults, **kwargs}.items():
        setattr(rule, k, v)
    return rule


# --- create_recurring_expense ---


def test_create_recurring_expense_happy_path() -> None:
    db = _mock_db()
    db.scalar.return_value = "cat-1"

    result = create_recurring_expense(
        db, "user-1", "cat-1", "Netflix", Decimal("500"), "PHP", date(2026, 1, 15)
    )

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert result.user_id == "user-1"
    assert result.category_id == "cat-1"
    assert result.description == "Netflix"
    assert result.start_on == date(2026, 1, 15)
    assert result.end_on is None


def test_create_recurring_expense_category_not_owned_raises() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    with pytest.raises(CategoryOwnershipError):
        create_recurring_expense(
            db,
            "user-1",
            "cat-other",
            "Netflix",
            Decimal("500"),
            "PHP",
            date(2026, 1, 15),
        )

    db.add.assert_not_called()


# --- list_recurring_expenses ---


def test_list_recurring_expenses_returns_all_for_user() -> None:
    db = _mock_db()
    rules = [_make_rule(), _make_rule(id="rec-2", description="Spotify")]
    db.execute.return_value.scalars.return_value.all.return_value = rules

    result = list_recurring_expenses(db, "user-1")

    assert result == rules


# --- project_month ---


def test_project_month_generates_occurrence_for_active_rule() -> None:
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]

    result = project_month(db, "user-1", 2026, 7)

    assert len(result) == 1
    occurrence = result[0]
    assert occurrence.recurring_expense_id == "rec-1"
    assert occurrence.category_id == "cat-1"
    assert occurrence.amount == Decimal("500.00")
    assert occurrence.spent_on == date(2026, 7, 15)
    assert occurrence.source == "generated"


def test_project_month_clamps_day_to_shorter_month() -> None:
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 31))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]

    result = project_month(db, "user-1", 2026, 2)

    assert result[0].spent_on == date(2026, 2, 28)


def test_project_month_excludes_rule_starting_after_month() -> None:
    db = _mock_db()
    db.execute.return_value.scalars.return_value.all.return_value = []

    result = project_month(db, "user-1", 2026, 7)

    assert result == []
    executed_query = db.execute.call_args[0][0]
    assert "start_on <=" in str(executed_query)


def test_project_month_preserves_historical_occurrence_after_end_on() -> None:
    """A rule ended in a past month still projects for months <= its end_on."""
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15), end_on=date(2026, 3, 31))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]

    result = project_month(db, "user-1", 2026, 3)

    assert len(result) == 1
    assert result[0].spent_on == date(2026, 3, 15)


# --- deactivate_recurring_expense ---


def test_deactivate_recurring_expense_bounds_end_on_to_month() -> None:
    db = _mock_db()
    rule = _make_rule(end_on=None)
    db.execute.return_value.scalar_one_or_none.return_value = rule

    result = deactivate_recurring_expense(db, "user-1", "rec-1", 2026, 7)

    assert result.is_active is False
    assert result.end_on == date(2026, 7, 31)
    db.commit.assert_called_once()


def test_deactivate_recurring_expense_does_not_extend_earlier_end_on() -> None:
    db = _mock_db()
    rule = _make_rule(end_on=date(2026, 5, 31))
    db.execute.return_value.scalar_one_or_none.return_value = rule

    deactivate_recurring_expense(db, "user-1", "rec-1", 2026, 7)

    assert rule.end_on == date(2026, 5, 31)


def test_deactivate_recurring_expense_not_found_raises() -> None:
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(RecurringExpenseNotFoundError):
        deactivate_recurring_expense(db, "user-1", "missing", 2026, 7)
