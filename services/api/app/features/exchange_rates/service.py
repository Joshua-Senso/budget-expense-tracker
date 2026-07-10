from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.households import (
    OWNER_ROLE,
    HouseholdAccessError,
    HouseholdRoleError,
    assert_household_scope,
    get_household_role,
    household_scope_clauses,
    locate_household_scoped_row,
)
from app.features.exchange_rates.models import ExchangeRate


class ExchangeRateNotFoundError(Exception):
    pass


def _find_pair(
    db: Session,
    user_id: str,
    household_id: str | None,
    from_currency: str,
    to_currency: str,
) -> ExchangeRate | None:
    return db.scalar(
        select(ExchangeRate).where(
            *household_scope_clauses(ExchangeRate, user_id, household_id),
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
        )
    )


def list_exchange_rates(
    db: Session, user_id: str, household_id: str | None = None
) -> list[ExchangeRate]:
    assert_household_scope(db, user_id, household_id)
    return list(
        db.execute(
            select(ExchangeRate)
            .where(*household_scope_clauses(ExchangeRate, user_id, household_id))
            .order_by(ExchangeRate.from_currency, ExchangeRate.to_currency)
        )
        .scalars()
        .all()
    )


def _require_owner_for_update(household_id: str | None, role: str | None) -> None:
    """Members may add a *new* rate to a shared scope, same as categories --
    but overwriting one that's already there is an edit, not an add, so it
    follows the same owner-only rule as editing a shared category/expense
    (PRD §10). Personal scope has no roles to check."""
    if household_id is not None and role != OWNER_ROLE:
        raise HouseholdRoleError(household_id)


def upsert_exchange_rate(
    db: Session,
    user_id: str,
    household_id: str | None,
    from_currency: str,
    to_currency: str,
    rate: Decimal,
) -> ExchangeRate:
    # Fetched once and reused for both the membership and (if the pair
    # already exists) ownership checks below, instead of querying `members`
    # twice for the same (user_id, household_id) -- same reasoning as
    # locate_household_scoped_row.
    role = get_household_role(db, user_id, household_id) if household_id else None
    if household_id is not None and role is None:
        raise HouseholdAccessError(household_id)

    existing = _find_pair(db, user_id, household_id, from_currency, to_currency)
    if existing is not None:
        _require_owner_for_update(household_id, role)
        existing.rate = rate
        existing.updated_by = user_id
        db.commit()
        return existing

    exchange_rate = ExchangeRate(
        user_id=user_id,
        household_id=household_id,
        from_currency=from_currency,
        to_currency=to_currency,
        rate=rate,
        updated_by=user_id,
    )
    db.add(exchange_rate)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) != "23505":
            raise
        # Lost a race with a concurrent first insert for this pair (within
        # the same scope) -- the row now exists (that's what the unique
        # violation means), so this becomes an update and needs the same
        # owner check as the existing-row branch above. Re-fetch explicitly
        # rather than asserting it exists -- assertions are stripped under
        # `python -O` and this path must stay safe either way.
        existing = _find_pair(db, user_id, household_id, from_currency, to_currency)
        if existing is None:
            raise
        _require_owner_for_update(household_id, role)
        existing.rate = rate
        existing.updated_by = user_id
        db.commit()
        return existing
    return exchange_rate


def delete_exchange_rate(db: Session, user_id: str, exchange_rate_id: str) -> None:
    """Only the household owner may delete a shared rate (PRD §10); members
    may read and add. A personal rate may only be deleted by its owner."""
    exchange_rate = locate_household_scoped_row(
        db,
        ExchangeRate,
        exchange_rate_id,
        user_id,
        ExchangeRateNotFoundError,
        require_owner=True,
    )
    db.delete(exchange_rate)
    db.commit()


def get_latest_rate(
    db: Session,
    user_id: str,
    household_id: str | None,
    from_currency: str,
    to_currency: str,
) -> Decimal | None:
    existing = _find_pair(db, user_id, household_id, from_currency, to_currency)
    return existing.rate if existing is not None else None


def resolve_exchange_rate(
    db: Session,
    user_id: str,
    household_id: str | None,
    currency: str,
    base_currency: str,
    exchange_rate: Decimal | None,
) -> Decimal | None:
    """Fall back to a manually maintained rate (BUD-52) for this pair, in the
    caller's own scope, when the caller didn't supply one. Lets expense entry
    skip retyping a known rate, and lets the non-interactive paths (recurring
    generation, import) use a maintained rate before falling back further
    (raising, or recording the row unconverted). Every conversion call site
    is expected to route through this before calling
    `convert_to_base`/`convert_to_base_or_unconverted` -- a call site that
    skips it silently loses the fallback.
    """
    if exchange_rate is not None or currency == base_currency:
        return exchange_rate
    return get_latest_rate(db, user_id, household_id, currency, base_currency)
