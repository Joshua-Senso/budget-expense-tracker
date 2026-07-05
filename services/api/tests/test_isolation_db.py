"""Real-Postgres proof of cross-user and cross-household isolation (BUD-47).

Every other authorization test in this suite mocks `Session`, which proves
the right `.where()`/`.get()` call was made but can't catch a bug in the
actual SQL Postgres executes. This module runs the same service-layer
functions each router calls -- for expenses, categories, recurring,
attachments, and budget -- against a live database with two real household
members and a real outsider, to prove rows never leak across users or across
non-member households (PRD §15).

Mirrors `tests/test_households_db.py`'s convention: self-contained, creates
Better Auth's `users`/`organizations`/`members` shadow tables if this
Postgres was never migrated by the auth service.

Requires a live Postgres reachable via `DATABASE_URL` (`make up` locally, the
`postgres` service container in CI -- see `.github/workflows/ci.yml`).
"""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy import inspect, text

from app.core.db import SessionLocal, engine
from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.features.attachments.models import ExpenseAttachment
from app.features.attachments.service import (
    ExpenseNotFoundError as AttachmentExpenseNotFoundError,
)
from app.features.attachments.service import delete_attachment, list_attachments
from app.features.budget.service import (
    MonthlySettingNotFoundError,
    get_monthly_setting,
    upsert_monthly_setting,
)
from app.features.categories.service import (
    CategoryNotFoundError,
    create_category,
    delete_category,
    list_categories,
    update_category,
)
from app.features.expenses.service import (
    ExpenseNotFoundError,
    create_expense,
    delete_expense,
    list_expenses,
    update_expense,
)
from app.features.recurring.service import (
    RecurringExpenseNotFoundError,
    create_recurring_expense,
    deactivate_recurring_expense,
    list_recurring_expenses,
)

_CREATE_USERS = """
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    email text NOT NULL UNIQUE,
    "emailVerified" boolean NOT NULL DEFAULT false,
    "createdAt" timestamptz NOT NULL DEFAULT now(),
    "updatedAt" timestamptz NOT NULL DEFAULT now()
)
"""

_CREATE_ORGANIZATIONS = """
CREATE TABLE organizations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    slug text NOT NULL UNIQUE,
    "createdAt" timestamptz NOT NULL DEFAULT now()
)
"""

_CREATE_MEMBERS = """
CREATE TABLE members (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    "organizationId" uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    "userId" uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role text NOT NULL,
    "createdAt" timestamptz NOT NULL DEFAULT now()
)
"""


def _ensure_better_auth_tables() -> bool:
    if inspect(engine).has_table("members"):
        return False
    with engine.begin() as conn:
        conn.execute(text(_CREATE_USERS))
        conn.execute(text(_CREATE_ORGANIZATIONS))
        conn.execute(text(_CREATE_MEMBERS))
    return True


def _drop_better_auth_tables() -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE members"))
        conn.execute(text("DROP TABLE organizations"))
        conn.execute(text("DROP TABLE users"))


