"""add exchange_rates

Revision ID: 013
Revises: 012
Create Date: 2026-07-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CURRENCY_CODES = (
    "'AED', 'AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'HKD', "
    "'IDR', 'INR', 'JPY', 'KRW', 'MYR', 'NZD', 'PHP', 'SAR', 'SGD', 'THB', "
    "'USD', 'VND'"
)


def upgrade() -> None:
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("household_id", sa.String(), nullable=True),
        sa.Column("from_currency", sa.String(3), nullable=False),
        sa.Column("to_currency", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 6), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
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
        sa.CheckConstraint("rate > 0", name="ck_exchange_rates_rate_positive"),
        sa.CheckConstraint(
            "from_currency <> to_currency", name="ck_exchange_rates_distinct_currencies"
        ),
        sa.CheckConstraint(
            f"from_currency IN ({_CURRENCY_CODES})",
            name="ck_exchange_rates_from_currency_valid",
        ),
        sa.CheckConstraint(
            f"to_currency IN ({_CURRENCY_CODES})",
            name="ck_exchange_rates_to_currency_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exchange_rates_user_id", "exchange_rates", ["user_id"])
    op.create_index(
        "ux_exchange_rates_user_pair",
        "exchange_rates",
        ["user_id", "from_currency", "to_currency"],
        unique=True,
        postgresql_where=sa.text("household_id IS NULL"),
    )
    op.create_index(
        "ux_exchange_rates_household_pair",
        "exchange_rates",
        ["household_id", "from_currency", "to_currency"],
        unique=True,
        postgresql_where=sa.text("household_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ux_exchange_rates_household_pair", table_name="exchange_rates")
    op.drop_index("ux_exchange_rates_user_pair", table_name="exchange_rates")
    op.drop_index("ix_exchange_rates_user_id", table_name="exchange_rates")
    op.drop_table("exchange_rates")
