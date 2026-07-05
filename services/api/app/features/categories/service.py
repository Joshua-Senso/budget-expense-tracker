from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.households import (
    assert_household_member,
    assert_household_owner,
    is_household_member,
)
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


def _commit_or_raise_duplicate(db: Session, name: str | None) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise DuplicateCategoryNameError(name) from exc
        raise


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


def _scoped_categories_query(user_id: str, household_id: str | None):
    if household_id is not None:
        return select(UserCategory).where(UserCategory.household_id == household_id)
    return select(UserCategory).where(
        UserCategory.user_id == user_id,
        UserCategory.household_id.is_(None),
    )


def _locate_category(db: Session, user_id: str, category_id: str) -> UserCategory:
    category = db.get(UserCategory, category_id)
    if category is None:
        raise CategoryNotFoundError(category_id)
    if category.household_id is None:
        if category.user_id != user_id:
            raise CategoryNotFoundError(category_id)
    elif not is_household_member(db, user_id, category.household_id):
        raise CategoryNotFoundError(category_id)
    return category


def _locate_category_for_mutation(
    db: Session, user_id: str, category_id: str
) -> UserCategory:
    """Locate a category for edit/delete: only the household owner may edit
    or delete a shared category (PRD §10); members may read and add."""
    category = _locate_category(db, user_id, category_id)
    if category.household_id is not None:
        assert_household_owner(db, user_id, category.household_id)
    return category


def list_categories(
    db: Session, user_id: str, household_id: str | None = None
) -> list[UserCategory]:
    if household_id is not None:
        assert_household_member(db, user_id, household_id)
        return list(
            db.execute(
                _scoped_categories_query(user_id, household_id).order_by(
                    UserCategory.name
                )
            )
            .scalars()
            .all()
        )

    categories = list(
        db.execute(_scoped_categories_query(user_id, None).order_by(UserCategory.name))
        .scalars()
        .all()
    )
    if not categories:
        categories = seed_default_categories(db, user_id)
        categories.sort(key=lambda c: c.name)
    return categories


def create_category(
    db: Session,
    user_id: str,
    name: str,
    color: str,
    expense_group: str,
    household_id: str | None = None,
) -> UserCategory:
    if household_id is not None:
        assert_household_member(db, user_id, household_id)
    category = UserCategory(
        user_id=user_id,
        name=name,
        color=color,
        expense_group=expense_group,
        household_id=household_id,
    )
    db.add(category)
    _commit_or_raise_duplicate(db, name)
    return category


def update_category(
    db: Session,
    user_id: str,
    category_id: str,
    name: str | None = None,
    color: str | None = None,
    expense_group: str | None = None,
) -> UserCategory:
    category = _locate_category_for_mutation(db, user_id, category_id)

    for attr, value in [
        ("name", name),
        ("color", color),
        ("expense_group", expense_group),
    ]:
        if value is not None:
            setattr(category, attr, value)

    _commit_or_raise_duplicate(db, name)
    return category


def delete_category(db: Session, user_id: str, category_id: str) -> None:
    category = _locate_category_for_mutation(db, user_id, category_id)

    # Lock every category in the same scope so concurrent deletes serialize
    # and cannot both pass the last-category guard.
    all_categories = list(
        db.execute(
            _scoped_categories_query(user_id, category.household_id).with_for_update()
        )
        .scalars()
        .all()
    )
    if len(all_categories) <= 1:
        raise LastCategoryError()

    db.delete(category)
    db.commit()
