from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.households import HouseholdAccessError
from app.features.expenses.models import Expense
from app.features.expenses.service import (
    CategoryOwnershipError,
    ExpenseNotFoundError,
    create_expense,
    create_installment_expenses,
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


def test_list_expenses_filters_by_month() -> None:
    db = _mock_db()
    july = [_make_expense()]
    db.execute.return_value.scalars.return_value.all.return_value = july

    result = list_expenses(db, "user-1", year=2026, month=7)

    assert result == july
    executed_query = db.execute.call_args[0][0]
    assert "spent_on BETWEEN" in str(executed_query)


def test_list_expenses_ignores_partial_month_filter() -> None:
    db = _mock_db()
    expenses = [_make_expense(), _make_expense(id="exp-2")]
    db.execute.return_value.scalars.return_value.all.return_value = expenses

    result = list_expenses(db, "user-1", year=2026, month=None)

    assert result == expenses
    executed_query = db.execute.call_args[0][0]
    assert "spent_on BETWEEN" not in str(executed_query)


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


# --- create_installment_expenses ---


def _stub_installment_requery(db: MagicMock) -> None:
    """Make the post-commit re-query return whatever was passed to add_all."""

    def fake_execute(*args, **kwargs):
        del args, kwargs
        created = db.add_all.call_args[0][0]
        result = MagicMock()
        result.scalars.return_value.all.return_value = created
        return result

    db.execute.side_effect = fake_execute


def test_create_installment_expenses_generates_one_row_per_term() -> None:
    db = _mock_db()
    db.scalar.return_value = "cat-1"
    _stub_installment_requery(db)

    result = create_installment_expenses(
        db, "user-1", "cat-1", "TV", Decimal("1000"), "PHP", date(2026, 7, 1), 3
    )

    db.add_all.assert_called_once()
    db.commit.assert_called_once()
    assert len(result) == 3
    assert [e.spent_on for e in result] == [
        date(2026, 7, 1),
        date(2026, 8, 1),
        date(2026, 9, 1),
    ]
    assert [e.installment_index for e in result] == [1, 2, 3]
    assert all(e.installment_total == 3 for e in result)
    assert all(e.original_description == "TV" for e in result)
    assert [e.description for e in result] == ["TV (1/3)", "TV (2/3)", "TV (3/3)"]
    group_ids = {e.installment_group_id for e in result}
    assert len(group_ids) == 1


def test_create_installment_expenses_clamps_month_end_day() -> None:
    db = _mock_db()
    db.scalar.return_value = "cat-1"
    _stub_installment_requery(db)

    result = create_installment_expenses(
        db, "user-1", "cat-1", "TV", Decimal("1000"), "PHP", date(2026, 1, 31), 3
    )

    assert [e.spent_on for e in result] == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
    ]


def test_create_installment_expenses_category_not_owned_raises() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    with pytest.raises(CategoryOwnershipError):
        create_installment_expenses(
            db, "user-1", "cat-other", "TV", Decimal("1000"), "PHP", date(2026, 7, 1), 3
        )

    db.add_all.assert_not_called()


# --- update_expense ---


def test_update_expense_happy_path() -> None:
    db = _mock_db()
    exp = _make_expense()
    db.get.return_value = exp

    result = update_expense(db, "user-1", "exp-1", description="Dinner")

    assert exp.description == "Dinner"
    db.commit.assert_called_once()
    assert result is exp


def test_update_expense_not_found_raises() -> None:
    db = _mock_db()
    db.get.return_value = None

    with pytest.raises(ExpenseNotFoundError):
        update_expense(db, "user-1", "missing-id", description="Dinner")


def test_update_expense_category_ownership_checked() -> None:
    db = _mock_db()
    exp = _make_expense()
    db.get.return_value = exp
    db.scalar.return_value = None

    with pytest.raises(CategoryOwnershipError):
        update_expense(db, "user-1", "exp-1", category_id="cat-other")


def test_update_expense_no_fields_is_noop() -> None:
    db = _mock_db()
    exp = _make_expense()
    db.get.return_value = exp

    result = update_expense(db, "user-1", "exp-1")

    db.commit.assert_called_once()
    assert result is exp
    assert exp.description == "Lunch"


# --- delete_expense ---


def test_delete_expense_happy_path() -> None:
    db = _mock_db()
    exp = _make_expense()
    db.get.return_value = exp

    delete_expense(db, "user-1", "exp-1")

    db.delete.assert_called_once_with(exp)
    db.commit.assert_called_once()


def test_delete_expense_not_found_raises() -> None:
    db = _mock_db()
    db.get.return_value = None

    with pytest.raises(ExpenseNotFoundError):
        delete_expense(db, "user-1", "missing-id")

    db.delete.assert_not_called()


def test_delete_expense_group_scope_on_non_grouped_row_deletes_single_row() -> None:
    db = _mock_db()
    exp = _make_expense(installment_group_id=None)
    db.get.return_value = exp

    delete_expense(db, "user-1", "exp-1", scope="group")

    db.delete.assert_called_once_with(exp)
    db.commit.assert_called_once()


