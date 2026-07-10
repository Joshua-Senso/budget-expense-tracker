"""add recurring expenses

Revision ID: 005
Revises: 004
Create Date: 2026-07-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recurring_expenses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("category_id", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("start_on", sa.Date(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("end_on", sa.Date(), nullable=True),
        sa.Column("household_id", sa.String(), nullable=True),
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
        sa.CheckConstraint("amount > 0", name="ck_recurring_expenses_amount_positive"),
        sa.CheckConstraint(
            "description <> ''", name="ck_recurring_expenses_description_nonempty"
        ),
        sa.CheckConstraint(
            "frequency = 'monthly'", name="ck_recurring_expenses_frequency_supported"
        ),
        sa.CheckConstraint(
            "end_on IS NULL OR end_on >= start_on",
            name="ck_recurring_expenses_end_on_after_start",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recurring_expenses_user_active",
        "recurring_expenses",
        ["user_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_recurring_expenses_user_active", table_name="recurring_expenses")
    op.drop_table("recurring_expenses")
