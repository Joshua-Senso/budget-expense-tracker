from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.features.currency.service import ExchangeRateRequiredError
from app.features.recurring.models import RecurringExpense
from app.features.recurring.service import (
    CategoryOwnershipError,
    RecurringExpenseNotFoundError,
    create_recurring_expense,
    deactivate_recurring_expense,
    generate_recurring_expenses,
    list_recurring_expenses,
    project_month,
)


def _mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture(autouse=True)
def _default_base_currency(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test below uses "PHP" rules; default the resolved base currency
    to match so the same-currency short circuit applies and no test needs to
    know about conversion unless it's specifically exercising it."""
    monkeypatch.setattr(
        "app.features.recurring.service.resolve_base_currency",
        lambda *args, **kwargs: "PHP",
    )


@pytest.fixture(autouse=True)
def _no_stored_exchange_rate_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default the manual-rate lookup (BUD-52) to a pass-through -- no stored
    rate for any pair -- so existing tests don't need to know about it.
    Fallback-specific tests override this per-test."""
    monkeypatch.setattr(
        "app.features.recurring.service.resolve_exchange_rate",
        lambda db, user_id, household_id, currency, base_currency, exchange_rate: (
            exchange_rate
        ),
    )


def _make_rule(**kwargs) -> RecurringExpense:
    defaults = {
        "id": "rec-1",
        "user_id": "user-1",
        "category_id": "cat-1",
        "description": "Netflix",
        "amount": Decimal("500.00"),
        "currency": "PHP",
        "exchange_rate": None,
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
    assert result.exchange_rate is None


def test_create_recurring_expense_stores_rate_when_currency_differs() -> None:
    db = _mock_db()
    db.scalar.return_value = "cat-1"

    result = create_recurring_expense(
        db,
        "user-1",
        "cat-1",
        "Netflix",
        Decimal("10"),
        "USD",
        date(2026, 1, 15),
        exchange_rate=Decimal("56.00"),
    )

    assert result.exchange_rate == Decimal("56.00")


def test_create_recurring_expense_requires_rate_when_currency_differs() -> None:
    db = _mock_db()
    db.scalar.return_value = "cat-1"

    with pytest.raises(ExchangeRateRequiredError):
        create_recurring_expense(
            db, "user-1", "cat-1", "Netflix", Decimal("10"), "USD", date(2026, 1, 15)
        )

    db.add.assert_not_called()


def test_create_recurring_expense_uses_stored_manual_rate_when_none_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """BUD-52: when the caller doesn't supply a rate, a manually maintained
    rate for the pair is used instead of raising."""
    monkeypatch.setattr(
        "app.features.recurring.service.resolve_exchange_rate",
        lambda db, user_id, household_id, currency, base_currency, exchange_rate: (
            Decimal("56.00")
        ),
    )
    db = _mock_db()
    db.scalar.return_value = "cat-1"

    result = create_recurring_expense(
        db, "user-1", "cat-1", "Netflix", Decimal("10"), "USD", date(2026, 1, 15)
    )

    assert result.exchange_rate == Decimal("56.00")


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


def test_project_month_only_queries_active_rules() -> None:
    """Must match generate_recurring_expenses's is_active filter (BUD-39 review).

    Otherwise a deactivated rule could still show up as a projected/exported
    row that the worker will never actually materialize.
    """
    db = _mock_db()
    db.execute.return_value.scalars.return_value.all.return_value = []

    project_month(db, "user-1", 2026, 7)

    executed_query = db.execute.call_args[0][0]
    assert "is_active" in str(executed_query)


def test_project_month_preserves_historical_occurrence_after_end_on() -> None:
    """A rule ended in a past month still projects for months <= its end_on."""
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15), end_on=date(2026, 3, 31))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]

    result = project_month(db, "user-1", 2026, 3)

    assert len(result) == 1
    assert result[0].spent_on == date(2026, 3, 15)


def test_project_month_excludes_occurrence_clamped_past_end_on() -> None:
    """A day-31 rule ending mid-April must not clamp forward to April 30.

    Regression guard: the month-overlap query alone let a Jan-31 rule with
    end_on=2026-04-15 through for April, and _occurrence_date used to clamp
    that to 2026-04-30 -- after the rule had already ended.
    """
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 31), end_on=date(2026, 4, 15))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]

    result = project_month(db, "user-1", 2026, 4)

    assert result == []


def test_project_month_includes_occurrence_exactly_on_end_on() -> None:
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 31), end_on=date(2026, 4, 30))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]

    result = project_month(db, "user-1", 2026, 4)

    assert len(result) == 1
    assert result[0].spent_on == date(2026, 4, 30)


# --- deactivate_recurring_expense ---


def test_deactivate_recurring_expense_bounds_end_on_to_month() -> None:
    db = _mock_db()
    rule = _make_rule(end_on=None)
    db.get.return_value = rule

    result = deactivate_recurring_expense(db, "user-1", "rec-1", 2026, 7)

    assert result.is_active is False
    assert result.end_on == date(2026, 7, 31)
    db.commit.assert_called_once()


def test_deactivate_recurring_expense_does_not_extend_earlier_end_on() -> None:
    db = _mock_db()
    rule = _make_rule(end_on=date(2026, 5, 31))
    db.get.return_value = rule

    deactivate_recurring_expense(db, "user-1", "rec-1", 2026, 7)

    assert rule.end_on == date(2026, 5, 31)


def test_deactivate_recurring_expense_not_found_raises() -> None:
    db = _mock_db()
    db.get.return_value = None

    with pytest.raises(RecurringExpenseNotFoundError):
        deactivate_recurring_expense(db, "user-1", "missing", 2026, 7)


# --- generate_recurring_expenses ---


def test_generate_recurring_expenses_creates_row_for_due_rule() -> None:
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]
    db.scalar.side_effect = ["cat-1", None]  # category owned, then no existing row

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 1
    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert added.recurring_expense_id == "rec-1"
    assert added.spent_on == date(2026, 7, 15)
    assert added.amount == Decimal("500.00")
    assert added.base_amount == Decimal("500.00")
    assert added.exchange_rate == Decimal("1")
    db.commit.assert_called_once()


def test_generate_recurring_expenses_uses_rules_stored_rate() -> None:
    db = _mock_db()
    rule = _make_rule(
        start_on=date(2026, 1, 15),
        currency="USD",
        amount=Decimal("10.00"),
        exchange_rate=Decimal("56.00"),
    )
    db.execute.return_value.scalars.return_value.all.return_value = [rule]
    db.scalar.side_effect = ["cat-1", None]

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 1
    added = db.add.call_args[0][0]
    assert added.base_amount == Decimal("560.00")
    assert added.exchange_rate == Decimal("56.00")


def test_generate_recurring_expenses_falls_back_when_rate_missing_after_base_currency_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Edge case: the scope's base currency diverged from the rule's currency
    after the rule was created with no rate needed at the time. The worker
    has no user present to supply one now, so it records the occurrence
    unconverted rather than dropping it from the batch."""
    monkeypatch.setattr(
        "app.features.recurring.service.resolve_base_currency",
        lambda *args, **kwargs: "EUR",
    )
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15), currency="USD", exchange_rate=None)
    db.execute.return_value.scalars.return_value.all.return_value = [rule]
    db.scalar.side_effect = ["cat-1", None]

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 1
    added = db.add.call_args[0][0]
    assert added.base_amount == rule.amount
    assert added.exchange_rate == Decimal("1")


