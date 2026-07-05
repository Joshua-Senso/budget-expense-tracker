"""add recurring expense id to expenses

Revision ID: 006
Revises: 005
Create Date: 2026-07-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "expenses", sa.Column("recurring_expense_id", sa.String(), nullable=True)
    )
    op.create_index(
        "ux_expenses_recurring_expense_id_spent_on",
        "expenses",
        ["recurring_expense_id", "spent_on"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_expenses_recurring_expense_id_spent_on", table_name="expenses")
    op.drop_column("expenses", "recurring_expense_id")
