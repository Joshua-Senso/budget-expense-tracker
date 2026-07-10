"""DB-backed regression test for category deletion vs. concurrent writes.

Mirrors tests/test_households_db.py: mocked-Session unit tests can prove the
up-front `_category_in_use` check works, but they can't prove anything about
the actual race it can't close -- a writer inserting a new expense/recurring
row for the category between that check and the delete's commit. This
exercises the real `ON DELETE RESTRICT` foreign keys added in migration 009
against a live Postgres, which is what actually closes that race.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import delete

import app.features.categories.service as categories_service
from app.core.db import SessionLocal
from app.features.categories.models import UserCategory
from app.features.categories.service import CategoryInUseError
from app.features.expenses.models import Expense


def test_delete_category_blocked_when_expense_inserted_after_in_use_check(
    monkeypatch,
) -> None:
    """Simulate the race the app-level check-then-delete can't close: a
    concurrent writer inserts an expense referencing the category right
    after `_category_in_use` runs (and sees nothing) but before the delete
    commits. The FK's `ON DELETE RESTRICT` must still block the delete
    outright -- not silently let the category disappear out from under a
    row that references it.
    """
    db = SessionLocal()
    user_id = f"test-user-{uuid.uuid4()}"
    category_id = str(uuid.uuid4())
    other_category_id = str(uuid.uuid4())  # so the last-category guard passes
    expense_id = str(uuid.uuid4())
    try:
        db.add_all(
            [
                UserCategory(
                    id=category_id,
                    user_id=user_id,
                    name="Groceries",
                    color="#FF0000",
                    expense_group="card",
                ),
                UserCategory(
                    id=other_category_id,
                    user_id=user_id,
                    name="Rent",
                    color="#00FF00",
                    expense_group="other",
                ),
            ]
        )
        db.commit()

        real_in_use_check = categories_service._category_in_use

        def _in_use_check_racing_a_concurrent_insert(
            inner_db: object, checked_category_id: str
        ) -> bool:
            result = real_in_use_check(inner_db, checked_category_id)
            inner_db.add(
                Expense(
                    id=expense_id,
                    user_id=user_id,
                    category_id=category_id,
                    description="Concurrent insert",
                    amount=Decimal("10.00"),
                    currency="PHP",
                    base_amount=Decimal("10.00"),
                    exchange_rate=Decimal("1"),
                    spent_on=date(2026, 7, 1),
                )
            )
            inner_db.flush()
            return result

        monkeypatch.setattr(
            categories_service,
            "_category_in_use",
            _in_use_check_racing_a_concurrent_insert,
        )

        with pytest.raises(CategoryInUseError):
            categories_service.delete_category(db, user_id, category_id)

        # The delete must have been rejected, not silently applied.
        assert db.get(UserCategory, category_id) is not None
    finally:
        db.rollback()
        db.execute(delete(Expense).where(Expense.id == expense_id))
        db.execute(
            delete(UserCategory).where(
                UserCategory.id.in_([category_id, other_category_id])
            )
        )
        db.commit()
        db.close()
