import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.features.currency.codes import DEFAULT_CURRENCY


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    # ON DELETE RESTRICT: see the matching comment on Expense.category_id --
    # the DB, not an app-level check, is what makes a category delete safe
    # against a concurrent insert referencing it.
    category_id: Mapped[str] = mapped_column(
        ForeignKey(
            "user_categories.id",
            name="fk_recurring_expenses_category_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default=DEFAULT_CURRENCY
    )
    start_on: Mapped[date] = mapped_column(Date, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False, default="monthly")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    end_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Captured once at rule-creation time (no user is present when the
    # worker generates each month's occurrence); NULL when currency already
    # matched the base currency at creation, so no rate was ever needed.
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)

    # Reserved for M6 (households)
    household_id: Mapped[str | None] = mapped_column(String, nullable=True)

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
        CheckConstraint("amount > 0", name="ck_recurring_expenses_amount_positive"),
        CheckConstraint(
            "description <> ''", name="ck_recurring_expenses_description_nonempty"
        ),
        CheckConstraint(
            "frequency = 'monthly'", name="ck_recurring_expenses_frequency_supported"
        ),
        CheckConstraint(
            "end_on IS NULL OR end_on >= start_on",
            name="ck_recurring_expenses_end_on_after_start",
        ),
        # Keep in sync with app.features.currency.codes.SUPPORTED_CURRENCIES
        CheckConstraint(
            "currency IN ('AED', 'AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'HKD', "
            "'IDR', 'INR', 'JPY', 'KRW', 'MYR', 'NZD', 'PHP', 'SAR', 'SGD', 'THB', "
            "'USD', 'VND')",
            name="ck_recurring_expenses_currency_valid",
        ),
        Index("ix_recurring_expenses_user_active", "user_id", "is_active"),
        Index(
            "ix_recurring_expenses_household_active",
            "household_id",
            "is_active",
            postgresql_where=text("household_id IS NOT NULL"),
        ),
    )
