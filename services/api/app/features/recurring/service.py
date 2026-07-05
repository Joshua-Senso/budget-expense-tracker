from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.features.categories.models import UserCategory
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


def _assert_category_owned(db: Session, user_id: str, category_id: str) -> None:
    owned = db.scalar(
        select(UserCategory.id).where(
            UserCategory.id == category_id,
            UserCategory.user_id == user_id,
            UserCategory.household_id.is_(None),
        )
    )
    if owned is None:
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
