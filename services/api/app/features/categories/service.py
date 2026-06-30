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


class CategoryNotFoundError(Exception):
    pass


class DuplicateCategoryNameError(Exception):
    pass


class LastCategoryError(Exception):
    pass


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


def _personal_categories_query(user_id: str):
    return select(UserCategory).where(
        UserCategory.user_id == user_id,
        UserCategory.household_id.is_(None),
    )


def list_categories(db: Session, user_id: str) -> list[UserCategory]:
    seed_default_categories(db, user_id)
    return list(
        db.execute(_personal_categories_query(user_id).order_by(UserCategory.name))
        .scalars()
        .all()
    )


def create_category(
    db: Session,
    user_id: str,
    name: str,
    color: str,
    expense_group: str,
) -> UserCategory:
    category = UserCategory(
        user_id=user_id, name=name, color=color, expense_group=expense_group
    )
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise DuplicateCategoryNameError(name) from exc
        raise
    return category


def update_category(
    db: Session,
    user_id: str,
    category_id: str,
    name: str | None = None,
    color: str | None = None,
    expense_group: str | None = None,
) -> UserCategory:
    category = db.execute(
        _personal_categories_query(user_id).where(UserCategory.id == category_id)
    ).scalar_one_or_none()
    if category is None:
        raise CategoryNotFoundError(category_id)

    for attr, value in [
        ("name", name),
        ("color", color),
        ("expense_group", expense_group),
    ]:
        if value is not None:
            setattr(category, attr, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise DuplicateCategoryNameError(name) from exc
        raise
    return category


def delete_category(db: Session, user_id: str, category_id: str) -> None:
    category = db.execute(
        _personal_categories_query(user_id).where(UserCategory.id == category_id)
    ).scalar_one_or_none()
    if category is None:
        raise CategoryNotFoundError(category_id)

    count = db.scalar(
        select(func.count()).where(
            UserCategory.user_id == user_id,
            UserCategory.household_id.is_(None),
        )
    )
    if count <= 1:
        raise LastCategoryError()

    db.delete(category)
    db.commit()
