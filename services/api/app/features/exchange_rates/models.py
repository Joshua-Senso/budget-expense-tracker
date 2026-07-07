import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ExchangeRate(Base):
    """A manually maintained currency-pair rate (BUD-52, PRD §7.10/§12).

    Scoped like `UserCategory`/`Expense`: personal (`user_id`, `household_id`
    IS NULL) or shared within a household (`household_id` set; any member
    may read/add, only the owner role may edit/delete -- PRD §10). Each
    scope maintains its own rates rather than one instance-wide table, so a
    member of one household can't change or delete the rate that drives
    another, unrelated household's conversions.
    """

    __tablename__ = "exchange_rates"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    household_id: Mapped[str | None] = mapped_column(String, nullable=True)
    from_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    updated_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("rate > 0", name="ck_exchange_rates_rate_positive"),
        CheckConstraint(
            "from_currency <> to_currency", name="ck_exchange_rates_distinct_currencies"
        ),
        # Keep in sync with app.features.currency.codes.SUPPORTED_CURRENCIES
        CheckConstraint(
            "from_currency IN ('AED', 'AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'HKD', "
            "'IDR', 'INR', 'JPY', 'KRW', 'MYR', 'NZD', 'PHP', 'SAR', 'SGD', 'THB', "
            "'USD', 'VND')",
            name="ck_exchange_rates_from_currency_valid",
        ),
        CheckConstraint(
            "to_currency IN ('AED', 'AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'HKD', "
            "'IDR', 'INR', 'JPY', 'KRW', 'MYR', 'NZD', 'PHP', 'SAR', 'SGD', 'THB', "
            "'USD', 'VND')",
            name="ck_exchange_rates_to_currency_valid",
        ),
        # Pair unique within personal scope (no household)
        Index(
            "ux_exchange_rates_user_pair",
            "user_id",
            "from_currency",
            "to_currency",
            unique=True,
            postgresql_where=text("household_id IS NULL"),
        ),
        # Pair unique within household scope
        Index(
            "ux_exchange_rates_household_pair",
            "household_id",
            "from_currency",
            "to_currency",
            unique=True,
            postgresql_where=text("household_id IS NOT NULL"),
        ),
    )