@pytest.fixture
def tenants():
    """Two real household members (owner, member) plus an outsider who
    belongs to neither -- the three-way split every isolation test needs."""
    created_tables = _ensure_better_auth_tables()
    db = SessionLocal()
    owner_id = str(uuid.uuid4())
    member_id = str(uuid.uuid4())
    outsider_id = str(uuid.uuid4())
    household_id = str(uuid.uuid4())
    try:
        for user_id in (owner_id, member_id, outsider_id):
            db.execute(
                text(
                    'INSERT INTO users (id, name, email, "emailVerified", "createdAt", "updatedAt") '
                    "VALUES (:id, 'Test User', :email, true, now(), now())"
                ),
                {"id": user_id, "email": f"{user_id}@example.com"},
            )
        db.execute(
            text(
                'INSERT INTO organizations (id, name, slug, "createdAt") '
                "VALUES (:id, 'Test Household', :slug, now())"
            ),
            {"id": household_id, "slug": household_id},
        )
        for user_id, role in ((owner_id, "owner"), (member_id, "member")):
            db.execute(
                text(
                    'INSERT INTO members (id, "organizationId", "userId", role, "createdAt") '
                    "VALUES (:id, :org_id, :user_id, :role, now())"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "org_id": household_id,
                    "user_id": user_id,
                    "role": role,
                },
            )
        db.commit()
        yield db, owner_id, member_id, outsider_id, household_id
    finally:
        db.rollback()
        # Deletion order respects FK RESTRICT from expenses/recurring_expenses
        # onto user_categories -- rows referencing a category must go first.
        # expense_attachments cascades from expenses, so no explicit delete
        # is needed there.
        db.execute(
            text("DELETE FROM expenses WHERE user_id IN (:owner, :member, :outsider)"),
            {"owner": owner_id, "member": member_id, "outsider": outsider_id},
        )
        db.execute(
            text(
                "DELETE FROM recurring_expenses "
                "WHERE user_id IN (:owner, :member, :outsider)"
            ),
            {"owner": owner_id, "member": member_id, "outsider": outsider_id},
        )
        db.execute(
            text(
                "DELETE FROM user_categories "
                "WHERE user_id IN (:owner, :member, :outsider)"
            ),
            {"owner": owner_id, "member": member_id, "outsider": outsider_id},
        )
        db.execute(
            text(
                "DELETE FROM user_monthly_settings "
                "WHERE user_id IN (:owner, :member, :outsider)"
            ),
            {"owner": owner_id, "member": member_id, "outsider": outsider_id},
        )
        db.commit()
        db.execute(
            text('DELETE FROM members WHERE "organizationId" = :id'),
            {"id": household_id},
        )
        db.execute(
            text("DELETE FROM organizations WHERE id = :id"), {"id": household_id}
        )
        db.execute(
            text("DELETE FROM users WHERE id IN (:owner, :member, :outsider)"),
            {"owner": owner_id, "member": member_id, "outsider": outsider_id},
        )
        db.commit()
        db.close()
        if created_tables:
            _drop_better_auth_tables()


# --- categories ---


def test_personal_category_isolated_from_other_user(tenants) -> None:
    db, owner_id, member_id, _outsider_id, _household_id = tenants
    category = create_category(db, owner_id, "Groceries", "#F59E0B", "card")

    assert category.id not in [c.id for c in list_categories(db, member_id)]
    with pytest.raises(CategoryNotFoundError):
        update_category(db, member_id, category.id, name="Hacked")
    with pytest.raises(CategoryNotFoundError):
        delete_category(db, member_id, category.id)


def test_shared_category_household_role_gating(tenants) -> None:
    db, owner_id, member_id, outsider_id, household_id = tenants
    shared = create_category(
        db, owner_id, "Rent", "#3B82F6", "other", household_id=household_id
    )
    # A second shared category so the owner's delete below isn't blocked by
    # the last-category guard -- unrelated to the isolation being proven here.
    create_category(
        db, owner_id, "Utilities", "#64748B", "other", household_id=household_id
    )

    with pytest.raises(HouseholdAccessError):
        list_categories(db, outsider_id, household_id=household_id)
    with pytest.raises(HouseholdAccessError):
        create_category(
            db, outsider_id, "Sneaky", "#000000", "other", household_id=household_id
        )

    member_categories = list_categories(db, member_id, household_id=household_id)
    assert shared.id in [c.id for c in member_categories]

    with pytest.raises(HouseholdRoleError):
        update_category(db, member_id, shared.id, name="Renamed by member")
    with pytest.raises(HouseholdRoleError):
        delete_category(db, member_id, shared.id)

    updated = update_category(db, owner_id, shared.id, name="Rent (updated)")
    assert updated.name == "Rent (updated)"
    delete_category(db, owner_id, shared.id)  # does not raise


# --- expenses ---


def test_personal_expense_isolated_from_other_user(tenants) -> None:
    db, owner_id, member_id, _outsider_id, _household_id = tenants
    category = create_category(db, owner_id, "Food", "#F59E0B", "card")
    expense = create_expense(
        db, owner_id, category.id, "Lunch", Decimal("150.00"), "PHP", date(2026, 7, 1)
    )

    assert expense.id not in [e.id for e in list_expenses(db, member_id)]
    with pytest.raises(ExpenseNotFoundError):
        update_expense(db, member_id, expense.id, description="Hacked")
    with pytest.raises(ExpenseNotFoundError):
        delete_expense(db, member_id, expense.id)


