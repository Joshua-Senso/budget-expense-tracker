from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.categories.models import UserCategory


_DEFAULT_CATEGORIES: list[tuple[str, str, str]] = [
    ("Food & Dining", "#F59E0B", "card"),
    ("Transportation", "#3B82F6", "card"),
    ("Shopping", "#EC4899", "card"),
    ("Entertainment", "#8B5CF6", "card"),
    ("Health", "#10B981", "card"),
    ("Housing", "#6366F1", "other"),
    ("Utilities", "#64748B", "other"),
    ("Others", "#94A3B8", "other"),
]


def seed_default_categories(db: Session, user_id: str) -> list[UserCategory]:
    """Insert default personal categories for a new user.

    No-op (returns empty list) when the user already has at least one
    personal category — safe to call on every request.
    """
    existing_count = db.scalar(
        select(func.count()).where(
            UserCategory.user_id == user_id,
            UserCategory.household_id.is_(None),
        )
    )
    if existing_count:
        return []

    categories = [
        UserCategory(
            user_id=user_id,
            name=name,
            color=color,
            expense_group=group,
        )
        for name, color, group in _DEFAULT_CATEGORIES
    ]
    db.add_all(categories)
    try:
        db.commit()
    except IntegrityError as exc:
        # Only recover from a unique-violation (SQLSTATE 23505) caused by a
        # concurrent first request winning the race. Any other IntegrityError
        # (e.g. CHECK constraint failure) is a real bug and must propagate.
        if getattr(exc.orig, "sqlstate", None) != "23505":
            raise
        db.rollback()
        return list(
            db.execute(
                select(UserCategory).where(
                    UserCategory.user_id == user_id,
                    UserCategory.household_id.is_(None),
                )
            )
            .scalars()
            .all()
        )
    return categories
