from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.features.exchange_rates.models import ExchangeRate
from app.features.exchange_rates.service import (
    ExchangeRateNotFoundError,
    delete_exchange_rate,
    get_latest_rate,
    list_exchange_rates,
    resolve_exchange_rate,
    upsert_exchange_rate,
)


def _mock_db() -> MagicMock:
    return MagicMock()


def _integrity_error(sqlstate: str) -> IntegrityError:
    orig = MagicMock()
    orig.sqlstate = sqlstate
    return IntegrityError("stmt", {}, orig)


def _make_rate(**kwargs) -> ExchangeRate:
    defaults = {
        "id": "fx-1",
        "user_id": "user-1",
        "household_id": None,
        "from_currency": "USD",
        "to_currency": "PHP",
        "rate": Decimal("56.00"),
        "updated_by": "user-1",
    }
    rate = MagicMock(spec=ExchangeRate)
    for k, v in {**defaults, **kwargs}.items():
        setattr(rate, k, v)
    return rate


# --- upsert_exchange_rate (personal scope) ---


def test_upsert_exchange_rate_creates_when_no_existing_pair() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    result = upsert_exchange_rate(db, "user-1", None, "USD", "PHP", Decimal("56.00"))

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert result.user_id == "user-1"
    assert result.household_id is None
    assert result.from_currency == "USD"
    assert result.to_currency == "PHP"
    assert result.rate == Decimal("56.00")
    assert result.updated_by == "user-1"


def test_upsert_exchange_rate_updates_existing_pair_in_place() -> None:
    db = _mock_db()
    existing = _make_rate(rate=Decimal("55.00"))
    db.scalar.return_value = existing

    result = upsert_exchange_rate(db, "user-1", None, "USD", "PHP", Decimal("57.50"))

    db.add.assert_not_called()
    db.commit.assert_called_once()
    assert result is existing
    assert result.rate == Decimal("57.50")
    assert result.updated_by == "user-1"


def test_upsert_exchange_rate_recovers_from_concurrent_insert_race() -> None:
    """Two upserts for the same brand-new pair (in the same scope) can both
    see no existing row and both try to insert; the loser's unique-constraint
    violation must convert into an update rather than a raw IntegrityError."""
    db = _mock_db()
    existing = _make_rate(rate=Decimal("55.00"))
    db.scalar.side_effect = [None, existing]  # miss, then found on retry
    db.commit.side_effect = [_integrity_error("23505"), None]

    result = upsert_exchange_rate(db, "user-1", None, "USD", "PHP", Decimal("57.50"))

    db.rollback.assert_called_once()
    assert result is existing
    assert result.rate == Decimal("57.50")


def test_upsert_exchange_rate_non_unique_integrity_error_reraises() -> None:
    db = _mock_db()
    db.scalar.return_value = None
    db.commit.side_effect = _integrity_error("23514")  # check_violation

    with pytest.raises(IntegrityError):
        upsert_exchange_rate(db, "user-1", None, "USD", "PHP", Decimal("57.50"))


# --- list_exchange_rates ---


def test_list_exchange_rates_returns_personal_rates() -> None:
    db = _mock_db()
    rates = [_make_rate(), _make_rate(id="fx-2", from_currency="EUR")]
    db.execute.return_value.scalars.return_value.all.return_value = rates

    result = list_exchange_rates(db, "user-1")

    assert result == rates


# --- delete_exchange_rate ---


def test_delete_exchange_rate_happy_path() -> None:
    db = _mock_db()
    rate = _make_rate()
    db.get.return_value = rate

    delete_exchange_rate(db, "user-1", "fx-1")

    db.delete.assert_called_once_with(rate)
    db.commit.assert_called_once()


def test_delete_exchange_rate_not_found_raises() -> None:
    db = _mock_db()
    db.get.return_value = None

    with pytest.raises(ExchangeRateNotFoundError):
        delete_exchange_rate(db, "user-1", "missing-id")

    db.delete.assert_not_called()


def test_delete_exchange_rate_personal_row_owned_by_someone_else_raises_not_found() -> (
    None
):
    db = _mock_db()
    rate = _make_rate(user_id="user-2")
    db.get.return_value = rate

    with pytest.raises(ExchangeRateNotFoundError):
        delete_exchange_rate(db, "user-1", "fx-1")

    db.delete.assert_not_called()


# --- get_latest_rate ---


def test_get_latest_rate_returns_stored_rate() -> None:
    db = _mock_db()
    db.scalar.return_value = _make_rate(rate=Decimal("56.00"))

    result = get_latest_rate(db, "user-1", None, "USD", "PHP")

    assert result == Decimal("56.00")


def test_get_latest_rate_returns_none_when_no_pair_stored() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    result = get_latest_rate(db, "user-1", None, "USD", "PHP")

    assert result is None


# --- resolve_exchange_rate ---


