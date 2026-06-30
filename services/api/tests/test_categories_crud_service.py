from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.features.categories.models import UserCategory
from app.features.categories.service import (
    CategoryNotFoundError,
    DuplicateCategoryNameError,
    LastCategoryError,
    create_category,
    delete_category,
    list_categories,
    update_category,
)


def _mock_db() -> MagicMock:
    return MagicMock()


def _integrity_error(sqlstate: str) -> IntegrityError:
    orig = MagicMock()
    orig.sqlstate = sqlstate
    return IntegrityError("stmt", {}, orig)


def _make_category(**kwargs) -> UserCategory:
    defaults = {
        "id": "cat-1",
        "user_id": "user-1",
        "household_id": None,
        "name": "Food",
        "color": "#FF0000",
        "expense_group": "card",
    }
    cat = MagicMock(spec=UserCategory)
    for k, v in {**defaults, **kwargs}.items():
        setattr(cat, k, v)
    return cat


# --- list_categories ---


def test_list_categories_seeds_and_returns_all() -> None:
    db = _mock_db()
    existing = [_make_category(name="Food"), _make_category(name="Transport")]
    db.execute.return_value.scalars.return_value.all.return_value = existing

    with patch("app.features.categories.service.seed_default_categories") as mock_seed:
        result = list_categories(db, "user-1")

    mock_seed.assert_called_once_with(db, "user-1")
    assert result == existing


# --- create_category ---


def test_create_category_happy_path() -> None:
    db = _mock_db()

    result = create_category(db, "user-1", "Food", "#FF0000", "card")

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert result.name == "Food"
    assert result.color == "#FF0000"
    assert result.expense_group == "card"
    assert result.user_id == "user-1"


def test_create_category_duplicate_name_raises() -> None:
    db = _mock_db()
    db.commit.side_effect = _integrity_error("23505")

    with pytest.raises(DuplicateCategoryNameError):
        create_category(db, "user-1", "Food", "#FF0000", "card")

    db.rollback.assert_called_once()


def test_create_category_non_unique_integrity_error_reraises() -> None:
    db = _mock_db()
    db.commit.side_effect = _integrity_error("23514")  # check_violation

    with pytest.raises(IntegrityError):
        create_category(db, "user-1", "Food", "#FF0000", "card")


# --- update_category ---


def test_update_category_happy_path() -> None:
    db = _mock_db()
    cat = _make_category(name="Food", color="#FF0000", expense_group="card")
    db.execute.return_value.scalar_one_or_none.return_value = cat

    result = update_category(db, "user-1", "cat-1", name="Groceries")

    assert cat.name == "Groceries"
    db.commit.assert_called_once()
    assert result is cat


def test_update_category_not_found_raises() -> None:
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(CategoryNotFoundError):
        update_category(db, "user-1", "missing-id", name="Groceries")


def test_update_category_duplicate_name_raises() -> None:
    db = _mock_db()
    cat = _make_category()
    db.execute.return_value.scalar_one_or_none.return_value = cat
    db.commit.side_effect = _integrity_error("23505")

    with pytest.raises(DuplicateCategoryNameError):
        update_category(db, "user-1", "cat-1", name="Transport")

    db.rollback.assert_called_once()


def test_update_category_no_fields_is_noop() -> None:
    db = _mock_db()
    cat = _make_category(name="Food", color="#FF0000", expense_group="card")
    db.execute.return_value.scalar_one_or_none.return_value = cat

    result = update_category(db, "user-1", "cat-1")

    db.commit.assert_called_once()
    assert result is cat
    assert cat.name == "Food"


# --- delete_category ---


def test_delete_category_happy_path() -> None:
    db = _mock_db()
    cat = _make_category()
    db.execute.return_value.scalar_one_or_none.return_value = cat
    db.scalar.return_value = 3

    delete_category(db, "user-1", "cat-1")

    db.delete.assert_called_once_with(cat)
    db.commit.assert_called_once()


def test_delete_category_not_found_raises() -> None:
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(CategoryNotFoundError):
        delete_category(db, "user-1", "missing-id")


def test_delete_last_category_raises() -> None:
    db = _mock_db()
    cat = _make_category()
    db.execute.return_value.scalar_one_or_none.return_value = cat
    db.scalar.return_value = 1

    with pytest.raises(LastCategoryError):
        delete_category(db, "user-1", "cat-1")

    db.delete.assert_not_called()
