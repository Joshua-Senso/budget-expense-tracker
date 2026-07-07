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
    # NOT VALID: before this migration any 3-letter uppercase code was
    # accepted, so existing rows may hold a currency outside this whitelist
    # (e.g. MXN, TWD). NOT VALID skips scanning existing rows, so the upgrade
    # can't fail on legacy data -- it still fully enforces the check on every
    # new insert/update from this point on. Once existing rows are audited
    # and cleaned up, run:
    #   ALTER TABLE expenses VALIDATE CONSTRAINT ck_expenses_currency_valid;
    op.execute(
        "ALTER TABLE expenses ADD CONSTRAINT ck_expenses_currency_valid "
        "CHECK (currency IN ('AED', 'AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', "
        "'HKD', 'IDR', 'INR', 'JPY', 'KRW', 'MYR', 'NZD', 'PHP', 'SAR', 'SGD', "
        "'THB', 'USD', 'VND')) NOT VALID"
    )


def downgrade() -> None:
    op.drop_constraint("ck_expenses_currency_valid", "expenses", type_="check")
