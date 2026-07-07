import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ExchangeRate(Base):
    """A manually maintained currency-pair rate (BUD-52, PRD §7.10/§12).

    Not user- or household-scoped: a rate is objective reference data shared
    by everyone converting that pair, and is the fallback conversion inputs
    reach for when no rate is supplied at entry -- including the
    non-interactive paths (recurring generation, import) that have no user
    present to ask.

    Writes are deliberately open to any authenticated user too, not just the
    household that happens to enter it first: there's no cross-household
    "admin" role in this app to gate it behind, and a wrong maintained rate
    is a correctable, low-stakes mistake (edit it again; already-persisted
    `Expense.base_amount`/`exchange_rate` values are never retroactively
    recomputed from it). `updated_by` records who last set it for that
    audit trail.
    """

    __tablename__ = "exchange_rates"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
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
        UniqueConstraint(
            "from_currency", "to_currency", name="ux_exchange_rates_currency_pair"
        ),
    )
