from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from openpyxl import load_workbook

from app.features.expenses.models import Expense
from app.features.import_export.service import (
    EXPORT_COLUMNS,
    build_export_workbook,
    build_year_export_rows,
    export_filename,
)
from app.features.recurring.models import RecurringExpense


def _mock_db() -> MagicMock:
    return MagicMock()


def _make_expense(**kwargs) -> Expense:
    defaults = {
        "id": "exp-1",
        "user_id": "user-1",
        "category_id": "cat-1",
        "description": "Lunch",
        "amount": Decimal("150.00"),
        "currency": "PHP",
        "spent_on": date(2026, 1, 5),
        "installment_group_id": None,
        "installment_index": None,
        "installment_total": None,
        "original_description": None,
        "recurring_expense_id": None,
        "household_id": None,
    }
    exp = MagicMock(spec=Expense)
    for k, v in {**defaults, **kwargs}.items():
        setattr(exp, k, v)
    return exp


def _make_rule(**kwargs) -> RecurringExpense:
    defaults = {
        "id": "rec-1",
        "user_id": "user-1",
        "category_id": "cat-1",
        "description": "Netflix",
        "amount": Decimal("500.00"),
        "currency": "PHP",
        "start_on": date(2026, 1, 15),
        "frequency": "monthly",
        "is_active": True,
        "end_on": None,
        "household_id": None,
    }
    rule = MagicMock(spec=RecurringExpense)
    for k, v in {**defaults, **kwargs}.items():
        setattr(rule, k, v)
    return rule


def _queue_db(db: MagicMock, *result_sets) -> None:
    """Chain db.execute(...).all()/.scalars().all() return values in call order."""
    execute_results = []
    for result_set in result_sets:
        mock_result = MagicMock()
        mock_result.all.return_value = result_set
        mock_result.scalars.return_value.all.return_value = result_set
        execute_results.append(mock_result)
    db.execute.side_effect = execute_results


# --- build_year_export_rows ---


def test_build_year_export_rows_includes_recorded_expense() -> None:
    db = _mock_db()
    expense = _make_expense()
    _queue_db(
        db,
        [("cat-1", "Food")],  # category name map
        [expense],  # recorded expenses
    )

    rows = build_year_export_rows(db, "user-1", 2026, today=date(2026, 12, 31))

    assert len(rows) == 1
    row = rows[0]
    assert row["row_id"] == "exp-1"
    assert row["row_type"] == "recorded"
    assert row["category"] == "Food"
    assert row["amount"] == Decimal("150.00")
    assert row["date"] == date(2026, 1, 5)


def test_build_year_export_rows_projects_future_months_only() -> None:
    db = _mock_db()
    rule = _make_rule(start_on=date(2026, 1, 15))
    # category map, recorded (none), then one project_month() call per month
    # from Feb (today's month is Jan, so Feb..Dec are "future" -> 11 calls)
    future_month_results = [[rule]] + [[] for _ in range(10)]
    _queue_db(
        db,
        [("cat-1", "Subscriptions")],
        [],
        *future_month_results,
    )

    rows = build_year_export_rows(db, "user-1", 2026, today=date(2026, 1, 10))

    assert len(rows) == 1
    row = rows[0]
    assert row["row_id"] is None
    assert row["row_type"] == "projected"
    assert row["category"] == "Subscriptions"
    assert row["recurring_expense_id"] == "rec-1"
    assert row["date"] == date(2026, 2, 15)


def test_build_year_export_rows_does_not_project_current_or_past_months() -> None:
    db = _mock_db()
    _queue_db(db, [], [])

    rows = build_year_export_rows(db, "user-1", 2025, today=date(2026, 7, 1))

    assert rows == []
    # category map + recorded query only -- no project_month calls for a past year
    assert db.execute.call_count == 2


def test_build_year_export_rows_sorted_by_date() -> None:
    db = _mock_db()
    later = _make_expense(id="exp-later", spent_on=date(2026, 3, 1))
    earlier = _make_expense(id="exp-earlier", spent_on=date(2026, 1, 1))
    _queue_db(db, [("cat-1", "Food")], [later, earlier])

    rows = build_year_export_rows(db, "user-1", 2026, today=date(2026, 12, 31))

    assert [row["row_id"] for row in rows] == ["exp-earlier", "exp-later"]


# --- build_export_workbook ---


def test_build_export_workbook_writes_header_and_rows() -> None:
    db = _mock_db()
    expense = _make_expense()
    _queue_db(db, [("cat-1", "Food")], [expense])

    buffer = build_export_workbook(db, "user-1", 2026, today=date(2026, 12, 31))

    workbook = load_workbook(buffer)
    sheet = workbook["Expenses"]
    header = [cell.value for cell in sheet[1]]
    assert header == EXPORT_COLUMNS

    data_row = [cell.value for cell in sheet[2]]
    assert data_row[0] == "exp-1"
    assert data_row[1] == "recorded"
    assert data_row[2] == "Food"
    assert data_row[3] == "Lunch"
    assert data_row[4] == 150.0
    assert data_row[5] == "PHP"


# --- export_filename ---


def test_export_filename_includes_year_and_current_date() -> None:
    assert (
        export_filename(2026, today=date(2026, 7, 5)) == "expenses-2026-2026-07-05.xlsx"
    )
