"""restrict category deletion when referenced

Revision ID: 009
Revises: 008
Create Date: 2026-07-06

"""

from collections.abc import Sequence

from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_expenses_category_id",
        "expenses",
        "user_categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_recurring_expenses_category_id",
        "recurring_expenses",
        "user_categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_recurring_expenses_category_id", "recurring_expenses", type_="foreignkey"
    )
    op.drop_constraint("fk_expenses_category_id", "expenses", type_="foreignkey")
