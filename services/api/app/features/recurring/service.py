from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.households import (
    assert_household_scope,
    category_accessible,
    household_scope_clauses,
    locate_household_scoped_row,
)
from app.features.currency.service import (
    convert_to_base,
    convert_to_base_or_unconverted,
    month_key_for,
    resolve_base_currency,
)
from app.features.exchange_rates.service import resolve_exchange_rate
from app.features.expenses.models import Expense
from app.features.recurring.models import RecurringExpense
from app.features.recurring.schemas import ProjectedExpense


class RecurringExpenseNotFoundError(Exception):
    pass


class CategoryOwnershipError(Exception):
    pass


def _scoped_recurring_query(user_id: str, household_id: str | None):
    return select(RecurringExpense).where(
        *household_scope_clauses(RecurringExpense, user_id, household_id)
    )


def _locate_recurring_for_mutation(
    db: Session, user_id: str, recurring_id: str
) -> RecurringExpense:
    """Locate a rule for edit/delete: only the household owner may edit or
    stop a shared rule (PRD §10); members may read and add."""
    return locate_household_scoped_row(
        db,
        RecurringExpense,
        recurring_id,
        user_id,
        RecurringExpenseNotFoundError,
        require_owner=True,
    )


def _assert_category_accessible(
    db: Session, user_id: str, category_id: str, household_id: str | None
) -> None:
    if not category_accessible(db, user_id, category_id, household_id):
        raise CategoryOwnershipError(category_id)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def list_recurring_expenses(
    db: Session, user_id: str, household_id: str | None = None
) -> list[RecurringExpense]:
    assert_household_scope(db, user_id, household_id)
    return list(
        db.execute(
            _scoped_recurring_query(user_id, household_id).order_by(
                RecurringExpense.start_on.desc()
            )
        )
        .scalars()
        .all()
    )


def create_recurring_expense(
    db: Session,
    user_id: str,
    category_id: str,
    description: str,
    amount: Decimal,
    currency: str,
    start_on: date,
    end_on: date | None = None,
    household_id: str | None = None,
    exchange_rate: Decimal | None = None,
) -> RecurringExpense:
    assert_household_scope(db, user_id, household_id)
    _assert_category_accessible(db, user_id, category_id, household_id)
    # Captured once here, not per generated occurrence -- the worker that
    # generates future months' rows has no user present to supply a rate.
    base_currency = resolve_base_currency(
        db, user_id, month_key_for(start_on), household_id
    )
    exchange_rate = resolve_exchange_rate(
        db, user_id, household_id, currency, base_currency, exchange_rate
    )
    _, exchange_rate = convert_to_base(amount, currency, base_currency, exchange_rate)
    recurring = RecurringExpense(
        user_id=user_id,
        category_id=category_id,
        description=description,
        amount=amount,
        currency=currency,
        start_on=start_on,
        end_on=end_on,
        household_id=household_id,
        exchange_rate=exchange_rate if currency != base_currency else None,
    )
    db.add(recurring)
    db.commit()
    return recurring


def deactivate_recurring_expense(
    db: Session,
    user_id: str,
    recurring_id: str,
    year: int,
    month: int,
) -> RecurringExpense:
    """Stop a recurring rule as viewed from a given month.

    Bounds the rule's end_on to that month so future occurrences stop being
    projected, while occurrences already projected for that month and earlier
    remain unaffected (PRD 7.3).
    """
    recurring = _locate_recurring_for_mutation(db, user_id, recurring_id)

    _, month_end = _month_bounds(year, month)
    if recurring.end_on is None or month_end < recurring.end_on:
        recurring.end_on = month_end
    recurring.is_active = False

    db.commit()
    return recurring


def _occurrence_date(start_on: date, year: int, month: int) -> date:
    day = min(start_on.day, monthrange(year, month)[1])
    return date(year, month, day)


