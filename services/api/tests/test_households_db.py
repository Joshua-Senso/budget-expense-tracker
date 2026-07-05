"""DB-backed regression test for app/core/households.py.

Every other test in this suite mocks `Session`, which can't catch a bug in
the actual SQL sent to Postgres. This module exists specifically to close
that gap: it runs `is_household_member`/`get_household_role`/
`assert_household_member` against a real database, using Better Auth's actual
column types (Postgres `uuid`, not text) for `members.id`,
`members.organizationId`, and `members.userId`.

Requires a live Postgres reachable via `DATABASE_URL` (provided by
`make up` locally and the `postgres` service container in CI -- see
`.github/workflows/ci.yml`).
"""

import uuid

import pytest
from sqlalchemy import inspect, text

from app.core.db import SessionLocal, engine
from app.core.households import (
    HouseholdAccessError,
    assert_household_member,
    get_household_role,
    is_household_member,
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
    """Create minimal users/organizations/members tables if this Postgres
    was never migrated by the auth service (e.g. CI's fresh database, which
    only runs Alembic for app tables per api AGENTS.md). Column types match
    the real Better Auth migration (services/auth/better-auth_migrations/).

    Returns True if this function created the tables (caller must drop them).
    """
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


def test_household_membership_lookup_against_real_postgres_uuid_columns() -> None:
    """Regression guard: members.id/organizationId/userId are real Postgres
    `uuid` columns (auth.ts: advanced.database.generateId: "uuid"), not
    text. Mapping them as SQLAlchemy `String` compiles a query that Postgres
    rejects outright: "operator does not exist: uuid = character varying".
    Every household-scoped endpoint in the app depends on this lookup, so a
    regression here breaks all household reads/writes silently in unit
    tests (which mock Session.scalar) and loudly in production.
    """
    created_tables = _ensure_better_auth_tables()
    db = SessionLocal()
    owner_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())
    household_id = str(uuid.uuid4())
    try:
        # createdAt is explicit (not left to a column default) because the
        # *real* Better Auth migration leaves organizations.createdAt and
        # members.createdAt NOT NULL with no default -- only users.createdAt
        # defaults to CURRENT_TIMESTAMP there.
        db.execute(
            text(
                'INSERT INTO users (id, name, email, "emailVerified", "createdAt", "updatedAt") '
                "VALUES (:id, 'Test Owner', :email, true, now(), now())"
            ),
            {"id": owner_id, "email": f"{owner_id}@example.com"},
        )
        db.execute(
            text(
                'INSERT INTO organizations (id, name, slug, "createdAt") '
                "VALUES (:id, 'Test Household', :slug, now())"
            ),
            {"id": household_id, "slug": household_id},
        )
        db.execute(
            text(
                'INSERT INTO members (id, "organizationId", "userId", role, "createdAt") '
                "VALUES (:id, :org_id, :user_id, 'owner', now())"
            ),
            {"id": str(uuid.uuid4()), "org_id": household_id, "user_id": owner_id},
        )
        db.commit()

        assert is_household_member(db, owner_id, household_id) is True
        assert get_household_role(db, owner_id, household_id) == "owner"
        assert_household_member(db, owner_id, household_id)  # does not raise

        assert is_household_member(db, other_user_id, household_id) is False
        assert get_household_role(db, other_user_id, household_id) is None
    finally:
        db.rollback()
        db.execute(
            text('DELETE FROM members WHERE "organizationId" = :id'),
            {"id": household_id},
        )
        db.execute(
            text("DELETE FROM organizations WHERE id = :id"), {"id": household_id}
        )
        db.execute(text("DELETE FROM users WHERE id = :id"), {"id": owner_id})
        db.commit()
        db.close()
        if created_tables:
            _drop_better_auth_tables()


def test_malformed_household_id_is_not_a_member_against_real_postgres() -> None:
    """Regression guard: organization_id/user_id are real Postgres `uuid`
    columns, so a caller-supplied non-UUID string (e.g. `?household_id=abc`)
    fails the cast at the DB level (sqlalchemy.exc.DataError) rather than
    simply matching zero rows. This must be treated as "not a member" (a
    controlled 404 at the router), and the session must recover so the rest
    of the request can still run.
    """
    created_tables = _ensure_better_auth_tables()
    db = SessionLocal()
    try:
        assert is_household_member(db, "not-a-uuid", "also-not-a-uuid") is False
        assert get_household_role(db, "not-a-uuid", "also-not-a-uuid") is None
        with pytest.raises(HouseholdAccessError):
            assert_household_member(db, "not-a-uuid", "also-not-a-uuid")

        # The session must still be usable after recovering from the
        # DataError -- a raw Postgres error leaves the transaction aborted
        # until rolled back, which would break the rest of the request.
        assert db.execute(text("SELECT 1")).scalar() == 1
    finally:
        db.rollback()
        db.close()
        if created_tables:
            _drop_better_auth_tables()
