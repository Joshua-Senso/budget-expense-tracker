from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.features.budget.models import UserMonthlySetting
from app.features.budget.service import (
    MonthlySettingNotFoundError,
    get_monthly_setting,
    upsert_monthly_setting,
)


def _mock_db() -> MagicMock:
    return MagicMock()


def _make_setting(**kwargs) -> UserMonthlySetting:
    defaults = {
        "id": "setting-1",
        "user_id": "user-1",
        "month_key": "2026-07",
        "monthly_net_salary": Decimal("50000.00"),
        "base_currency": None,
        "household_id": None,
    }
    setting = MagicMock(spec=UserMonthlySetting)
    for k, v in {**defaults, **kwargs}.items():
        setattr(setting, k, v)
    return setting


# --- get_monthly_setting ---


def test_get_monthly_setting_found() -> None:
    db = _mock_db()
    setting = _make_setting()
    db.execute.return_value.scalar_one_or_none.return_value = setting

    result = get_monthly_setting(db, "user-1", "2026-07")

    assert result is setting


def test_get_monthly_setting_not_found_raises() -> None:
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(MonthlySettingNotFoundError):
        get_monthly_setting(db, "user-1", "2026-07")


# --- upsert_monthly_setting ---


def test_upsert_monthly_setting_commits_and_returns_current() -> None:
    db = _mock_db()
    setting = _make_setting(monthly_net_salary=Decimal("60000.00"))
    db.execute.return_value.scalar_one_or_none.return_value = setting

    result = upsert_monthly_setting(db, "user-1", "2026-07", Decimal("60000.00"), "PHP")

    assert result is setting
    db.commit.assert_called_once()
    assert db.execute.call_count == 2
