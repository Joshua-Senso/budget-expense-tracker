from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.features.exchange_rates import service
from app.features.exchange_rates.schemas import ExchangeRateResponse, ExchangeRateUpsert
from app.features.exchange_rates.service import ExchangeRateNotFoundError

router = APIRouter(prefix="/exchange-rates", tags=["exchange-rates"])


@router.get("", response_model=list[ExchangeRateResponse])
def list_exchange_rates(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[ExchangeRateResponse]:
    return service.list_exchange_rates(db)


@router.put("", response_model=ExchangeRateResponse)
def upsert_exchange_rate(
    body: ExchangeRateUpsert,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ExchangeRateResponse:
    return service.upsert_exchange_rate(
        db, user_id, body.from_currency, body.to_currency, body.rate
    )


@router.delete("/{exchange_rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exchange_rate(
    exchange_rate_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    try:
        service.delete_exchange_rate(db, exchange_rate_id)
    except ExchangeRateNotFoundError:
        raise HTTPException(status_code=404, detail="Exchange rate not found.")
