import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PHP")
    start_on: Mapped[date] = mapped_column(Date, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False, default="monthly")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    end_on: Mapped[date | None] = mapped_column(Date, nullable=True)

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
        Index("ix_recurring_expenses_user_active", "user_id", "is_active"),
    )
