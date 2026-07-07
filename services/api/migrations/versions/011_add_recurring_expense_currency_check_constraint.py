"""add recurring expense currency check constraint

Revision ID: 011
Revises: 010
Create Date: 2026-07-07

"""

from collections.abc import Sequence

from alembic import op

revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_recurring_expenses_currency_valid",
        "recurring_expenses",
        "currency IN ('AED', 'AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'HKD', "
        "'IDR', 'INR', 'JPY', 'KRW', 'MYR', 'NZD', 'PHP', 'SAR', 'SGD', 'THB', "
        "'USD', 'VND')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_recurring_expenses_currency_valid", "recurring_expenses", type_="check"
    )
