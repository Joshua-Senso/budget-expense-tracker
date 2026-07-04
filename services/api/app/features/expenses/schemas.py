import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from pydantic import BaseModel, field_validator


_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_MAX_AMOUNT = Decimal("9999999999.99")
_MIN_INSTALLMENT_TOTAL = 2
_MAX_INSTALLMENT_TOTAL = 60


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


class ExpenseCreate(BaseModel):
    category_id: str
    description: str
    amount: Decimal
    currency: str = "PHP"
    spent_on: date

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


class ExpenseInstallmentCreate(ExpenseCreate):
    installment_total: int

    @field_validator("installment_total")
    @classmethod
    def installment_total_valid(cls, v: int) -> int:
        if not (_MIN_INSTALLMENT_TOTAL <= v <= _MAX_INSTALLMENT_TOTAL):
            raise ValueError(
                f"installment_total must be between {_MIN_INSTALLMENT_TOTAL} "
                f"and {_MAX_INSTALLMENT_TOTAL}"
            )
        return v


class ExpenseUpdate(BaseModel):
    category_id: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    spent_on: date | None = None

    @field_validator("description")
    @classmethod
    def description_nonempty(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("description must not be blank")
        return stripped

    @field_validator("amount")
    @classmethod
    def amount_valid(cls, v: Decimal | None) -> Decimal | None:
        return _validate_amount(v) if v is not None else None

    @field_validator("currency")
    @classmethod
    def currency_valid(cls, v: str | None) -> str | None:
        return _validate_currency(v) if v is not None else None


class ExpenseResponse(BaseModel):
    id: str
    user_id: str
    category_id: str
    description: str
    amount: Decimal
    currency: str
    spent_on: date
    installment_group_id: str | None = None
    installment_index: int | None = None
    installment_total: int | None = None
    original_description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
