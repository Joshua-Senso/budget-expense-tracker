import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_MAX_AMOUNT = Decimal("9999999999.99")


def _validate_currency(v: str) -> str:
    upper = v.strip().upper()
    if not _CURRENCY_RE.match(upper):
        raise ValueError("currency must be a 3-letter ISO 4217 code, e.g. PHP")
    return upper


def _validate_amount(v: Decimal) -> Decimal:
    if v <= 0:
        raise ValueError("amount must be positive")
    try:
        quantized = v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError("amount exceeds maximum allowed value")
    if quantized > _MAX_AMOUNT:
        raise ValueError("amount exceeds maximum allowed value")
    return quantized


class RecurringExpenseCreate(BaseModel):
    category_id: str
    description: str
    amount: Decimal
    currency: str = "PHP"
    start_on: date
    end_on: date | None = None
    household_id: str | None = None

    @field_validator("description")
    @classmethod
    def description_nonempty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("description must not be blank")
        return stripped

    @field_validator("amount")
    @classmethod
    def amount_valid(cls, v: Decimal) -> Decimal:
        return _validate_amount(v)

    @field_validator("currency")
    @classmethod
    def currency_valid(cls, v: str) -> str:
        return _validate_currency(v)

    @model_validator(mode="after")
    def end_on_after_start(self) -> "RecurringExpenseCreate":
        if self.end_on is not None and self.end_on < self.start_on:
            raise ValueError("end_on must not be before start_on")
        return self


class RecurringExpenseResponse(BaseModel):
    id: str
    user_id: str
    household_id: str | None = None
    category_id: str
    description: str
    amount: Decimal
    currency: str
    start_on: date
    frequency: str
    is_active: bool
    end_on: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectedExpense(BaseModel):
    recurring_expense_id: str
    category_id: str
    description: str
    amount: Decimal
    currency: str
    spent_on: date
    source: Literal["generated"] = "generated"
