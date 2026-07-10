import re
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.features.categories.service import _DEFAULT_CATEGORIES, seed_default_categories

_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_VALID_GROUPS = {"card", "other"}


def _mock_db(existing_count: int = 0) -> MagicMock:
    db = MagicMock()
    db.scalar.return_value = existing_count
    return db


def _integrity_error(sqlstate: str) -> IntegrityError:
    orig = MagicMock()
    orig.sqlstate = sqlstate
    return IntegrityError("stmt", {}, orig)


def test_seeds_defaults_for_new_user() -> None:
    db = _mock_db(existing_count=0)

    result = seed_default_categories(db, "user-1")

    assert len(result) == len(_DEFAULT_CATEGORIES)
    db.add_all.assert_called_once()
    db.commit.assert_called_once()


def test_no_op_when_categories_already_exist() -> None:
    db = _mock_db(existing_count=3)

    result = seed_default_categories(db, "user-1")

    assert result == []
    db.add_all.assert_not_called()
    db.commit.assert_not_called()


def test_concurrent_insert_recovers_via_rollback() -> None:
    db = _mock_db(existing_count=0)
    db.commit.side_effect = _integrity_error("23505")
    existing = [MagicMock(), MagicMock()]
    db.execute.return_value.scalars.return_value.all.return_value = existing

    result = seed_default_categories(db, "user-1")

    db.rollback.assert_called_once()
    assert result == existing


def test_non_unique_integrity_error_is_reraised() -> None:
    db = _mock_db(existing_count=0)
    db.commit.side_effect = _integrity_error("23514")  # check_violation

    with pytest.raises(IntegrityError):
        seed_default_categories(db, "user-1")


def test_seed_data_satisfies_constraints() -> None:
    for name, color, group in _DEFAULT_CATEGORIES:
        assert name != "", f"name must be non-empty: {name!r}"
        assert _HEX_COLOR_RE.match(color), f"color must be 6-char hex: {color!r}"
        assert group in _VALID_GROUPS, f"group must be 'card' or 'other': {group!r}"


def test_seed_rows_have_unique_names() -> None:
    names = [name for name, _, _ in _DEFAULT_CATEGORIES]
    assert len(names) == len(set(names)), "default category names must be unique"
