from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import DataError

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


def _data_error() -> DataError:
    return DataError("stmt", {}, Exception('invalid input syntax for type uuid: "abc"'))


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


# --- malformed household_id / user_id ---
#
# organization_id/user_id are real Postgres `uuid` columns, so a malformed
# id (e.g. a caller-supplied `?household_id=abc`) fails the cast at the DB
# level with sqlalchemy.exc.DataError before any row could match. That must
# be treated the same as "not a member" -- a controlled 404, not a raw 500.


def test_get_household_role_treats_malformed_id_as_not_a_member() -> None:
    db = MagicMock()
    db.scalar.side_effect = _data_error()

    assert get_household_role(db, "user-1", "not-a-uuid") is None
    db.rollback.assert_called_once()


def test_is_household_member_false_for_malformed_id() -> None:
    db = MagicMock()
    db.scalar.side_effect = _data_error()

    assert is_household_member(db, "user-1", "not-a-uuid") is False


def test_assert_household_member_raises_access_error_for_malformed_id() -> None:
    db = MagicMock()
    db.scalar.side_effect = _data_error()

    with pytest.raises(HouseholdAccessError):
        assert_household_member(db, "user-1", "not-a-uuid")
