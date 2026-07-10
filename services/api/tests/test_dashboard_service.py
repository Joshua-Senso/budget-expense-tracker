from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.core.households import HouseholdAccessError
from app.features.budget.service import MonthlySettingNotFoundError
from app.features.dashboard.service import get_dashboard_summary, get_yearly_overview


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


def test_get_dashboard_summary_sums_base_amount_not_original_amount() -> None:
    """Regression guard: totals must aggregate the converted base-currency
    amount, not the original per-expense amount -- summing raw `amount`
    across mixed currencies silently produces a wrong total (BUD-51)."""
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        return_value=_make_setting(Decimal("1000.00")),
    ):
        get_dashboard_summary(db, "user-1", "2026-07")

    executed_query = db.execute.call_args[0][0]
    query_str = str(executed_query.compile(compile_kwargs={"literal_binds": True}))
    assert "sum(expenses.base_amount)" in query_str.lower()
    assert "sum(expenses.amount)" not in query_str.lower()


def test_get_dashboard_summary_includes_resolved_base_currency() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    with (
        patch(
            "app.features.dashboard.service.get_monthly_setting",
            return_value=_make_setting(Decimal("1000.00")),
        ),
        patch(
            "app.features.dashboard.service.resolve_base_currency",
            return_value="USD",
        ),
    ):
        result = get_dashboard_summary(db, "user-1", "2026-07")

    assert result["base_currency"] == "USD"


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


# --- get_yearly_overview ---


def test_get_yearly_overview_buckets_by_month_and_group() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = [
        (2, "card", Decimal("300.00")),
        (2, "other", Decimal("50.00")),
        (7, "other", Decimal("100.00")),
    ]

    result = get_yearly_overview(db, "user-1", 2026)

    assert len(result["months"]) == 12
    feb = result["months"][1]
    assert feb["month_key"] == "2026-02"
    assert feb["card_total"] == Decimal("300.00")
    assert feb["other_total"] == Decimal("50.00")
    assert feb["month_total"] == Decimal("350.00")

    jul = result["months"][6]
    assert jul["card_total"] == Decimal("0")
    assert jul["other_total"] == Decimal("100.00")
    assert jul["month_total"] == Decimal("100.00")


def test_get_yearly_overview_no_expenses_returns_zero_totals_for_all_months() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    result = get_yearly_overview(db, "user-1", 2026)

    assert len(result["months"]) == 12
    assert all(month["month_total"] == Decimal("0") for month in result["months"])
    assert result["year_total"] == Decimal("0")


def test_get_yearly_overview_computes_year_total() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = [
        (1, "card", Decimal("100.00")),
        (6, "other", Decimal("250.00")),
        (12, "card", Decimal("75.00")),
    ]

    result = get_yearly_overview(db, "user-1", 2026)

    assert result["year_total"] == Decimal("425.00")


def test_get_yearly_overview_uses_correct_year_bounds() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    get_yearly_overview(db, "user-1", 2026)

    executed_query = db.execute.call_args[0][0]
    query_str = str(executed_query.compile(compile_kwargs={"literal_binds": True}))
    assert "2026-01-01" in query_str
    assert "2026-12-31" in query_str


def test_get_yearly_overview_includes_resolved_base_currency() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    with patch(
        "app.features.dashboard.service.resolve_base_currency", return_value="EUR"
    ):
        result = get_yearly_overview(db, "user-1", 2026)

    assert result["base_currency"] == "EUR"


def test_get_yearly_overview_query_scopes_categories_to_owner() -> None:
    db = _mock_db()
    db.execute.return_value.all.return_value = []

    get_yearly_overview(db, "user-1", 2026)

    executed_query = db.execute.call_args[0][0]
    query_str = str(executed_query.compile(compile_kwargs={"literal_binds": True}))
    assert "user_categories.user_id = 'user-1'" in query_str
    assert "user_categories.household_id IS NULL" in query_str


# --- household scope ---


def test_get_dashboard_summary_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        get_dashboard_summary(db, "user-1", "2026-07", household_id="household-1")


def test_get_dashboard_summary_household_scope_returns_shared_totals() -> None:
    db = _mock_db()
    db.scalar.return_value = "member-1"  # requester is a member of household-1
    db.execute.return_value.all.return_value = [
        ("cat-card", "Groceries", "#FF0000", "card", Decimal("300.00")),
    ]

    result = get_dashboard_summary(db, "user-1", "2026-07", household_id="household-1")

    assert result["card"]["total"] == Decimal("300.00")
    query_str = str(
        db.execute.call_args_list[0][0][0].compile(
            compile_kwargs={"literal_binds": True}
        )
    )
    assert "expenses.household_id = 'household-1'" in query_str
    assert "user_categories.household_id = 'household-1'" in query_str


def test_get_dashboard_summary_household_scope_has_no_personal_salary() -> None:
    """Household-level salary isn't supported yet (PRD §14 open question) --
    a household summary must not leak the caller's personal salary into
    shared totals."""
    db = _mock_db()
    db.scalar.return_value = "member-1"
    db.execute.return_value.all.return_value = []

    with patch(
        "app.features.dashboard.service.get_monthly_setting",
        return_value=_make_setting(Decimal("1000.00")),
    ) as mock_get_setting:
        result = get_dashboard_summary(
            db, "user-1", "2026-07", household_id="household-1"
        )

    mock_get_setting.assert_not_called()
    assert result["monthly_net_salary"] is None
    assert result["remaining"] is None
    assert result["percent_used"] is None


def test_get_yearly_overview_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        get_yearly_overview(db, "user-1", 2026, household_id="household-1")


def test_get_yearly_overview_household_scope_returns_shared_totals() -> None:
    db = _mock_db()
    db.scalar.return_value = "member-1"  # requester is a member of household-1
    db.execute.return_value.all.return_value = [(2, "card", Decimal("300.00"))]

    result = get_yearly_overview(db, "user-1", 2026, household_id="household-1")

    assert result["months"][1]["card_total"] == Decimal("300.00")
    query_str = str(
        db.execute.call_args_list[0][0][0].compile(
            compile_kwargs={"literal_binds": True}
        )
    )
    assert "expenses.household_id = 'household-1'" in query_str
    assert "user_categories.household_id = 'household-1'" in query_str
