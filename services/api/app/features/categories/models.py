import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UserCategory(Base):
    __tablename__ = "user_categories"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # household_id is null for personal categories; set when shared via a household (M6).
    household_id: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    expense_group: Mapped[str] = mapped_column(String, nullable=False)
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
        CheckConstraint("name <> ''", name="ck_user_categories_name_nonempty"),
        CheckConstraint(
            "color ~ '^#[0-9A-Fa-f]{6}$'", name="ck_user_categories_color_hex"
        ),
        CheckConstraint(
            "expense_group IN ('card', 'other')",
            name="ck_user_categories_group_valid",
        ),
        # Name unique within personal scope (no household)
        Index(
            "ix_user_categories_user_name",
            "user_id",
            "name",
            unique=True,
            postgresql_where=text("household_id IS NULL"),
        ),
        # Name unique within household scope
        Index(
            "ix_user_categories_household_name",
            "household_id",
            "name",
            unique=True,
            postgresql_where=text("household_id IS NOT NULL"),
        ),
    )
