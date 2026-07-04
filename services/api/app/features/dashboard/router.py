from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.features.dashboard import service
from app.features.dashboard.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_MONTH_KEY_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get("/summary/{month_key}", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    month_key: str = Path(pattern=_MONTH_KEY_PATTERN),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    return service.get_dashboard_summary(db, user_id, month_key)
