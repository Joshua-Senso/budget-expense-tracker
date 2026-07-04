"""add expense installment metadata constraint

Revision ID: 004
Revises: 003
Create Date: 2026-07-05

"""

from collections.abc import Sequence

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_expenses_installment_group_id", "expenses", ["installment_group_id"]
    )
    op.create_check_constraint(
        "ck_expenses_installment_metadata",
        "expenses",
        "(installment_group_id IS NULL AND installment_index IS NULL "
        "AND installment_total IS NULL AND original_description IS NULL) "
        "OR (installment_group_id IS NOT NULL AND installment_index IS NOT NULL "
        "AND installment_total IS NOT NULL AND original_description IS NOT NULL "
        "AND installment_total >= 2 AND installment_index >= 1 "
        "AND installment_index <= installment_total)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_expenses_installment_metadata", "expenses", type_="check")
    op.drop_index("ix_expenses_installment_group_id", table_name="expenses")
