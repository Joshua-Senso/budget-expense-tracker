from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

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
        "from_currency": "USD",
        "to_currency": "PHP",
        "rate": Decimal("56.00"),
        "updated_by": "user-1",
    }
    rate = MagicMock(spec=ExchangeRate)
    for k, v in {**defaults, **kwargs}.items():
        setattr(rate, k, v)
    return rate


# --- upsert_exchange_rate ---


def test_upsert_exchange_rate_creates_when_no_existing_pair() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    result = upsert_exchange_rate(db, "user-1", "USD", "PHP", Decimal("56.00"))

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert result.from_currency == "USD"
    assert result.to_currency == "PHP"
    assert result.rate == Decimal("56.00")
    assert result.updated_by == "user-1"


def test_upsert_exchange_rate_updates_existing_pair_in_place() -> None:
    db = _mock_db()
    existing = _make_rate(rate=Decimal("55.00"))
    db.scalar.return_value = existing

    result = upsert_exchange_rate(db, "user-2", "USD", "PHP", Decimal("57.50"))

    db.add.assert_not_called()
    db.commit.assert_called_once()
    assert result is existing
    assert result.rate == Decimal("57.50")
    assert result.updated_by == "user-2"


def test_upsert_exchange_rate_recovers_from_concurrent_insert_race() -> None:
    """Two upserts for the same brand-new pair can both see no existing row
    and both try to insert; the loser's unique-constraint violation must
    convert into an update rather than a raw IntegrityError."""
    db = _mock_db()
    existing = _make_rate(rate=Decimal("55.00"))
    db.scalar.side_effect = [None, existing]  # miss, then found on retry
    db.commit.side_effect = [_integrity_error("23505"), None]

    result = upsert_exchange_rate(db, "user-1", "USD", "PHP", Decimal("57.50"))

    db.rollback.assert_called_once()
    assert result is existing
    assert result.rate == Decimal("57.50")


def test_upsert_exchange_rate_non_unique_integrity_error_reraises() -> None:
    db = _mock_db()
    db.scalar.return_value = None
    db.commit.side_effect = _integrity_error("23514")  # check_violation

    with pytest.raises(IntegrityError):
        upsert_exchange_rate(db, "user-1", "USD", "PHP", Decimal("57.50"))


# --- list_exchange_rates ---


def test_list_exchange_rates_returns_all() -> None:
    db = _mock_db()
    rates = [_make_rate(), _make_rate(id="fx-2", from_currency="EUR")]
    db.execute.return_value.scalars.return_value.all.return_value = rates

    result = list_exchange_rates(db)

    assert result == rates


# --- delete_exchange_rate ---


def test_delete_exchange_rate_happy_path() -> None:
    db = _mock_db()
    rate = _make_rate()
    db.get.return_value = rate

    delete_exchange_rate(db, "fx-1")

    db.delete.assert_called_once_with(rate)
    db.commit.assert_called_once()


def test_delete_exchange_rate_not_found_raises() -> None:
    db = _mock_db()
    db.get.return_value = None

    with pytest.raises(ExchangeRateNotFoundError):
        delete_exchange_rate(db, "missing-id")

    db.delete.assert_not_called()


# --- get_latest_rate ---


def test_get_latest_rate_returns_stored_rate() -> None:
    db = _mock_db()
    db.scalar.return_value = _make_rate(rate=Decimal("56.00"))

    result = get_latest_rate(db, "USD", "PHP")

    assert result == Decimal("56.00")


def test_get_latest_rate_returns_none_when_no_pair_stored() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    result = get_latest_rate(db, "USD", "PHP")

    assert result is None


# --- resolve_exchange_rate ---


def test_resolve_exchange_rate_returns_supplied_rate_without_lookup() -> None:
    db = _mock_db()

    result = resolve_exchange_rate(db, "USD", "PHP", Decimal("58.00"))

    assert result == Decimal("58.00")
    db.scalar.assert_not_called()


def test_resolve_exchange_rate_short_circuits_same_currency_without_lookup() -> None:
    db = _mock_db()

    result = resolve_exchange_rate(db, "PHP", "PHP", None)

    assert result is None
    db.scalar.assert_not_called()


def test_resolve_exchange_rate_falls_back_to_stored_rate_when_none_supplied() -> None:
    db = _mock_db()
    db.scalar.return_value = _make_rate(rate=Decimal("56.00"))

    result = resolve_exchange_rate(db, "USD", "PHP", None)

    assert result == Decimal("56.00")


def test_resolve_exchange_rate_returns_none_when_nothing_supplied_or_stored() -> None:
    db = _mock_db()
    db.scalar.return_value = None

    result = resolve_exchange_rate(db, "USD", "PHP", None)

    assert result is None