def test_shared_expense_household_role_gating(tenants) -> None:
    db, owner_id, member_id, outsider_id, household_id = tenants
    category = create_category(
        db, owner_id, "Rent", "#3B82F6", "other", household_id=household_id
    )
    expense = create_expense(
        db,
        owner_id,
        category.id,
        "Monthly rent",
        Decimal("15000.00"),
        "PHP",
        date(2026, 7, 1),
        household_id=household_id,
    )

    with pytest.raises(HouseholdAccessError):
        list_expenses(db, outsider_id, household_id=household_id)

    member_expenses = list_expenses(db, member_id, household_id=household_id)
    assert expense.id in [e.id for e in member_expenses]

    with pytest.raises(HouseholdRoleError):
        update_expense(db, member_id, expense.id, description="Edited by member")
    with pytest.raises(HouseholdRoleError):
        delete_expense(db, member_id, expense.id)

    updated = update_expense(db, owner_id, expense.id, description="Rent (paid)")
    assert updated.description == "Rent (paid)"
    delete_expense(db, owner_id, expense.id)  # does not raise


# --- recurring ---


def test_personal_recurring_isolated_from_other_user(tenants) -> None:
    db, owner_id, member_id, _outsider_id, _household_id = tenants
    category = create_category(db, owner_id, "Subscriptions", "#8B5CF6", "card")
    rule = create_recurring_expense(
        db, owner_id, category.id, "Netflix", Decimal("500.00"), "PHP", date(2026, 1, 1)
    )

    assert rule.id not in [r.id for r in list_recurring_expenses(db, member_id)]
    with pytest.raises(RecurringExpenseNotFoundError):
        deactivate_recurring_expense(db, member_id, rule.id, 2026, 7)


def test_shared_recurring_household_role_gating(tenants) -> None:
    db, owner_id, member_id, outsider_id, household_id = tenants
    category = create_category(
        db, owner_id, "Utilities", "#64748B", "other", household_id=household_id
    )
    rule = create_recurring_expense(
        db,
        owner_id,
        category.id,
        "Electricity",
        Decimal("2000.00"),
        "PHP",
        date(2026, 1, 1),
        household_id=household_id,
    )

    with pytest.raises(HouseholdAccessError):
        list_recurring_expenses(db, outsider_id, household_id=household_id)

    member_rules = list_recurring_expenses(db, member_id, household_id=household_id)
    assert rule.id in [r.id for r in member_rules]

    with pytest.raises(HouseholdRoleError):
        deactivate_recurring_expense(db, member_id, rule.id, 2026, 7)

    deactivated = deactivate_recurring_expense(db, owner_id, rule.id, 2026, 7)
    assert deactivated.is_active is False


# --- attachments ---


def test_shared_attachment_household_role_gating(tenants, monkeypatch) -> None:
    # Isolation is enforced before any S3 call, but delete_attachment still
    # tries a best-effort object delete on success -- stub the client so this
    # test doesn't depend on a reachable MinIO.
    monkeypatch.setattr(
        "app.features.attachments.service.get_s3_client", lambda: MagicMock()
    )
    db, owner_id, member_id, outsider_id, household_id = tenants
    category = create_category(
        db, owner_id, "Receipts", "#10B981", "other", household_id=household_id
    )
    expense = create_expense(
        db,
        owner_id,
        category.id,
        "Groceries",
        Decimal("1200.00"),
        "PHP",
        date(2026, 7, 1),
        household_id=household_id,
    )
    attachment = ExpenseAttachment(
        expense_id=expense.id,
        user_id=owner_id,
        household_id=household_id,
        object_key=f"{owner_id}/{expense.id}/{uuid.uuid4()}.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
    )
    db.add(attachment)
    db.commit()

    with pytest.raises(AttachmentExpenseNotFoundError):
        list_attachments(db, outsider_id, expense.id)

    member_attachments = list_attachments(db, member_id, expense.id)
    assert attachment.id in [a.id for a in member_attachments]

    with pytest.raises(HouseholdRoleError):
        delete_attachment(db, member_id, expense.id, attachment.id)

    delete_attachment(db, owner_id, expense.id, attachment.id)  # does not raise


# --- budget (personal-only; no household support) ---


def test_monthly_setting_isolated_from_other_user(tenants) -> None:
    db, owner_id, member_id, _outsider_id, _household_id = tenants
    upsert_monthly_setting(db, owner_id, "2026-07", Decimal("50000.00"), "PHP")

    with pytest.raises(MonthlySettingNotFoundError):
        get_monthly_setting(db, member_id, "2026-07")

    # Same month_key, different user -- must not update the owner's row.
    upsert_monthly_setting(db, member_id, "2026-07", Decimal("30000.00"), "PHP")
    owner_setting = get_monthly_setting(db, owner_id, "2026-07")
    assert owner_setting.monthly_net_salary == Decimal("50000.00")
