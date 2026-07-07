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
from app.features.currency.service import (
    convert_to_base,
    month_key_for,
    resolve_base_currency,
)
from app.features.exchange_rates.service import resolve_exchange_rate
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
    exchange_rate: Decimal | None = None,
) -> Expense:
    assert_household_scope(db, user_id, household_id)
    _assert_category_accessible(db, user_id, category_id, household_id)
    base_currency = resolve_base_currency(
        db, user_id, month_key_for(spent_on), household_id
    )
    exchange_rate = resolve_exchange_rate(db, currency, base_currency, exchange_rate)
    base_amount, exchange_rate = convert_to_base(
        amount, currency, base_currency, exchange_rate
    )
    expense = Expense(
        user_id=user_id,
        category_id=category_id,
        description=description,
        amount=amount,
        currency=currency,
        spent_on=spent_on,
        household_id=household_id,
        base_amount=base_amount,
        exchange_rate=exchange_rate,
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
    exchange_rate: Decimal | None = None,
) -> list[Expense]:
    assert_household_scope(db, user_id, household_id)
    _assert_category_accessible(db, user_id, category_id, household_id)
    group_id = str(uuid.uuid4())
    # Resolved once for the whole plan, from the first occurrence's month --
    # a single rate is captured once when the plan is entered, and it can
    # only be valid against one target currency. Re-resolving per occurrence
    # (a user's per-month base-currency preference can differ month to
    # month) would risk applying that one rate against a different currency
    # than it was meant for on a later occurrence.
    base_currency = resolve_base_currency(
        db, user_id, month_key_for(spent_on), household_id
    )
    exchange_rate = resolve_exchange_rate(db, currency, base_currency, exchange_rate)
    base_amount, stored_rate = convert_to_base(
        amount, currency, base_currency, exchange_rate
    )
    expenses = []
    for index in range(1, installment_total + 1):
        occurrence_spent_on = _add_months(spent_on, index - 1)
        expenses.append(
            Expense(
                user_id=user_id,
                category_id=category_id,
                description=f"{description} ({index}/{installment_total})",
                amount=amount,
                currency=currency,
                spent_on=occurrence_spent_on,
                installment_group_id=group_id,
                installment_index=index,
                installment_total=installment_total,
                original_description=description,
                household_id=household_id,
                base_amount=base_amount,
                exchange_rate=stored_rate,
            )
        )
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
    exchange_rate: Decimal | None = None,
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

    # Only recompute when a conversion input actually changed this call.
    # The stored rate is never reused across a recompute: it was captured
    # against whatever base currency was active *then*, and nothing here
    # records what that was, so there's no safe way to tell whether it's
    # still valid for the base currency active *now* (which can drift --
    # a household's or a user's base currency can change independently of
    # this row). A call that doesn't touch amount/currency/spent_on/
    # exchange_rate leaves the existing base_amount/exchange_rate untouched
    # rather than risk silently misapplying a stale rate.
    #
    # spent_on is included even though it isn't a conversion input by
    # itself: a personal base currency is resolved per-month, so moving a
    # row to a different month can change which base currency it resolves
    # against (a household's base currency doesn't vary by month, but this
    # check doesn't need to know that -- recomputing is cheap and correct
    # either way).
    if (
        amount is not None
        or currency is not None
        or spent_on is not None
        or exchange_rate is not None
    ):
        base_currency = resolve_base_currency(
            db, user_id, month_key_for(expense.spent_on), expense.household_id
        )
        exchange_rate = resolve_exchange_rate(
            db, expense.currency, base_currency, exchange_rate
        )
        expense.base_amount, expense.exchange_rate = convert_to_base(
            expense.amount, expense.currency, base_currency, exchange_rate
        )

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
