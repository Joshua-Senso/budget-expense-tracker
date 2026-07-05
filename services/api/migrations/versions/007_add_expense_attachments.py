"""add expense attachments

Revision ID: 007
Revises: 006
Create Date: 2026-07-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expense_attachments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("expense_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("household_id", sa.String(), nullable=True),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "object_key <> ''", name="ck_expense_attachments_object_key_nonempty"
        ),
        sa.CheckConstraint(
            "size_bytes > 0", name="ck_expense_attachments_size_positive"
        ),
        sa.ForeignKeyConstraint(
            ["expense_id"],
            ["expenses.id"],
            name="fk_expense_attachments_expense_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index(
        "ix_expense_attachments_expense_id",
        "expense_attachments",
        ["expense_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_expense_attachments_expense_id", table_name="expense_attachments")
    op.drop_table("expense_attachments")
