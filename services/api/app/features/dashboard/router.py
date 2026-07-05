from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.households import HouseholdAccessError
from app.core.security import get_current_user_id
from app.features.dashboard import service
from app.features.dashboard.schemas import (
    DashboardSummaryResponse,
    YearlyOverviewResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_MONTH_KEY_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
_YEAR_PATTERN = r"^[1-9]\d{3}$"
_HOUSEHOLD_NOT_FOUND = HTTPException(status_code=404, detail="Household not found.")


@router.get("/summary/{month_key}", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    month_key: str = Path(pattern=_MONTH_KEY_PATTERN),
    household_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    try:
        return service.get_dashboard_summary(
            db, user_id, month_key, household_id=household_id
        )
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None


@router.get("/yearly/{year}", response_model=YearlyOverviewResponse)
def get_yearly_overview(
    year: str = Path(pattern=_YEAR_PATTERN),
    household_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> YearlyOverviewResponse:
    try:
        return service.get_yearly_overview(
            db, user_id, int(year), household_id=household_id
        )
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None