def test_generate_recurring_expenses_uses_stored_manual_rate_after_base_currency_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """BUD-52: the worker has no user present to supply a rate after a
    base-currency drift (see the test above for the no-stored-rate case),
    but it can still use a manually maintained rate for the pair instead of
    falling all the way back to recording the occurrence unconverted."""
    monkeypatch.setattr(
        "app.features.recurring.service.resolve_base_currency",
        lambda *args, **kwargs: "EUR",
    )
    monkeypatch.setattr(
        "app.features.recurring.service.resolve_exchange_rate",
        lambda db, user_id, household_id, currency, base_currency, exchange_rate: (
            Decimal("0.92")
        ),
    )
    db = _mock_db()
    rule = _make_rule(
        start_on=date(2026, 1, 15),
        currency="USD",
        amount=Decimal("10.00"),
        exchange_rate=None,
    )
    db.execute.return_value.scalars.return_value.all.return_value = [rule]
    db.scalar.side_effect = ["cat-1", None]

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 1
    added = db.add.call_args[0][0]
    assert added.base_amount == Decimal("9.20")
    assert added.exchange_rate == Decimal("0.92")


def test_generate_recurring_expenses_is_idempotent() -> None:
    """A row already generated for (recurring_expense_id, spent_on) is skipped."""
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]
    db.scalar.side_effect = ["cat-1", "existing-expense-id"]

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 0
    db.add.assert_not_called()


def test_generate_recurring_expenses_skips_rule_with_unowned_category() -> None:
    """A rule whose category was since deleted/reassigned is skipped, not raised.

    Regression guard: the worker runs across all users, so one rule with a
    stale category must not raise and abort the rest of the batch.
    """
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]
    db.scalar.return_value = None  # category no longer owned

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 0
    db.add.assert_not_called()
    db.commit.assert_called_once()


def test_generate_recurring_expenses_swallows_race_on_unique_index() -> None:
    """Two concurrent runs can both pass the pre-check before either commits.

    The resulting IntegrityError on the losing insert must be caught (via the
    SAVEPOINT) and treated as an idempotent skip, not bubble up and fail the
    whole job.
    """
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]
    db.scalar.side_effect = ["cat-1", None]  # owned, and pre-check sees no row yet
    db.flush.side_effect = IntegrityError("insert", {}, Exception("dup key"))

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 0
    db.commit.assert_called_once()


