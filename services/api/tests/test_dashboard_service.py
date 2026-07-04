from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.features.budget.service import MonthlySettingNotFoundError
from app.features.dashboard.service import get_dashboard_summary


def _mock_db() -> MagicMock:
    return MagicMock()


def _make_setting(monthly_net_salary: Decimal) -> MagicMock:
    setting = MagicMock()
    setting.monthly_net_salary = monthly_net_salary
    return setting


# --- get_dashboard_summary ---


def test_get_dashboard_summary_buckets_by_expense_group() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = [
        ("cat-card", "Groceries", "#FF0000", "card", Decimal("300.00")),
        ("cat-other", "Utilities", "#00FF00", "other", Decimal("100.00")),
    ]

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        return_value=_make_setting(Decimal("1000.00")),
    ):
        result = get_dashboard_summary(db, "user-1", "2026-07")

    assert result["card"]["total"] == Decimal("300.00")
    assert result["card"]["categories"] == [
        {
            "category_id": "cat-card",
            "name": "Groceries",
            "color": "#FF0000",
            "total": Decimal("300.00"),
        }
    ]
    assert result["other"]["total"] == Decimal("100.00")
    assert result["month_total"] == Decimal("400.00")


def test_get_dashboard_summary_no_expenses_returns_zero_totals() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        return_value=_make_setting(Decimal("1000.00")),
    ):
        result = get_dashboard_summary(db, "user-1", "2026-07")

    assert result["card"]["total"] == Decimal("0")
    assert result["other"]["total"] == Decimal("0")
    assert result["month_total"] == Decimal("0")
    assert result["card"]["categories"] == []


def test_get_dashboard_summary_no_salary_set_returns_none_fields() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        side_effect=MonthlySettingNotFoundError("2026-07"),
    ):
        result = get_dashboard_summary(db, "user-1", "2026-07")

    assert result["monthly_net_salary"] is None
    assert result["remaining"] is None
    assert result["percent_used"] is None


def test_get_dashboard_summary_remaining_and_percent_used_computed() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = [
        ("cat-card", "Groceries", "#FF0000", "card", Decimal("250.00")),
    ]

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        return_value=_make_setting(Decimal("1000.00")),
    ):
        result = get_dashboard_summary(db, "user-1", "2026-07")

    assert result["remaining"] == Decimal("750.00")
    assert result["percent_used"] == Decimal("25.00")


def test_get_dashboard_summary_zero_salary_skips_percent_used() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        return_value=_make_setting(Decimal("0")),
    ):
        result = get_dashboard_summary(db, "user-1", "2026-07")

    assert result["remaining"] == Decimal("0")
    assert result["percent_used"] is None


def test_get_dashboard_summary_uses_correct_month_bounds() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        return_value=_make_setting(Decimal("1000.00")),
    ):
        get_dashboard_summary(db, "user-1", "2026-02")

    executed_query = db.execute.call_args[0][0]
    query_str = str(executed_query.compile(compile_kwargs={"literal_binds": True}))
    assert "2026-02-01" in query_str
    assert "2026-02-28" in query_str


def test_get_dashboard_summary_query_scopes_categories_to_owner() -> None:
    # Regression guard: the join must not rely solely on expenses.user_id —
    # it must also assert user_categories.user_id/household_id so a future
    # write-time bypass can't leak another user's category data here.
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        return_value=_make_setting(Decimal("1000.00")),
    ):
        get_dashboard_summary(db, "user-1", "2026-07")

    executed_query = db.execute.call_args[0][0]
    query_str = str(executed_query.compile(compile_kwargs={"literal_binds": True}))
    assert "user_categories.user_id = 'user-1'" in query_str
    assert "user_categories.household_id IS NULL" in query_str
