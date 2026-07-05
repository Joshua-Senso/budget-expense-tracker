from unittest.mock import MagicMock

import pytest

from app.core.households import (
    HouseholdAccessError,
    assert_household_member,
    is_household_member,
)


def _mock_db(member_id: str | None) -> MagicMock:
    db = MagicMock()
    db.scalar.return_value = member_id
    return db


def test_is_household_member_true_when_row_found() -> None:
    db = _mock_db("member-1")

    assert is_household_member(db, "user-1", "household-1") is True


def test_is_household_member_false_when_no_row() -> None:
    db = _mock_db(None)

    assert is_household_member(db, "user-1", "household-1") is False


def test_assert_household_member_passes_silently_for_member() -> None:
    db = _mock_db("member-1")

    assert_household_member(db, "user-1", "household-1")  # does not raise


def test_assert_household_member_raises_for_non_member() -> None:
    db = _mock_db(None)

    with pytest.raises(HouseholdAccessError):
        assert_household_member(db, "user-1", "household-1")
