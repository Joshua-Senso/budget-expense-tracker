from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator, model_validator

from app.features.currency.codes import SUPPORTED_CURRENCIES


def _validate_currency(v: str) -> str:
    upper = v.strip().upper()
    if upper not in SUPPORTED_CURRENCIES:
        raise ValueError(
            f"currency must be one of: {', '.join(sorted(SUPPORTED_CURRENCIES))}"
        )
    return upper


class ExchangeRateUpsert(BaseModel):
    from_currency: str
    to_currency: str
    rate: Decimal
    household_id: str | None = None

    @field_validator("from_currency", "to_currency")
    @classmethod
    def currency_valid(cls, v: str) -> str:
        return _validate_currency(v)

    @field_validator("rate")
    @classmethod
    def rate_valid(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("rate must be positive")
        return v

    @model_validator(mode="after")
    def currencies_distinct(self) -> "ExchangeRateUpsert":
        if self.from_currency == self.to_currency:
            raise ValueError("from_currency and to_currency must differ")
        return self


class ExchangeRateResponse(BaseModel):
    id: str
    user_id: str
    household_id: str | None = None
    from_currency: str
    to_currency: str
    rate: Decimal
    updated_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
