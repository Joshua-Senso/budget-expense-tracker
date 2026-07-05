from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.households import assert_household_scope, household_scope_clauses
from app.features.budget.service import MonthlySettingNotFoundError, get_monthly_setting
from app.features.categories.models import UserCategory
from app.features.expenses.models import Expense

_PERCENT_QUANT = Decimal("0.01")


def _month_bounds(month_key: str) -> tuple[date, date]:
    year_str, month_str = month_key.split("-")
    year, month = int(year_str), int(month_str)
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return start, end


def _year_bounds(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year, 12, 31)


def _scope_conditions(user_id: str, household_id: str | None) -> list[Any]:
    return [
        *household_scope_clauses(Expense, user_id, household_id),
        *household_scope_clauses(UserCategory, user_id, household_id),
    ]


def _category_totals(
    db: Session,
    user_id: str,
    household_id: str | None,
    month_start: date,
    month_end: date,
) -> list[Any]:
    query = (
        select(
            UserCategory.id,
            UserCategory.name,
            UserCategory.color,
            UserCategory.expense_group,
            func.sum(Expense.amount),
        )
        .join(Expense, Expense.category_id == UserCategory.id)
        .where(
            *_scope_conditions(user_id, household_id),
            Expense.spent_on.between(month_start, month_end),
        )
        .group_by(
            UserCategory.id,
            UserCategory.name,
            UserCategory.color,
            UserCategory.expense_group,
        )
    )
    return list(db.execute(query).all())


def _monthly_group_totals(
    db: Session,
    user_id: str,
    household_id: str | None,
    year_start: date,
    year_end: date,
) -> list[Any]:
    query = (
        select(
            func.extract("month", Expense.spent_on),
            UserCategory.expense_group,
            func.sum(Expense.amount),
        )
        .join(Expense, Expense.category_id == UserCategory.id)
        .where(
            *_scope_conditions(user_id, household_id),
            Expense.spent_on.between(year_start, year_end),
        )
        .group_by(func.extract("month", Expense.spent_on), UserCategory.expense_group)
    )
    return list(db.execute(query).all())


def get_yearly_overview(
    db: Session, user_id: str, year: int, household_id: str | None = None
) -> dict:
    assert_household_scope(db, user_id, household_id)
    year_start, year_end = _year_bounds(year)
    rows = _monthly_group_totals(db, user_id, household_id, year_start, year_end)

    card_totals: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    other_totals: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for month_num, expense_group, total in rows:
        if expense_group == "card":
            card_totals[int(month_num)] += total
        else:
            other_totals[int(month_num)] += total

    months = []
    year_total = Decimal("0")
    for month_num in range(1, 13):
        card_total = card_totals[month_num]
        other_total = other_totals[month_num]
        month_total = card_total + other_total
        year_total += month_total
        months.append(
            {
                "month_key": f"{year}-{month_num:02d}",
                "month": month_num,
                "card_total": card_total,
                "other_total": other_total,
                "month_total": month_total,
            }
        )

    return {"year": year, "months": months, "year_total": year_total}


def get_dashboard_summary(
    db: Session, user_id: str, month_key: str, household_id: str | None = None
) -> dict:
    assert_household_scope(db, user_id, household_id)
    month_start, month_end = _month_bounds(month_key)
    rows = _category_totals(db, user_id, household_id, month_start, month_end)

    groups: dict[str, list[dict]] = {"card": [], "other": []}
    totals: dict[str, Decimal] = {"card": Decimal("0"), "other": Decimal("0")}

    for category_id, name, color, expense_group, total in rows:
        groups[expense_group].append(
            {"category_id": category_id, "name": name, "color": color, "total": total}
        )
        totals[expense_group] += total

    month_total = totals["card"] + totals["other"]

    # Household-level salary/budget settings don't exist yet (PRD §14 open
    # question); a household summary reports totals only, no salary-derived
    # fields, rather than mixing in the caller's personal salary.
    monthly_net_salary = None
    if household_id is None:
        try:
            monthly_net_salary = get_monthly_setting(
                db, user_id, month_key
            ).monthly_net_salary
        except MonthlySettingNotFoundError:
            monthly_net_salary = None

    remaining = (
        monthly_net_salary - month_total if monthly_net_salary is not None else None
    )
    percent_used = (
        (month_total / monthly_net_salary * 100).quantize(_PERCENT_QUANT)
        if monthly_net_salary
        else None
    )

    return {
        "month_key": month_key,
        "card": {"total": totals["card"], "categories": groups["card"]},
        "other": {"total": totals["other"], "categories": groups["other"]},
        "month_total": month_total,
        "monthly_net_salary": monthly_net_salary,
        "remaining": remaining,
        "percent_used": percent_used,
    }
