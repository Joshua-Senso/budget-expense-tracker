"""add household scoping indexes

Revision ID: 008
Revises: 007
Create Date: 2026-07-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_expenses_household_spent_on",
        "expenses",
        ["household_id", "spent_on"],
        unique=False,
        postgresql_where=sa.text("household_id IS NOT NULL"),
    )
    op.create_index(
        "ix_recurring_expenses_household_active",
        "recurring_expenses",
        ["household_id", "is_active"],
        unique=False,
        postgresql_where=sa.text("household_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recurring_expenses_household_active",
        table_name="recurring_expenses",
        postgresql_where=sa.text("household_id IS NOT NULL"),
    )
    op.drop_index(
        "ix_expenses_household_spent_on",
        table_name="expenses",
        postgresql_where=sa.text("household_id IS NOT NULL"),
    )
