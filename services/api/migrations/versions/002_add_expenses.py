"""add expenses

Revision ID: 002
Revises: 001
Create Date: 2026-07-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("category_id", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("spent_on", sa.Date(), nullable=False),
        sa.Column("installment_group_id", sa.String(), nullable=True),
        sa.Column("installment_index", sa.Integer(), nullable=True),
        sa.Column("installment_total", sa.Integer(), nullable=True),
        sa.Column("original_description", sa.String(), nullable=True),
        sa.Column("household_id", sa.String(), nullable=True),
        sa.Column("base_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("exchange_rate", sa.Numeric(18, 6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        sa.CheckConstraint(
            "description <> ''", name="ck_expenses_description_nonempty"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expenses_user_spent_on", "expenses", ["user_id", "spent_on"])


def downgrade() -> None:
    op.drop_index("ix_expenses_user_spent_on", table_name="expenses")
    op.drop_table("expenses")
