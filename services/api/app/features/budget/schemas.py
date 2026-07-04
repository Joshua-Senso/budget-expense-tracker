import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class MonthlySettingUpsert(BaseModel):
    monthly_net_salary: Decimal
    base_currency: str | None = None

    @field_validator("monthly_net_salary")
    @classmethod
    def salary_nonneg(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("monthly_net_salary must be zero or greater")
        return v

    @field_validator("base_currency")
    @classmethod
    def currency_valid(cls, v: str | None) -> str | None:
        if v is None:
            return None
        upper = v.strip().upper()
        if not _CURRENCY_RE.match(upper):
            raise ValueError("base_currency must be a 3-letter ISO 4217 code, e.g. PHP")
        return upper


class MonthlySettingResponse(BaseModel):
    id: str
    user_id: str
    month_key: str
    monthly_net_salary: Decimal
    base_currency: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
