from unittest.mock import MagicMock

import pytest

from app.core.households import (
    HouseholdAccessError,
    HouseholdRoleError,
    assert_household_member,
    assert_household_owner,
    get_household_role,
    is_household_member,
    is_household_owner,
)


def _mock_db(role: str | None) -> MagicMock:
    db = MagicMock()
    db.scalar.return_value = role
    return db


def test_is_household_member_true_when_row_found() -> None:
    db = _mock_db("member")

    assert is_household_member(db, "user-1", "household-1") is True


def test_is_household_member_false_when_no_row() -> None:
    db = _mock_db(None)

    assert is_household_member(db, "user-1", "household-1") is False


def test_assert_household_member_passes_silently_for_member() -> None:
    db = _mock_db("member")

    assert_household_member(db, "user-1", "household-1")  # does not raise


def test_assert_household_member_raises_for_non_member() -> None:
    db = _mock_db(None)

    with pytest.raises(HouseholdAccessError):
        assert_household_member(db, "user-1", "household-1")


def test_get_household_role_returns_role_when_member() -> None:
    db = _mock_db("owner")

    assert get_household_role(db, "user-1", "household-1") == "owner"


def test_get_household_role_returns_none_when_not_member() -> None:
    db = _mock_db(None)

    assert get_household_role(db, "user-1", "household-1") is None


def test_is_household_owner_true_for_owner_role() -> None:
    db = _mock_db("owner")

    assert is_household_owner(db, "user-1", "household-1") is True


def test_is_household_owner_false_for_member_role() -> None:
    db = _mock_db("member")

    assert is_household_owner(db, "user-1", "household-1") is False


def test_is_household_owner_false_when_not_a_member() -> None:
    db = _mock_db(None)

    assert is_household_owner(db, "user-1", "household-1") is False


def test_assert_household_owner_passes_silently_for_owner() -> None:
    db = _mock_db("owner")

    assert_household_owner(db, "user-1", "household-1")  # does not raise


def test_assert_household_owner_raises_for_non_owner_member() -> None:
    db = _mock_db("member")

    with pytest.raises(HouseholdRoleError):
        assert_household_owner(db, "user-1", "household-1")
