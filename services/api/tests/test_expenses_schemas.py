from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseInstallmentCreate,
    ExpenseUpdate,
)


# --- ExpenseCreate ---


def test_create_valid() -> None:
    e = ExpenseCreate(
        category_id="cat-1",
        description="Lunch",
        amount=Decimal("150.00"),
        currency="PHP",
        spent_on=date(2026, 7, 1),
    )
    assert e.description == "Lunch"
    assert e.amount == Decimal("150.00")
    assert e.currency == "PHP"


def test_create_currency_defaults_php() -> None:
    e = ExpenseCreate(
        category_id="cat-1",
        description="Lunch",
        amount=Decimal("150"),
        spent_on=date(2026, 7, 1),
    )
    assert e.currency == "PHP"


def test_create_currency_uppercased() -> None:
    e = ExpenseCreate(
        category_id="cat-1",
        description="Lunch",
        amount=Decimal("100"),
        currency="usd",
        spent_on=date(2026, 7, 1),
    )
    assert e.currency == "USD"


def test_create_currency_too_long_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(
            category_id="cat-1",
            description="Lunch",
            amount=Decimal("100"),
            currency="peso",
            spent_on=date(2026, 7, 1),
        )


def test_create_currency_too_short_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(
            category_id="cat-1",
            description="Lunch",
            amount=Decimal("100"),
            currency="PH",
            spent_on=date(2026, 7, 1),
        )


def test_create_description_stripped() -> None:
    e = ExpenseCreate(
        category_id="cat-1",
        description="  Coffee  ",
        amount=Decimal("50"),
        spent_on=date(2026, 7, 1),
    )
    assert e.description == "Coffee"


def test_create_blank_description_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(
            category_id="cat-1",
            description="   ",
            amount=Decimal("100"),
            spent_on=date(2026, 7, 1),
        )


def test_create_zero_amount_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(
            category_id="cat-1",
            description="Lunch",
            amount=Decimal("0"),
            spent_on=date(2026, 7, 1),
        )


def test_create_negative_amount_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(
            category_id="cat-1",
            description="Lunch",
            amount=Decimal("-10"),
            spent_on=date(2026, 7, 1),
        )


def test_create_amount_quantized_to_2dp() -> None:
    e = ExpenseCreate(
        category_id="cat-1",
        description="Lunch",
        amount=Decimal("150.999"),
        spent_on=date(2026, 7, 1),
    )
    assert e.amount == Decimal("151.00")


def test_create_amount_overflow_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(
            category_id="cat-1",
            description="Lunch",
            amount=Decimal("10000000000"),
            spent_on=date(2026, 7, 1),
        )


def test_create_amount_extreme_magnitude_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(
            category_id="cat-1",
            description="Lunch",
            amount=Decimal("1e30"),
            spent_on=date(2026, 7, 1),
        )


# --- ExpenseInstallmentCreate ---


def test_installment_create_valid() -> None:
    e = ExpenseInstallmentCreate(
        category_id="cat-1",
        description="TV",
        amount=Decimal("1000"),
        spent_on=date(2026, 7, 1),
        installment_total=12,
    )
    assert e.installment_total == 12


def test_installment_create_total_of_one_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseInstallmentCreate(
            category_id="cat-1",
            description="TV",
            amount=Decimal("1000"),
            spent_on=date(2026, 7, 1),
            installment_total=1,
        )


def test_installment_create_total_too_high_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseInstallmentCreate(
            category_id="cat-1",
            description="TV",
            amount=Decimal("1000"),
            spent_on=date(2026, 7, 1),
            installment_total=61,
        )


def test_installment_create_blank_description_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseInstallmentCreate(
            category_id="cat-1",
            description="   ",
            amount=Decimal("1000"),
            spent_on=date(2026, 7, 1),
            installment_total=12,
        )


# --- ExpenseUpdate ---


def test_update_all_none_is_valid() -> None:
    u = ExpenseUpdate()
    assert u.description is None
    assert u.amount is None


def test_update_partial_fields() -> None:
    u = ExpenseUpdate(description="Dinner", amount=Decimal("300"))
    assert u.description == "Dinner"
    assert u.amount == Decimal("300")


def test_update_blank_description_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseUpdate(description="  ")


def test_update_zero_amount_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseUpdate(amount=Decimal("0"))


def test_update_currency_uppercased() -> None:
    u = ExpenseUpdate(currency="eur")
    assert u.currency == "EUR"


def test_update_currency_too_long_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseUpdate(currency="euro")


def test_update_amount_quantized_to_2dp() -> None:
    u = ExpenseUpdate(amount=Decimal("99.999"))
    assert u.amount == Decimal("100.00")


def test_update_amount_overflow_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseUpdate(amount=Decimal("10000000000"))


def test_update_amount_extreme_magnitude_fails() -> None:
    with pytest.raises(ValidationError):
        ExpenseUpdate(amount=Decimal("1e30"))
