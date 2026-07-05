from sqlalchemy import String, select
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

    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        "organizationId", String, nullable=False
    )
    user_id: Mapped[str] = mapped_column("userId", String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)


def get_household_role(db: Session, user_id: str, household_id: str) -> str | None:
    return db.scalar(
        select(Member.role).where(
            Member.organization_id == household_id,
            Member.user_id == user_id,
        )
    )


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
