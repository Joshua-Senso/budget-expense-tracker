from datetime import date
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.categories.models import UserCategory
from app.features.expenses.models import Expense
from app.features.recurring.service import project_month

EXPORT_COLUMNS = [
    "Row ID",
    "Row Type",
    "Category",
    "Description",
    "Amount",
    "Currency",
    "Date",
    "Category ID",
    "Recurring Expense ID",
    "Installment Group ID",
    "Installment Index",
    "Installment Total",
    "Original Description",
]

EXPORT_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _year_bounds(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year, 12, 31)


def _category_name_map(db: Session, user_id: str) -> dict[str, str]:
    rows = db.execute(
        select(UserCategory.id, UserCategory.name).where(
            UserCategory.user_id == user_id,
            UserCategory.household_id.is_(None),
        )
    ).all()
    return {category_id: name for category_id, name in rows}


def _recorded_rows(
    db: Session, user_id: str, year: int, categories: dict[str, str]
) -> list[dict[str, Any]]:
    year_start, year_end = _year_bounds(year)
    query = (
        select(Expense)
        .where(
            Expense.user_id == user_id,
            Expense.household_id.is_(None),
            Expense.spent_on.between(year_start, year_end),
        )
        .order_by(Expense.spent_on, Expense.id)
    )
    return [
        {
            "row_id": expense.id,
            "row_type": "recorded",
            "category": categories.get(expense.category_id),
            "description": expense.description,
            "amount": expense.amount,
            "currency": expense.currency,
            "date": expense.spent_on,
            "category_id": expense.category_id,
            "recurring_expense_id": expense.recurring_expense_id,
            "installment_group_id": expense.installment_group_id,
            "installment_index": expense.installment_index,
            "installment_total": expense.installment_total,
            "original_description": expense.original_description,
        }
        for expense in db.execute(query).scalars().all()
    ]


def _projected_rows(
    db: Session,
    user_id: str,
    year: int,
    today: date,
    categories: dict[str, str],
) -> list[dict[str, Any]]:
    """Recurring occurrences for months the monthly generation job hasn't reached yet.

    The worker only materializes the current month's rows (on the 1st, PRD
    §7.3), so a year's remaining future months have no Expense rows yet --
    project them so the export still reflects the full year.
    """
    current_month_start = today.replace(day=1)
    rows = []
    for month in range(1, 13):
        if date(year, month, 1) <= current_month_start:
            continue
        for occurrence in project_month(db, user_id, year, month):
            rows.append(
                {
                    "row_id": None,
                    "row_type": "projected",
                    "category": categories.get(occurrence.category_id),
                    "description": occurrence.description,
                    "amount": occurrence.amount,
                    "currency": occurrence.currency,
                    "date": occurrence.spent_on,
                    "category_id": occurrence.category_id,
                    "recurring_expense_id": occurrence.recurring_expense_id,
                    "installment_group_id": None,
                    "installment_index": None,
                    "installment_total": None,
                    "original_description": None,
                }
            )
    return rows


def build_year_export_rows(
    db: Session, user_id: str, year: int, today: date | None = None
) -> list[dict[str, Any]]:
    today = today or date.today()
    categories = _category_name_map(db, user_id)
    rows = _recorded_rows(db, user_id, year, categories)
    rows.extend(_projected_rows(db, user_id, year, today, categories))
    rows.sort(key=lambda row: (row["date"], row["row_id"] or ""))
    return rows


def build_export_workbook(
    db: Session, user_id: str, year: int, today: date | None = None
) -> BytesIO:
    rows = build_year_export_rows(db, user_id, year, today)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Expenses"
    sheet.append(EXPORT_COLUMNS)
    for row in rows:
        sheet.append(
            [
                row["row_id"],
                row["row_type"],
                row["category"],
                row["description"],
                str(row["amount"]),
                row["currency"],
                row["date"],
                row["category_id"],
                row["recurring_expense_id"],
                row["installment_group_id"],
                row["installment_index"],
                row["installment_total"],
                row["original_description"],
            ]
        )

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def export_filename(year: int, today: date | None = None) -> str:
    today = today or date.today()
    return f"expenses-{year}-{today.isoformat()}.xlsx"
