"""add user monthly settings

Revision ID: 003
Revises: 002
Create Date: 2026-07-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_monthly_settings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("month_key", sa.String(7), nullable=False),
        sa.Column("monthly_net_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("base_currency", sa.String(3), nullable=True),
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
        sa.CheckConstraint(
            "monthly_net_salary >= 0", name="ck_user_monthly_settings_salary_nonneg"
        ),
        sa.CheckConstraint(
            "month_key ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'",
            name="ck_user_monthly_settings_month_key_format",
        ),
        sa.CheckConstraint(
            "base_currency IS NULL OR base_currency ~ '^[A-Z]{3}$'",
            name="ck_user_monthly_settings_currency_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_monthly_settings_user_id", "user_monthly_settings", ["user_id"]
    )
    op.create_index(
        "ix_user_monthly_settings_user_month",
        "user_monthly_settings",
        ["user_id", "month_key"],
        unique=True,
        postgresql_where=sa.text("household_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_monthly_settings_user_month",
        table_name="user_monthly_settings",
        postgresql_where=sa.text("household_id IS NULL"),
    )
    op.drop_index(
        "ix_user_monthly_settings_user_id", table_name="user_monthly_settings"
    )
    op.drop_table("user_monthly_settings")
