from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.features.budget.schemas import MonthlySettingUpsert


# --- MonthlySettingUpsert ---


def test_upsert_valid() -> None:
    s = MonthlySettingUpsert(
        monthly_net_salary=Decimal("50000.00"), base_currency="php"
    )
    assert s.monthly_net_salary == Decimal("50000.00")
    assert s.base_currency == "PHP"


def test_upsert_base_currency_optional() -> None:
    s = MonthlySettingUpsert(monthly_net_salary=Decimal("50000"))
    assert s.base_currency is None


def test_upsert_salary_zero_allowed() -> None:
    s = MonthlySettingUpsert(monthly_net_salary=Decimal("0"))
    assert s.monthly_net_salary == Decimal("0")


def test_upsert_salary_negative_fails() -> None:
    with pytest.raises(ValidationError):
        MonthlySettingUpsert(monthly_net_salary=Decimal("-1"))


def test_upsert_currency_too_short_fails() -> None:
    with pytest.raises(ValidationError):
        MonthlySettingUpsert(monthly_net_salary=Decimal("100"), base_currency="P")


def test_upsert_currency_too_long_fails() -> None:
    with pytest.raises(ValidationError):
        MonthlySettingUpsert(monthly_net_salary=Decimal("100"), base_currency="PESO")