def project_month(
    db: Session,
    user_id: str,
    year: int,
    month: int,
    household_id: str | None = None,
) -> list[ProjectedExpense]:
    assert_household_scope(db, user_id, household_id)
    month_start, month_end = _month_bounds(year, month)
    rules = (
        db.execute(
            _scoped_recurring_query(user_id, household_id).where(
                RecurringExpense.is_active.is_(True),
                RecurringExpense.start_on <= month_end,
                or_(
                    RecurringExpense.end_on.is_(None),
                    RecurringExpense.end_on >= month_start,
                ),
            )
        )
        .scalars()
        .all()
    )

    return [
        ProjectedExpense(
            recurring_expense_id=rule.id,
            category_id=rule.category_id,
            description=rule.description,
            amount=rule.amount,
            currency=rule.currency,
            spent_on=spent_on,
        )
        for rule in rules
        if (spent_on := _occurrence_date(rule.start_on, year, month)) >= rule.start_on
        and (rule.end_on is None or spent_on <= rule.end_on)
    ]


def generate_recurring_expenses(db: Session, year: int, month: int) -> int:
    """Persist one Expense row per active recurring rule due in a given month.

    Idempotent: a (recurring_expense_id, spent_on) unique index backs the
    existence check, and each insert runs in its own SAVEPOINT so a race
    between two concurrent runs (both passing the pre-check before either
    commits) surfaces as a caught IntegrityError, not a failed job. Runs
    across all users/rules (personal and household-scoped alike) — this is
    worker-internal, not a user-scoped API call, so a rule whose category is
    no longer accessible is skipped rather than raising and aborting the rest
    of the batch.
    """
    month_start, month_end = _month_bounds(year, month)
    rules = (
        db.execute(
            select(RecurringExpense).where(
                RecurringExpense.is_active.is_(True),
                RecurringExpense.start_on <= month_end,
                or_(
                    RecurringExpense.end_on.is_(None),
                    RecurringExpense.end_on >= month_start,
                ),
            )
        )
        .scalars()
        .all()
    )

    created = 0
    for rule in rules:
        spent_on = _occurrence_date(rule.start_on, year, month)
        if spent_on < rule.start_on or (
            rule.end_on is not None and spent_on > rule.end_on
        ):
            continue

        if not category_accessible(
            db, rule.user_id, rule.category_id, rule.household_id
        ):
            continue

        exists = db.scalar(
            select(Expense.id).where(
                Expense.recurring_expense_id == rule.id,
                Expense.spent_on == spent_on,
            )
        )
        if exists is not None:
            continue

        # Edge case: the scope's base currency drifted after the rule was
        # created (with no rate needed, or a rate for a currency pair that
        # no longer applies) and there's no user present to supply a fresh
        # one now. Fall back to a manually maintained rate for the pair
        # (BUD-52) before recording the occurrence unconverted rather than
        # dropping it from the whole batch (same resilience as the
        # inaccessible-category skip above, which also can't abort the rest
        # of the run).
        base_currency = resolve_base_currency(
            db, rule.user_id, month_key_for(spent_on), rule.household_id
        )
        rate = resolve_exchange_rate(
            db,
            rule.user_id,
            rule.household_id,
            rule.currency,
            base_currency,
            rule.exchange_rate,
        )
        base_amount, exchange_rate = convert_to_base_or_unconverted(
            rule.amount, rule.currency, base_currency, rate
        )

        try:
            with db.begin_nested():
                db.add(
                    Expense(
                        user_id=rule.user_id,
                        category_id=rule.category_id,
                        description=rule.description,
                        amount=rule.amount,
                        household_id=rule.household_id,
                        currency=rule.currency,
                        spent_on=spent_on,
                        recurring_expense_id=rule.id,
                        base_amount=base_amount,
                        exchange_rate=exchange_rate,
                    )
                )
                db.flush()
        except IntegrityError:
            continue
        created += 1

    db.commit()
    return created
