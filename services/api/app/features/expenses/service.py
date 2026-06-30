from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.categories.models import UserCategory
from app.features.expenses.models import Expense


class ExpenseNotFoundError(Exception):
    pass


class CategoryOwnershipError(Exception):
    pass


def _own_expense_query(user_id: str):
    return select(Expense).where(
        Expense.user_id == user_id,
        Expense.household_id.is_(None),
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


def list_expenses(db: Session, user_id: str) -> list[Expense]:
    return list(
        db.execute(_own_expense_query(user_id).order_by(Expense.spent_on.desc()))
        .scalars()
        .all()
    )


def create_expense(
    db: Session,
    user_id: str,
    category_id: str,
    description: str,
    amount: Decimal,
    currency: str,
    spent_on: date,
) -> Expense:
    _assert_category_owned(db, user_id, category_id)
    expense = Expense(
        user_id=user_id,
        category_id=category_id,
        description=description,
        amount=amount,
        currency=currency,
        spent_on=spent_on,
    )
    db.add(expense)
    db.commit()
    return expense


def update_expense(
    db: Session,
    user_id: str,
    expense_id: str,
    category_id: str | None = None,
    description: str | None = None,
    amount: Decimal | None = None,
    currency: str | None = None,
    spent_on: date | None = None,
) -> Expense:
    expense = db.execute(
        _own_expense_query(user_id).where(Expense.id == expense_id)
    ).scalar_one_or_none()
    if expense is None:
        raise ExpenseNotFoundError(expense_id)

    if category_id is not None:
        _assert_category_owned(db, user_id, category_id)
        expense.category_id = category_id

    for attr, value in [
        ("description", description),
        ("amount", amount),
        ("currency", currency),
        ("spent_on", spent_on),
    ]:
        if value is not None:
            setattr(expense, attr, value)

    db.commit()
    return expense


def delete_expense(db: Session, user_id: str, expense_id: str) -> None:
    expense = db.execute(
        _own_expense_query(user_id).where(Expense.id == expense_id)
    ).scalar_one_or_none()
    if expense is None:
        raise ExpenseNotFoundError(expense_id)
    db.delete(expense)
    db.commit()
