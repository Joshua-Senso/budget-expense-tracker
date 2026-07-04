from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.features.budget import service
from app.features.budget.schemas import MonthlySettingResponse, MonthlySettingUpsert
from app.features.budget.service import MonthlySettingNotFoundError

router = APIRouter(prefix="/budget", tags=["budget"])

_MONTH_KEY_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get("/settings/{month_key}", response_model=MonthlySettingResponse)
def get_monthly_setting(
    month_key: str = Path(pattern=_MONTH_KEY_PATTERN),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> MonthlySettingResponse:
    try:
        return service.get_monthly_setting(db, user_id, month_key)
    except MonthlySettingNotFoundError:
        raise HTTPException(status_code=404, detail="No salary set for this month.")


@router.put("/settings/{month_key}", response_model=MonthlySettingResponse)
def upsert_monthly_setting(
    body: MonthlySettingUpsert,
    month_key: str = Path(pattern=_MONTH_KEY_PATTERN),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> MonthlySettingResponse:
    return service.upsert_monthly_setting(
        db, user_id, month_key, body.monthly_net_salary, body.base_currency
    )
