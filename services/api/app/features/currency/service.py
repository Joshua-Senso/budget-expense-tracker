from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.households import get_household_base_currency
from app.features.budget.models import UserMonthlySetting
from app.features.currency.codes import DEFAULT_CURRENCY

_AMOUNT_QUANT = Decimal("0.01")


class ExchangeRateRequiredError(Exception):
    """Raised when converting a non-base-currency amount with no rate given."""

    def __init__(self, currency: str, base_currency: str) -> None:
        self.currency = currency
        self.base_currency = base_currency
        self.detail = (
            f"exchange_rate is required to convert {currency} to {base_currency}."
        )
        super().__init__(self.detail)


def validate_exchange_rate(v: Decimal | None) -> Decimal | None:
    if v is None:
        return None
    if v <= 0:
        raise ValueError("exchange_rate must be positive")
    return v


def resolve_base_currency(
    db: Session, user_id: str, month_key: str, household_id: str | None
) -> str:
    """The base currency for the given scope/month (PRD §7.10, §9.4, §9.5).

    A household's base currency always wins in shared scope. In personal
    scope, the user's per-month preference applies if set, else PHP.
    """
    if household_id is not None:
        base_currency = get_household_base_currency(db, household_id)
        return base_currency if base_currency is not None else DEFAULT_CURRENCY

    base_currency = db.scalar(
        select(UserMonthlySetting.base_currency).where(
            UserMonthlySetting.user_id == user_id,
            UserMonthlySetting.household_id.is_(None),
            UserMonthlySetting.month_key == month_key,
        )
    )
    return base_currency if base_currency is not None else DEFAULT_CURRENCY


def month_key_for(spent_on: date) -> str:
    return f"{spent_on.year:04d}-{spent_on.month:02d}"


def convert_to_base(
    amount: Decimal,
    currency: str,
    base_currency: str,
    exchange_rate: Decimal | None,
) -> tuple[Decimal, Decimal]:
    """Convert `amount` (in `currency`) to `base_currency`.

    Returns `(base_amount, exchange_rate)` to persist. Same-currency amounts
    are never converted -- any client-supplied rate is ignored and `1` is
    stored, so a household/user base-currency change later can't be
    misread as "this row was converted at some point".
    """
    if currency == base_currency:
        return amount, Decimal("1")
    if exchange_rate is None:
        raise ExchangeRateRequiredError(currency, base_currency)
    base_amount = (amount * exchange_rate).quantize(
        _AMOUNT_QUANT, rounding=ROUND_HALF_UP
    )
    return base_amount, exchange_rate


def convert_to_base_or_unconverted(
    amount: Decimal,
    currency: str,
    base_currency: str,
    exchange_rate: Decimal | None,
) -> tuple[Decimal, Decimal]:
    """Same as `convert_to_base`, but for call sites with no interactive
    moment to supply a missing rate (the recurring worker, bulk import).
    Falls back to recording the amount unconverted (rate `1`) rather than
    failing the whole batch -- see PRD §13's accepted stale-rate risk.
    """
    try:
        return convert_to_base(amount, currency, base_currency, exchange_rate)
    except ExchangeRateRequiredError:
        return amount, Decimal("1")
