import uuid
from calendar import monthrange
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.households import (
    assert_household_scope,
    category_accessible,
    household_scope_clauses,
    locate_household_scoped_row,
)
from app.features.expenses.models import Expense


class ExpenseNotFoundError(Exception):
    pass


class CategoryOwnershipError(Exception):
    pass


def _scoped_expense_query(user_id: str, household_id: str | None):
    return select(Expense).where(
        *household_scope_clauses(Expense, user_id, household_id)
    )


def _locate_expense_for_mutation(db: Session, user_id: str, expense_id: str) -> Expense:
    """Locate an expense for edit/delete: only the household owner may edit
    or delete a shared expense (PRD §10); members may read and add."""
    return locate_household_scoped_row(
        db, Expense, expense_id, user_id, ExpenseNotFoundError, require_owner=True
    )


def _assert_category_accessible(
    db: Session, user_id: str, category_id: str, household_id: str | None
) -> None:
    if not category_accessible(db, user_id, category_id, household_id):
        raise CategoryOwnershipError(category_id)


def list_expenses(
    db: Session,
    user_id: str,
    year: int | None = None,
    month: int | None = None,
    household_id: str | None = None,
) -> list[Expense]:
    assert_household_scope(db, user_id, household_id)
    query = _scoped_expense_query(user_id, household_id)

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
    household_id: str | None = None,
) -> Expense:
    assert_household_scope(db, user_id, household_id)
    _assert_category_accessible(db, user_id, category_id, household_id)
    expense = Expense(
        user_id=user_id,
        category_id=category_id,
        description=description,
        amount=amount,
        currency=currency,
        spent_on=spent_on,
        household_id=household_id,
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
    household_id: str | None = None,
) -> list[Expense]:
    assert_household_scope(db, user_id, household_id)
    _assert_category_accessible(db, user_id, category_id, household_id)
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
            household_id=household_id,
        )
        for index in range(1, installment_total + 1)
    ]
    db.add_all(expenses)
    db.commit()
    return list(
        db.execute(
            _scoped_expense_query(user_id, household_id)
            .where(Expense.installment_group_id == group_id)
            .order_by(Expense.installment_index)
        )
        .scalars()
        .all()
    )


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
    expense = _locate_expense_for_mutation(db, user_id, expense_id)

    if category_id is not None:
        _assert_category_accessible(db, user_id, category_id, expense.household_id)
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
    expense = _locate_expense_for_mutation(db, user_id, expense_id)

    if scope == "group" and expense.installment_group_id is not None:
        # A personal group is scoped to (user_id, household_id IS NULL), not
        # household_id IS NULL alone -- otherwise a group-id collision (or a
        # legacy row) could let one user's delete remove another user's rows.
        db.execute(
            delete(Expense).where(
                *household_scope_clauses(Expense, user_id, expense.household_id),
                Expense.installment_group_id == expense.installment_group_id,
            )
        )
    else:
        db.delete(expense)

    db.commit()
