"""add exchange rate to recurring expenses and enforce expense conversion

Revision ID: 012
Revises: 011
Create Date: 2026-07-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recurring_expenses",
        sa.Column("exchange_rate", sa.Numeric(18, 6), nullable=True),
    )

    # Backfill rows created before BUD-51 (base_amount/exchange_rate were
    # reserved but never populated): treat them as already in their scope's
    # base currency, since no historical rate was captured for them.
    op.execute(
        "UPDATE expenses SET base_amount = amount, exchange_rate = 1 "
        "WHERE base_amount IS NULL"
    )
    op.alter_column("expenses", "base_amount", nullable=False)
    op.alter_column("expenses", "exchange_rate", nullable=False)


def downgrade() -> None:
    op.alter_column("expenses", "exchange_rate", nullable=True)
    op.alter_column("expenses", "base_amount", nullable=True)
    op.drop_column("recurring_expenses", "exchange_rate")