def test_delete_expense_group_scope_bulk_deletes_group_rows() -> None:
    db = _mock_db()
    exp = _make_expense(installment_group_id="grp-1")
    db.get.return_value = exp

    delete_expense(db, "user-1", "exp-1", scope="group")

    db.delete.assert_not_called()
    db.execute.assert_called_once()
    bulk_delete_stmt = db.execute.call_args_list[0][0][0]
    assert "DELETE FROM expenses" in str(bulk_delete_stmt)
    db.commit.assert_called_once()


def test_delete_expense_group_scope_personal_rows_scoped_to_owner() -> None:
    """Regression: a personal group-delete must stay scoped to (user_id,
    household_id IS NULL), not household_id IS NULL alone -- otherwise a
    group-id collision (or a legacy row) could delete another user's
    installments too (Greptile P1 on PR #106)."""
    db = _mock_db()
    exp = _make_expense(installment_group_id="grp-1")
    db.get.return_value = exp

    delete_expense(db, "user-1", "exp-1", scope="group")

    bulk_delete_stmt = db.execute.call_args_list[0][0][0]
    assert "expenses.user_id" in str(bulk_delete_stmt)


def test_delete_expense_group_scope_household_rows_not_scoped_to_deleter() -> None:
    """A shared group-delete is scoped by household, not by which member
    triggered it -- every row in the group carries the same household_id."""
    db = _mock_db()
    exp = _make_expense(
        installment_group_id="grp-1", household_id="household-1", user_id="user-2"
    )
    db.get.return_value = exp
    db.scalar.return_value = "member-1"  # requester is a member of household-1

    delete_expense(db, "user-1", "exp-1", scope="group")

    bulk_delete_stmt = db.execute.call_args_list[0][0][0]
    assert "expenses.household_id" in str(bulk_delete_stmt)
    assert "expenses.user_id" not in str(bulk_delete_stmt)


def test_delete_expense_row_scope_ignores_installment_group() -> None:
    db = _mock_db()
    exp = _make_expense(installment_group_id="grp-1")
    db.get.return_value = exp

    delete_expense(db, "user-1", "exp-1", scope="row")

    db.delete.assert_called_once_with(exp)
    db.commit.assert_called_once()


# --- household scoping ---


def test_list_expenses_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        list_expenses(db, "user-1", household_id="household-1")


def test_list_expenses_household_scope_returns_shared_rows() -> None:
    db = _mock_db()
    db.scalar.return_value = "member-1"
    shared = [_make_expense(household_id="household-1", user_id="user-2")]
    db.execute.return_value.scalars.return_value.all.return_value = shared

    result = list_expenses(db, "user-1", household_id="household-1")

    assert result == shared


def test_create_expense_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        create_expense(
            db,
            "user-1",
            "cat-1",
            "Lunch",
            Decimal("150"),
            "PHP",
            date(2026, 7, 1),
            household_id="household-1",
        )

    db.add.assert_not_called()


def test_create_expense_household_scope_happy_path() -> None:
    db = _mock_db()
    db.scalar.return_value = "cat-1"  # both membership and category checks pass

    result = create_expense(
        db,
        "user-1",
        "cat-1",
        "Lunch",
        Decimal("150"),
        "PHP",
        date(2026, 7, 1),
        household_id="household-1",
    )

    assert result.household_id == "household-1"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_create_expense_household_scope_rejects_category_from_other_household() -> None:
    db = _mock_db()
    # member check passes, category-accessibility check fails
    db.scalar.side_effect = ["member-1", None]

    with pytest.raises(CategoryOwnershipError):
        create_expense(
            db,
            "user-1",
            "cat-other-household",
            "Lunch",
            Decimal("150"),
            "PHP",
            date(2026, 7, 1),
            household_id="household-1",
        )

    db.add.assert_not_called()


def test_create_expense_household_scope_category_check_excludes_personal_fallback() -> (
    None
):
    """Regression: a household-scoped expense must not accept the creator's
    personal category -- other household members can't resolve it when they
    list the shared row (Greptile P1 on PR #106)."""
    db = _mock_db()
    db.scalar.return_value = "cat-1"

    create_expense(
        db,
        "user-1",
        "cat-1",
        "Lunch",
        Decimal("150"),
        "PHP",
        date(2026, 7, 1),
        household_id="household-1",
    )

    category_check_query = db.scalar.call_args_list[-1][0][0]
    assert "user_id" not in str(category_check_query)


def test_update_expense_shared_row_accessible_to_household_member() -> None:
    db = _mock_db()
    exp = _make_expense(household_id="household-1", user_id="user-2")
    db.get.return_value = exp
    db.scalar.return_value = "member-1"  # requester is a member of household-1

    result = update_expense(db, "user-1", "exp-1", description="Dinner")

    assert result.description == "Dinner"
    db.commit.assert_called_once()


def test_update_expense_shared_row_inaccessible_to_non_member() -> None:
    db = _mock_db()
    exp = _make_expense(household_id="household-1", user_id="user-2")
    db.get.return_value = exp
    db.scalar.return_value = None  # requester is not a member

    with pytest.raises(ExpenseNotFoundError):
        update_expense(db, "user-1", "exp-1", description="Dinner")
