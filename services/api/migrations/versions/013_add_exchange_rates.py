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
        sa.UniqueConstraint(
            "from_currency", "to_currency", name="ux_exchange_rates_currency_pair"
        ),
    )


def downgrade() -> None:
    op.drop_table("exchange_rates")
