from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.exchange_rates.models import ExchangeRate


class ExchangeRateNotFoundError(Exception):
    pass


def _find_pair(
    db: Session, from_currency: str, to_currency: str
) -> ExchangeRate | None:
    return db.scalar(
        select(ExchangeRate).where(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
        )
    )


def list_exchange_rates(db: Session) -> list[ExchangeRate]:
    return list(
        db.execute(
            select(ExchangeRate).order_by(
                ExchangeRate.from_currency, ExchangeRate.to_currency
            )
        )
        .scalars()
        .all()
    )


def upsert_exchange_rate(
    db: Session, user_id: str, from_currency: str, to_currency: str, rate: Decimal
) -> ExchangeRate:
    existing = _find_pair(db, from_currency, to_currency)
    if existing is not None:
        existing.rate = rate
        existing.updated_by = user_id
        db.commit()
        return existing

    exchange_rate = ExchangeRate(
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
        # Lost a race with a concurrent first insert for this pair -- treat
        # as an update rather than failing the request. The row is
        # guaranteed to exist now (that's what the unique violation means),
        # but re-fetch explicitly rather than asserting it -- assertions are
        # stripped under `python -O` and this path must stay safe either way.
        existing = _find_pair(db, from_currency, to_currency)
        if existing is None:
            raise
        existing.rate = rate
        existing.updated_by = user_id
        db.commit()
        return existing
    return exchange_rate


def delete_exchange_rate(db: Session, exchange_rate_id: str) -> None:
    exchange_rate = db.get(ExchangeRate, exchange_rate_id)
    if exchange_rate is None:
        raise ExchangeRateNotFoundError(exchange_rate_id)
    db.delete(exchange_rate)
    db.commit()


def get_latest_rate(
    db: Session, from_currency: str, to_currency: str
) -> Decimal | None:
    existing = _find_pair(db, from_currency, to_currency)
    return existing.rate if existing is not None else None


def resolve_exchange_rate(
    db: Session,
    currency: str,
    base_currency: str,
    exchange_rate: Decimal | None,
) -> Decimal | None:
    """Fall back to a manually maintained rate (BUD-52) for this pair when
    the caller didn't supply one. Lets expense entry skip retyping a known
    rate, and lets the non-interactive paths (recurring generation, import)
    use a maintained rate before falling back further (raising, or recording
    the row unconverted). Every conversion call site is expected to route
    through this before calling `convert_to_base`/`convert_to_base_or_unconverted`
    -- a call site that skips it silently loses the fallback.
    """
    if exchange_rate is not None or currency == base_currency:
        return exchange_rate
    return get_latest_rate(db, currency, base_currency)
