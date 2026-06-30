"""add user_categories

Revision ID: 001
Revises:
Create Date: 2026-06-30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_categories",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("household_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
        sa.Column("expense_group", sa.String(), nullable=False),
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
        sa.CheckConstraint("name <> ''", name="ck_user_categories_name_nonempty"),
        sa.CheckConstraint(
            "color ~ '^#[0-9A-Fa-f]{6}$'", name="ck_user_categories_color_hex"
        ),
        sa.CheckConstraint(
            "expense_group IN ('card', 'other')",
            name="ck_user_categories_group_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_categories_user_id", "user_categories", ["user_id"])
    op.create_index(
        "ix_user_categories_user_name",
        "user_categories",
        ["user_id", "name"],
        unique=True,
        postgresql_where=sa.text("household_id IS NULL"),
    )
    op.create_index(
        "ix_user_categories_household_name",
        "user_categories",
        ["household_id", "name"],
        unique=True,
        postgresql_where=sa.text("household_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_user_categories_household_name", table_name="user_categories")
    op.drop_index("ix_user_categories_user_name", table_name="user_categories")
    op.drop_index("ix_user_categories_user_id", table_name="user_categories")
    op.drop_table("user_categories")
