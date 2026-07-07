from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.features.currency.codes import DEFAULT_CURRENCY
from app.features.currency.service import (
    ExchangeRateRequiredError,
    convert_to_base,
    month_key_for,
    resolve_base_currency,
)


def _mock_db() -> MagicMock:
    return MagicMock()


# --- resolve_base_currency ---


def test_resolve_base_currency_household_scope_uses_organization_base_currency() -> (
    None
):
    db = _mock_db()
    db.scalar.return_value = "USD"

    result = resolve_base_currency(db, "user-1", "2026-07", household_id="household-1")

    assert result == "USD"


def test_resolve_base_currency_household_scope_falls_back_when_org_missing() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    result = resolve_base_currency(db, "user-1", "2026-07", household_id="household-1")

    assert result == DEFAULT_CURRENCY


def test_resolve_base_currency_personal_scope_uses_monthly_setting() -> None:
    db = _mock_db()
    db.scalar.return_value = "EUR"

    result = resolve_base_currency(db, "user-1", "2026-07", household_id=None)

    assert result == "EUR"


def test_resolve_base_currency_personal_scope_defaults_to_php() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    result = resolve_base_currency(db, "user-1", "2026-07", household_id=None)

    assert result == DEFAULT_CURRENCY


# --- convert_to_base ---


def test_convert_to_base_same_currency_forces_rate_to_one() -> None:
    base_amount, exchange_rate = convert_to_base(
        Decimal("150.00"), "PHP", "PHP", exchange_rate=Decimal("58.00")
    )

    assert base_amount == Decimal("150.00")
    assert exchange_rate == Decimal("1")


def test_convert_to_base_requires_rate_when_currency_differs() -> None:
    with pytest.raises(ExchangeRateRequiredError) as exc_info:
        convert_to_base(Decimal("100.00"), "USD", "PHP", exchange_rate=None)

    assert exc_info.value.currency == "USD"
    assert exc_info.value.base_currency == "PHP"


def test_convert_to_base_computes_and_rounds_base_amount() -> None:
    base_amount, exchange_rate = convert_to_base(
        Decimal("100.00"), "USD", "PHP", exchange_rate=Decimal("56.789")
    )

    assert base_amount == Decimal("5678.90")
    assert exchange_rate == Decimal("56.789")


# --- month_key_for ---


def test_month_key_for_pads_single_digit_months() -> None:
    assert month_key_for(date(2026, 1, 5)) == "2026-01"
    assert month_key_for(date(2026, 12, 25)) == "2026-12"
