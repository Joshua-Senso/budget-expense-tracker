from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.households import HouseholdAccessError
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


def test_list_categories_returns_existing_without_seeding() -> None:
    db = _mock_db()
    existing = [_make_category(name="Food"), _make_category(name="Transport")]
    db.execute.return_value.scalars.return_value.all.return_value = existing

    with patch("app.features.categories.service.seed_default_categories") as mock_seed:
        result = list_categories(db, "user-1")

    mock_seed.assert_not_called()
    assert result == existing


def test_list_categories_seeds_when_empty() -> None:
    db = _mock_db()
    db.execute.return_value.scalars.return_value.all.return_value = []
    seeded = [_make_category(name="Food"), _make_category(name="Transport")]

    with patch(
        "app.features.categories.service.seed_default_categories", return_value=seeded
    ) as mock_seed:
        result = list_categories(db, "user-1")

    mock_seed.assert_called_once_with(db, "user-1")
    assert {c.name for c in result} == {"Food", "Transport"}


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
    db.get.return_value = cat

    result = update_category(db, "user-1", "cat-1", name="Groceries")

    assert cat.name == "Groceries"
    db.commit.assert_called_once()
    assert result is cat


def test_update_category_not_found_raises() -> None:
    db = _mock_db()
    db.get.return_value = None

    with pytest.raises(CategoryNotFoundError):
        update_category(db, "user-1", "missing-id", name="Groceries")


def test_update_category_duplicate_name_raises() -> None:
    db = _mock_db()
    cat = _make_category()
    db.get.return_value = cat
    db.commit.side_effect = _integrity_error("23505")

    with pytest.raises(DuplicateCategoryNameError):
        update_category(db, "user-1", "cat-1", name="Transport")

    db.rollback.assert_called_once()


def test_update_category_no_fields_is_noop() -> None:
    db = _mock_db()
    cat = _make_category(name="Food", color="#FF0000", expense_group="card")
    db.get.return_value = cat

    result = update_category(db, "user-1", "cat-1")

    db.commit.assert_called_once()
    assert result is cat
    assert cat.name == "Food"


# --- delete_category ---


def test_delete_category_happy_path() -> None:
    db = _mock_db()
    cat1 = _make_category(id="cat-1", name="Food")
    cat2 = _make_category(id="cat-2", name="Transport")
    db.get.return_value = cat1
    db.execute.return_value.scalars.return_value.all.return_value = [cat1, cat2]

    delete_category(db, "user-1", "cat-1")

    db.delete.assert_called_once_with(cat1)
    db.commit.assert_called_once()


def test_delete_category_not_found_raises() -> None:
    db = _mock_db()
    db.get.return_value = None

    with pytest.raises(CategoryNotFoundError):
        delete_category(db, "user-1", "missing-id")


def test_delete_last_category_raises() -> None:
    db = _mock_db()
    cat = _make_category(id="cat-1", name="Food")
    db.get.return_value = cat
    db.execute.return_value.scalars.return_value.all.return_value = [cat]

    with pytest.raises(LastCategoryError):
        delete_category(db, "user-1", "cat-1")

    db.delete.assert_not_called()


# --- household scoping ---


def test_list_categories_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        list_categories(db, "user-1", household_id="household-1")


def test_list_categories_household_scope_returns_shared_rows() -> None:
    db = _mock_db()
    db.scalar.return_value = "member-1"
    shared = [_make_category(household_id="household-1", user_id="user-2")]
    db.execute.return_value.scalars.return_value.all.return_value = shared

    result = list_categories(db, "user-1", household_id="household-1")

    assert result == shared


def test_create_category_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        create_category(
            db, "user-1", "Food", "#FF0000", "card", household_id="household-1"
        )

    db.add.assert_not_called()


def test_create_category_household_scope_happy_path() -> None:
    db = _mock_db()
    db.scalar.return_value = "member-1"

    result = create_category(
        db, "user-1", "Food", "#FF0000", "card", household_id="household-1"
    )

    assert result.household_id == "household-1"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_update_category_shared_row_accessible_to_household_member() -> None:
    db = _mock_db()
    cat = _make_category(household_id="household-1", user_id="user-2")
    db.get.return_value = cat
    db.scalar.return_value = "member-1"  # requester is a member of household-1

    result = update_category(db, "user-1", "cat-1", name="Groceries")

    assert result.name == "Groceries"
    db.commit.assert_called_once()


def test_update_category_shared_row_inaccessible_to_non_member() -> None:
    db = _mock_db()
    cat = _make_category(household_id="household-1", user_id="user-2")
    db.get.return_value = cat
    db.scalar.return_value = None  # requester is not a member

    with pytest.raises(CategoryNotFoundError):
        update_category(db, "user-1", "cat-1", name="Groceries")
