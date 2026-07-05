from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.categories.models import UserCategory
from app.features.expenses.models import Expense
from app.features.recurring.models import RecurringExpense
from app.features.recurring.schemas import ProjectedExpense


class RecurringExpenseNotFoundError(Exception):
    pass


class CategoryOwnershipError(Exception):
    pass


def _own_recurring_query(user_id: str):
    return select(RecurringExpense).where(
        RecurringExpense.user_id == user_id,
        RecurringExpense.household_id.is_(None),
    )


def _is_category_owned(db: Session, user_id: str, category_id: str) -> bool:
    return (
        db.scalar(
            select(UserCategory.id).where(
                UserCategory.id == category_id,
                UserCategory.user_id == user_id,
                UserCategory.household_id.is_(None),
            )
        )
        is not None
    )


def _assert_category_owned(db: Session, user_id: str, category_id: str) -> None:
    if not _is_category_owned(db, user_id, category_id):
        raise CategoryOwnershipError(category_id)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def list_recurring_expenses(db: Session, user_id: str) -> list[RecurringExpense]:
    return list(
        db.execute(
            _own_recurring_query(user_id).order_by(RecurringExpense.start_on.desc())
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
) -> RecurringExpense:
    _assert_category_owned(db, user_id, category_id)
    recurring = RecurringExpense(
        user_id=user_id,
        category_id=category_id,
        description=description,
        amount=amount,
        currency=currency,
        start_on=start_on,
        end_on=end_on,
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
    recurring = db.execute(
        _own_recurring_query(user_id).where(RecurringExpense.id == recurring_id)
    ).scalar_one_or_none()
    if recurring is None:
        raise RecurringExpenseNotFoundError(recurring_id)

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
    db: Session, user_id: str, year: int, month: int
) -> list[ProjectedExpense]:
    month_start, month_end = _month_bounds(year, month)
    rules = (
        db.execute(
            _own_recurring_query(user_id).where(
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
    across all users/rules — this is worker-internal, not a user-scoped API
    call, so a rule whose category is no longer owned is skipped rather than
    raising and aborting the rest of the batch.
    """
    month_start, month_end = _month_bounds(year, month)
    rules = (
        db.execute(
            select(RecurringExpense).where(
                RecurringExpense.is_active.is_(True),
                RecurringExpense.household_id.is_(None),
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

        if not _is_category_owned(db, rule.user_id, rule.category_id):
            continue

        exists = db.scalar(
            select(Expense.id).where(
                Expense.recurring_expense_id == rule.id,
                Expense.spent_on == spent_on,
            )
        )
        if exists is not None:
            continue

        try:
            with db.begin_nested():
                db.add(
                    Expense(
                        user_id=rule.user_id,
                        category_id=rule.category_id,
                        description=rule.description,
                        amount=rule.amount,
                        currency=rule.currency,
                        spent_on=spent_on,
                        recurring_expense_id=rule.id,
                    )
                )
                db.flush()
        except IntegrityError:
            continue
        created += 1

    db.commit()
    return created
