from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError

from app.features.categories.service import _DEFAULT_CATEGORIES, seed_default_categories


def _mock_db(existing_count: int = 0) -> MagicMock:
    db = MagicMock()
    db.scalar.return_value = existing_count
    return db


def test_seeds_defaults_for_new_user() -> None:
    db = _mock_db(existing_count=0)

    result = seed_default_categories(db, "user-1")

    assert len(result) == len(_DEFAULT_CATEGORIES)
    db.add_all.assert_called_once()
    db.flush.assert_called_once()


def test_no_op_when_categories_already_exist() -> None:
    db = _mock_db(existing_count=3)

    result = seed_default_categories(db, "user-1")

    assert result == []
    db.add_all.assert_not_called()
    db.flush.assert_not_called()


def test_concurrent_insert_recovers_via_rollback() -> None:
    db = _mock_db(existing_count=0)
    db.flush.side_effect = IntegrityError("unique violation", {}, None)
    existing = [MagicMock(), MagicMock()]
    db.execute.return_value.scalars.return_value.all.return_value = existing

    result = seed_default_categories(db, "user-1")

    db.rollback.assert_called_once()
    assert result == existing
