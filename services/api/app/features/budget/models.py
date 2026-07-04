import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UserMonthlySetting(Base):
    __tablename__ = "user_monthly_settings"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    month_key: Mapped[str] = mapped_column(String(7), nullable=False)
    monthly_net_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    base_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

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
        CheckConstraint(
            "monthly_net_salary >= 0", name="ck_user_monthly_settings_salary_nonneg"
        ),
        CheckConstraint(
            "month_key ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'",
            name="ck_user_monthly_settings_month_key_format",
        ),
        CheckConstraint(
            "base_currency IS NULL OR base_currency ~ '^[A-Z]{3}$'",
            name="ck_user_monthly_settings_currency_valid",
        ),
        # One setting per user per month within personal scope (no household)
        Index(
            "ix_user_monthly_settings_user_month",
            "user_id",
            "month_key",
            unique=True,
            postgresql_where=text("household_id IS NULL"),
        ),
    )
