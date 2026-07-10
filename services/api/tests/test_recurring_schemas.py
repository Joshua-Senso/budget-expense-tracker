from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.features.recurring.schemas import RecurringExpenseCreate

# --- RecurringExpenseCreate ---


def test_create_valid() -> None:
    r = RecurringExpenseCreate(
        category_id="cat-1",
        description="Netflix",
        amount=Decimal("500.00"),
        currency="PHP",
        start_on=date(2026, 1, 15),
    )
    assert r.description == "Netflix"
    assert r.amount == Decimal("500.00")
    assert r.end_on is None


def test_create_currency_defaults_php() -> None:
    r = RecurringExpenseCreate(
        category_id="cat-1",
        description="Netflix",
        amount=Decimal("500"),
        start_on=date(2026, 1, 15),
    )
    assert r.currency == "PHP"


def test_create_currency_uppercased() -> None:
    r = RecurringExpenseCreate(
        category_id="cat-1",
        description="Netflix",
        amount=Decimal("500"),
        currency="usd",
        start_on=date(2026, 1, 15),
    )
    assert r.currency == "USD"


def test_create_currency_unsupported_code_fails() -> None:
    with pytest.raises(ValidationError):
        RecurringExpenseCreate(
            category_id="cat-1",
            description="Netflix",
            amount=Decimal("500"),
            currency="ZZZ",
            start_on=date(2026, 1, 15),
        )


def test_create_blank_description_fails() -> None:
    with pytest.raises(ValidationError):
        RecurringExpenseCreate(
            category_id="cat-1",
            description="   ",
            amount=Decimal("500"),
            start_on=date(2026, 1, 15),
        )


def test_create_zero_amount_fails() -> None:
    with pytest.raises(ValidationError):
        RecurringExpenseCreate(
            category_id="cat-1",
            description="Netflix",
            amount=Decimal("0"),
            start_on=date(2026, 1, 15),
        )


def test_create_amount_quantized_to_2dp() -> None:
    r = RecurringExpenseCreate(
        category_id="cat-1",
        description="Netflix",
        amount=Decimal("500.999"),
        start_on=date(2026, 1, 15),
    )
    assert r.amount == Decimal("501.00")


def test_create_with_end_on_after_start_valid() -> None:
    r = RecurringExpenseCreate(
        category_id="cat-1",
        description="Netflix",
        amount=Decimal("500"),
        start_on=date(2026, 1, 15),
        end_on=date(2026, 6, 30),
    )
    assert r.end_on == date(2026, 6, 30)


def test_create_end_on_before_start_fails() -> None:
    with pytest.raises(ValidationError):
        RecurringExpenseCreate(
            category_id="cat-1",
            description="Netflix",
            amount=Decimal("500"),
            start_on=date(2026, 6, 30),
            end_on=date(2026, 1, 15),
        )


# --- exchange_rate ---


def test_create_exchange_rate_optional() -> None:
    r = RecurringExpenseCreate(
        category_id="cat-1",
        description="Netflix",
        amount=Decimal("10"),
        currency="USD",
        start_on=date(2026, 1, 15),
    )
    assert r.exchange_rate is None


def test_create_exchange_rate_accepted() -> None:
    r = RecurringExpenseCreate(
        category_id="cat-1",
        description="Netflix",
        amount=Decimal("10"),
        currency="USD",
        start_on=date(2026, 1, 15),
        exchange_rate=Decimal("56.00"),
    )
    assert r.exchange_rate == Decimal("56.00")


def test_create_exchange_rate_zero_fails() -> None:
    with pytest.raises(ValidationError):
        RecurringExpenseCreate(
            category_id="cat-1",
            description="Netflix",
            amount=Decimal("10"),
            currency="USD",
            start_on=date(2026, 1, 15),
            exchange_rate=Decimal("0"),
        )
