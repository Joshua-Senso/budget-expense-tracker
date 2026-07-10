"""restrict category deletion when referenced

Revision ID: 009
Revises: 008
Create Date: 2026-07-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _warn_on_orphaned_category_ids(table: str) -> None:
    # Deployment safety: a plain ADD CONSTRAINT scans and validates every
    # existing row, so a category_id orphaned under the pre-fix rules (e.g. a
    # category deleted before this PR's in-use guard existed) would abort the
    # migration outright. We add the FK NOT VALID below instead -- Postgres
    # still enforces it for every new insert/update/delete from this point on,
    # it just skips validating pre-existing rows. This surfaces any orphans
    # that slipped through so they can be reconciled, without blocking deploy.
    bind = op.get_bind()
    orphans = bind.execute(
        sa.text(
            f"SELECT count(*) FROM {table} t "
            "LEFT JOIN user_categories c ON c.id = t.category_id "
            "WHERE c.id IS NULL"
        )
    ).scalar_one()
    if orphans:
        print(
            f"WARNING: {orphans} row(s) in {table} reference a category_id "
            "with no matching user_categories row. The new FK is added "
            "NOT VALID so this migration won't fail, but these rows should "
            "be reconciled and the constraint validated "
            f"(ALTER TABLE {table} VALIDATE CONSTRAINT ...)."
        )


def upgrade() -> None:
    _warn_on_orphaned_category_ids("expenses")
    _warn_on_orphaned_category_ids("recurring_expenses")

    op.create_foreign_key(
        "fk_expenses_category_id",
        "expenses",
        "user_categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
        postgresql_not_valid=True,
    )
    op.create_foreign_key(
        "fk_recurring_expenses_category_id",
        "recurring_expenses",
        "user_categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
        postgresql_not_valid=True,
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_recurring_expenses_category_id", "recurring_expenses", type_="foreignkey"
    )
    op.drop_constraint("fk_expenses_category_id", "expenses", type_="foreignkey")