def test_generate_recurring_expenses_skips_occurrence_past_end_on() -> None:
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 31), end_on=date(2026, 4, 15))
    db.execute.return_value.scalars.return_value.all.return_value = [rule]

    created = generate_recurring_expenses(db, 2026, 4)

    assert created == 0
    db.add.assert_not_called()


def test_generate_recurring_expenses_only_queries_active_rules() -> None:
    db = _mock_db()
    db.execute.return_value.scalars.return_value.all.return_value = []

    generate_recurring_expenses(db, 2026, 7)

    executed_query = db.execute.call_args[0][0]
    assert "is_active" in str(executed_query)


def test_generate_recurring_expenses_handles_mixed_rules() -> None:
    db = _mock_db()
    due_rule = _make_rule(id="rec-1", start_on=date(2026, 1, 15))
    existing_rule = _make_rule(id="rec-2", start_on=date(2026, 1, 20))
    db.execute.return_value.scalars.return_value.all.return_value = [
        due_rule,
        existing_rule,
    ]
    db.scalar.side_effect = ["cat-1", None, "cat-1", "already-generated"]

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 1
    db.add.assert_called_once()
    assert db.add.call_args[0][0].recurring_expense_id == "rec-1"


def test_generate_recurring_expenses_carries_household_id_onto_generated_row() -> None:
    """Household-scoped rules must generate household-scoped expenses too."""
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15), household_id="household-1")
    db.execute.return_value.scalars.return_value.all.return_value = [rule]
    db.scalar.side_effect = ["cat-1", None]  # category accessible, no existing row

    created = generate_recurring_expenses(db, 2026, 7)

    assert created == 1
    added = db.add.call_args[0][0]
    assert added.household_id == "household-1"


# --- household scoping ---


def test_list_recurring_expenses_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        list_recurring_expenses(db, "user-1", household_id="household-1")


def test_list_recurring_expenses_household_scope_returns_shared_rows() -> None:
    db = _mock_db()
    db.scalar.return_value = "member-1"
    shared = [_make_rule(household_id="household-1", user_id="user-2")]
    db.execute.return_value.scalars.return_value.all.return_value = shared

    result = list_recurring_expenses(db, "user-1", household_id="household-1")

    assert result == shared


def test_create_recurring_expense_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        create_recurring_expense(
            db,
            "user-1",
            "cat-1",
            "Netflix",
            Decimal("500"),
            "PHP",
            date(2026, 1, 15),
            household_id="household-1",
        )

    db.add.assert_not_called()


def test_create_recurring_expense_household_scope_happy_path() -> None:
    db = _mock_db()
    db.scalar.return_value = "cat-1"  # both membership and category checks pass

    result = create_recurring_expense(
        db,
        "user-1",
        "cat-1",
        "Netflix",
        Decimal("500"),
        "PHP",
        date(2026, 1, 15),
        household_id="household-1",
    )

    assert result.household_id == "household-1"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_create_recurring_expense_household_scope_category_check_excludes_personal_fallback() -> (
    None
):
    """Regression: a household-scoped rule must not accept the creator's
    personal category -- other household members can't resolve it when they
    list the shared rule (Greptile P1 on PR #106)."""
    db = _mock_db()
    db.scalar.return_value = "cat-1"

    create_recurring_expense(
        db,
        "user-1",
        "cat-1",
        "Netflix",
        Decimal("500"),
        "PHP",
        date(2026, 1, 15),
        household_id="household-1",
    )

    category_check_query = db.scalar.call_args_list[-1][0][0]
    assert "user_id" not in str(category_check_query)


def test_deactivate_recurring_expense_shared_row_accessible_to_household_owner() -> (
    None
):
    db = _mock_db()
    rule = _make_rule(household_id="household-1", user_id="user-2", end_on=None)
    db.get.return_value = rule
    db.scalar.return_value = "owner"  # requester owns household-1

    result = deactivate_recurring_expense(db, "user-1", "rec-1", 2026, 7)

    assert result.is_active is False


def test_deactivate_recurring_expense_shared_row_inaccessible_to_non_member() -> None:
    db = _mock_db()
    rule = _make_rule(household_id="household-1", user_id="user-2")
    db.get.return_value = rule
    db.scalar.return_value = None  # requester is not a member

    with pytest.raises(RecurringExpenseNotFoundError):
        deactivate_recurring_expense(db, "user-1", "rec-1", 2026, 7)


def test_deactivate_recurring_expense_shared_row_forbidden_for_non_owner_member() -> (
    None
):
    """Only the household owner may stop a shared recurring rule (PRD §10);
    members may read and add but not edit/delete."""
    db = _mock_db()
    rule = _make_rule(household_id="household-1", user_id="user-2")
    db.get.return_value = rule
    db.scalar.return_value = "member"  # requester is a member, not the owner

    with pytest.raises(HouseholdRoleError):
        deactivate_recurring_expense(db, "user-1", "rec-1", 2026, 7)
