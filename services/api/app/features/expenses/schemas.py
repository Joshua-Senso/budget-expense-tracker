from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


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
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def currency_nonempty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("currency must not be blank")
        return stripped.upper()


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
    def amount_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("amount must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def currency_nonempty(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("currency must not be blank")
        return stripped.upper()


class ExpenseResponse(BaseModel):
    id: str
    user_id: str
    category_id: str
    description: str
    amount: Decimal
    currency: str
    spent_on: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
