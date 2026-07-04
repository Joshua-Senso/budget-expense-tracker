import uuid
from calendar import monthrange
from datetime import date
from decimal import Decimal
from typing import Literal

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


def list_expenses(
    db: Session,
    user_id: str,
    year: int | None = None,
    month: int | None = None,
) -> list[Expense]:
    query = _own_expense_query(user_id)

    if year is not None and month is not None:
        month_start = date(year, month, 1)
        month_end = date(year, month, monthrange(year, month)[1])
        query = query.where(Expense.spent_on.between(month_start, month_end))

    return list(db.execute(query.order_by(Expense.spent_on.desc())).scalars().all())


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


def _add_months(start: date, months: int) -> date:
    total_month_index = start.month - 1 + months
    year = start.year + total_month_index // 12
    month = total_month_index % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)


def create_installment_expenses(
    db: Session,
    user_id: str,
    category_id: str,
    description: str,
    amount: Decimal,
    currency: str,
    spent_on: date,
    installment_total: int,
) -> list[Expense]:
    _assert_category_owned(db, user_id, category_id)
    group_id = str(uuid.uuid4())
    expenses = [
        Expense(
            user_id=user_id,
            category_id=category_id,
            description=f"{description} ({index}/{installment_total})",
            amount=amount,
            currency=currency,
            spent_on=_add_months(spent_on, index - 1),
            installment_group_id=group_id,
            installment_index=index,
            installment_total=installment_total,
            original_description=description,
        )
        for index in range(1, installment_total + 1)
    ]
    db.add_all(expenses)
    db.commit()
    return expenses


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


def delete_expense(
    db: Session,
    user_id: str,
    expense_id: str,
    scope: Literal["row", "group"] = "row",
) -> None:
    expense = db.execute(
        _own_expense_query(user_id).where(Expense.id == expense_id)
    ).scalar_one_or_none()
    if expense is None:
        raise ExpenseNotFoundError(expense_id)

    if scope == "group" and expense.installment_group_id is not None:
        group_expenses = (
            db.execute(
                _own_expense_query(user_id).where(
                    Expense.installment_group_id == expense.installment_group_id
                )
            )
            .scalars()
            .all()
        )
        for row in group_expenses:
            db.delete(row)
    else:
        db.delete(expense)

    db.commit()
