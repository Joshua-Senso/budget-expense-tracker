from calendar import monthrange
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

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


def _category_totals(
    db: Session, user_id: str, month_start: date, month_end: date
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
            Expense.user_id == user_id,
            Expense.household_id.is_(None),
            Expense.spent_on.between(month_start, month_end),
            UserCategory.user_id == user_id,
            UserCategory.household_id.is_(None),
        )
        .group_by(
            UserCategory.id,
            UserCategory.name,
            UserCategory.color,
            UserCategory.expense_group,
        )
    )
    return list(db.execute(query).all())


def get_dashboard_summary(db: Session, user_id: str, month_key: str) -> dict:
    month_start, month_end = _month_bounds(month_key)
    rows = _category_totals(db, user_id, month_start, month_end)

    groups: dict[str, list[dict]] = {"card": [], "other": []}
    totals: dict[str, Decimal] = {"card": Decimal("0"), "other": Decimal("0")}

    for category_id, name, color, expense_group, total in rows:
        groups[expense_group].append(
            {"category_id": category_id, "name": name, "color": color, "total": total}
        )
        totals[expense_group] += total

    month_total = totals["card"] + totals["other"]

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
