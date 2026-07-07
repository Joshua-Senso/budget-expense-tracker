"""add expense currency check constraint

Revision ID: 010
Revises: 009
Create Date: 2026-07-07

"""

from collections.abc import Sequence

from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_expenses_currency_valid",
        "expenses",
        "currency IN ('AED', 'AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'HKD', "
        "'IDR', 'INR', 'JPY', 'KRW', 'MYR', 'NZD', 'PHP', 'SAR', 'SGD', 'THB', "
        "'USD', 'VND')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_expenses_currency_valid", "expenses", type_="check")
