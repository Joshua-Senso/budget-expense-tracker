import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ExpenseAttachment(Base):
    __tablename__ = "expense_attachments"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # ON DELETE CASCADE: an attachment can never outlive its expense, regardless
    # of which code path deletes the expense (single row, installment group,
    # or bulk import delete all issue raw DELETE statements the ORM can't hook).
    expense_id: Mapped[str] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    # Reserved for M6 (households); mirrors the parent expense's household_id.
    household_id: Mapped[str | None] = mapped_column(String, nullable=True)
    object_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_expense_attachments_size_positive"),
        CheckConstraint(
            "object_key <> ''", name="ck_expense_attachments_object_key_nonempty"
        ),
        Index("ix_expense_attachments_expense_id", "expense_id"),
    )
