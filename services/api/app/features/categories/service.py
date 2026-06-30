import uuid

from sqlalchemy import func, select
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
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            color=color,
            expense_group=group,
        )
        for name, color, group in _DEFAULT_CATEGORIES
    ]
    db.add_all(categories)
    db.flush()
    return categories