def test_resolve_exchange_rate_returns_supplied_rate_without_lookup() -> None:
    db = _mock_db()

    result = resolve_exchange_rate(db, "user-1", None, "USD", "PHP", Decimal("58.00"))

    assert result == Decimal("58.00")
    db.scalar.assert_not_called()


def test_resolve_exchange_rate_short_circuits_same_currency_without_lookup() -> None:
    db = _mock_db()

    result = resolve_exchange_rate(db, "user-1", None, "PHP", "PHP", None)

    assert result is None
    db.scalar.assert_not_called()


def test_resolve_exchange_rate_falls_back_to_stored_rate_when_none_supplied() -> None:
    db = _mock_db()
    db.scalar.return_value = _make_rate(rate=Decimal("56.00"))

    result = resolve_exchange_rate(db, "user-1", None, "USD", "PHP", None)

    assert result == Decimal("56.00")


def test_resolve_exchange_rate_returns_none_when_nothing_supplied_or_stored() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    result = resolve_exchange_rate(db, "user-1", None, "USD", "PHP", None)

    assert result is None


# --- household scoping ---


def test_list_exchange_rates_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        list_exchange_rates(db, "user-1", household_id="household-1")


def test_list_exchange_rates_household_scope_returns_shared_rows() -> None:
    db = _mock_db()
    db.scalar.return_value = "member-1"
    shared = [_make_rate(household_id="household-1", user_id="user-2")]
    db.execute.return_value.scalars.return_value.all.return_value = shared

    result = list_exchange_rates(db, "user-1", household_id="household-1")

    assert result == shared


def test_upsert_exchange_rate_household_scope_requires_membership() -> None:
    db = _mock_db()
    db.scalar.return_value = None  # not a member

    with pytest.raises(HouseholdAccessError):
        upsert_exchange_rate(
            db, "user-1", "household-1", "USD", "PHP", Decimal("56.00")
        )

    db.add.assert_not_called()


def test_upsert_exchange_rate_household_scope_happy_path() -> None:
    db = _mock_db()
    # membership check, then the pair lookup sees no existing row
    db.scalar.side_effect = ["member-1", None]

    result = upsert_exchange_rate(
        db, "user-1", "household-1", "USD", "PHP", Decimal("56.00")
    )

    assert result.household_id == "household-1"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_upsert_exchange_rate_household_scope_forbidden_for_non_owner_member_updating_existing() -> (
    None
):
    """Members may add a *new* rate to a shared scope, but overwriting one
    that's already there is an edit -- only the household owner may do that
    (PRD §10), mirroring categories/expenses."""
    db = _mock_db()
    existing = _make_rate(household_id="household-1", user_id="user-2")
    db.scalar.side_effect = ["member", existing]  # membership check, then found pair

    with pytest.raises(HouseholdRoleError):
        upsert_exchange_rate(
            db, "user-1", "household-1", "USD", "PHP", Decimal("57.50")
        )

    db.commit.assert_not_called()


def test_upsert_exchange_rate_household_scope_allowed_for_owner_updating_existing() -> (
    None
):
    db = _mock_db()
    existing = _make_rate(
        household_id="household-1", user_id="user-2", rate=Decimal("55.00")
    )
    db.scalar.side_effect = ["owner", existing]  # requester owns household-1

    result = upsert_exchange_rate(
        db, "user-1", "household-1", "USD", "PHP", Decimal("57.50")
    )

    assert result is existing
    assert result.rate == Decimal("57.50")
    db.commit.assert_called_once()


def test_upsert_exchange_rate_race_recovery_still_enforces_owner_check() -> None:
    """A non-owner member losing the concurrent-insert race must not be able
    to sneak an update past the owner check via the race-recovery path."""
    db = _mock_db()
    existing = _make_rate(household_id="household-1", user_id="user-2")
    # membership check, no existing pair before the insert, found on retry
    db.scalar.side_effect = ["member", None, existing]
    db.commit.side_effect = [_integrity_error("23505")]

    with pytest.raises(HouseholdRoleError):
        upsert_exchange_rate(
            db, "user-1", "household-1", "USD", "PHP", Decimal("57.50")
        )

    db.rollback.assert_called_once()


def test_delete_exchange_rate_shared_row_forbidden_for_non_owner_member() -> None:
    """Only the household owner may delete a shared rate (PRD §10); members
    may read and add."""
    db = _mock_db()
    rate = _make_rate(household_id="household-1", user_id="user-2")
    db.get.return_value = rate
    db.scalar.return_value = "member"  # requester is a member, not the owner

    with pytest.raises(HouseholdRoleError):
        delete_exchange_rate(db, "user-1", "fx-1")

    db.delete.assert_not_called()


def test_delete_exchange_rate_shared_row_allowed_for_owner() -> None:
    db = _mock_db()
    rate = _make_rate(household_id="household-1", user_id="user-2")
    db.get.return_value = rate
    db.scalar.return_value = "owner"  # requester owns household-1

    delete_exchange_rate(db, "user-1", "fx-1")

    db.delete.assert_called_once_with(rate)
    db.commit.assert_called_once()
