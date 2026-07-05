from typing import Any, Protocol, TypeVar

from sqlalchemy import String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base


class HouseholdAccessError(Exception):
    """Raised when a caller references a household they are not a member of."""


class HouseholdRoleError(Exception):
    """Raised when a member's role doesn't permit the requested action."""


OWNER_ROLE = "owner"


class Member(Base):
    """Read-only mapping onto Better Auth's `members` table.

    Better Auth owns this table's schema and migrations (household = its
    organization model); the API only ever reads it to authorize
    household-scoped requests. Deliberately not imported by
    `import_app_models()` -- Alembic must never manage or diff it.
    """

    __tablename__ = "members"

    # Better Auth's `advanced.database.generateId: "uuid"` (auth.ts) makes
    # these real Postgres `uuid` columns, not text -- comparing them to a
    # plain String-bound parameter fails at the SQL level ("operator does
    # not exist: uuid = character varying"). `as_uuid=False` keeps the
    # Python-side value a plain str, matching how the rest of the app
    # (Expense.user_id, UserCategory.household_id, ...) stores these ids.
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        "organizationId", UUID(as_uuid=False), nullable=False
    )
    user_id: Mapped[str] = mapped_column("userId", UUID(as_uuid=False), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)


def get_household_role(db: Session, user_id: str, household_id: str) -> str | None:
    try:
        return db.scalar(
            select(Member.role).where(
                Member.organization_id == household_id,
                Member.user_id == user_id,
            )
        )
    except DataError:
        # organization_id/user_id are real Postgres `uuid` columns, so a
        # malformed id (e.g. a caller-supplied `?household_id=abc`) fails
        # the cast at the DB level before any row could possibly match --
        # treat it the same as "not a member" rather than a 500, and roll
        # back so the aborted transaction doesn't break the rest of the
        # request. A malformed household_id and a well-formed-but-unknown
        # one are indistinguishable to the caller either way (both 404).
        db.rollback()
        return None


def is_household_member(db: Session, user_id: str, household_id: str) -> bool:
    return get_household_role(db, user_id, household_id) is not None


def assert_household_member(db: Session, user_id: str, household_id: str) -> None:
    if not is_household_member(db, user_id, household_id):
        raise HouseholdAccessError(household_id)


def is_household_owner(db: Session, user_id: str, household_id: str) -> bool:
    return get_household_role(db, user_id, household_id) == OWNER_ROLE


def assert_household_owner(db: Session, user_id: str, household_id: str) -> None:
    """Require the owner role for an action on an already-located shared row.

    Only the owner may edit or delete a shared row (PRD §10); members may
    read and add. Callers must already know the row belongs to `household_id`
    (e.g. via a prior membership check) -- this only narrows member -> owner.
    """
    if not is_household_owner(db, user_id, household_id):
        raise HouseholdRoleError(household_id)


class _HouseholdScopedRow(Protocol):
    user_id: str
    household_id: str | None


_RowT = TypeVar("_RowT", bound=_HouseholdScopedRow)


def locate_household_scoped_row(
    db: Session,
    model: type[_RowT],
    row_id: str,
    user_id: str,
    not_found: type[Exception],
    *,
    require_owner: bool = False,
) -> _RowT:
    """Locate a row that is either personal (`user_id`, `household_id IS
    NULL`) or shared within a household (any member may read/add; only the
    owner role may mutate -- PRD §10).

    Raises `not_found` uniformly whether the row doesn't exist or the caller
    isn't a member, so a non-member can't distinguish the two. When
    `require_owner` is set, fetches the household role once and reuses it for
    both the membership and ownership checks, instead of querying `members`
    twice for the same `(user_id, household_id)`.
    """
    row = db.get(model, row_id)
    if row is None:
        raise not_found(row_id)
    if row.household_id is None:
        if row.user_id != user_id:
            raise not_found(row_id)
        return row
    role = get_household_role(db, user_id, row.household_id)
    if role is None:
        raise not_found(row_id)
    if require_owner and role != OWNER_ROLE:
        raise HouseholdRoleError(row.household_id)
    return row


def household_scope_clauses(
    model: type[_HouseholdScopedRow], user_id: str, household_id: str | None
) -> list[Any]:
    """Build the WHERE clauses for `model` rows visible in the given scope:
    every row shared in `household_id`, or the caller's own personal rows.
    """
    if household_id is not None:
        return [model.household_id == household_id]
    return [model.user_id == user_id, model.household_id.is_(None)]
