from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.households import HouseholdAccessError
from app.core.security import get_current_user_id
from app.features.recurring import service
from app.features.recurring.schemas import (
    ProjectedExpense,
    RecurringExpenseCreate,
    RecurringExpenseResponse,
)
from app.features.recurring.service import (
    CategoryOwnershipError,
    RecurringExpenseNotFoundError,
)

router = APIRouter(prefix="/recurring", tags=["recurring"])

_MONTH_KEY_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
_HOUSEHOLD_NOT_FOUND = HTTPException(status_code=404, detail="Household not found.")


def _parse_month_key(month_key: str) -> tuple[int, int]:
    year_str, month_str = month_key.split("-")
    return int(year_str), int(month_str)


@router.get("", response_model=list[RecurringExpenseResponse])
def list_recurring_expenses(
    household_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[RecurringExpenseResponse]:
    try:
        return service.list_recurring_expenses(db, user_id, household_id=household_id)
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None


@router.post(
    "", response_model=RecurringExpenseResponse, status_code=status.HTTP_201_CREATED
)
def create_recurring_expense(
    body: RecurringExpenseCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> RecurringExpenseResponse:
    try:
        return service.create_recurring_expense(
            db,
            user_id,
            body.category_id,
            body.description,
            body.amount,
            body.currency,
            body.start_on,
            body.end_on,
            household_id=body.household_id,
        )
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None
    except CategoryOwnershipError:
        raise HTTPException(status_code=404, detail="Category not found.")


@router.get("/projection/{month_key}", response_model=list[ProjectedExpense])
def get_monthly_projection(
    month_key: str = Path(pattern=_MONTH_KEY_PATTERN),
    household_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[ProjectedExpense]:
    year, month = _parse_month_key(month_key)
    try:
        return service.project_month(
            db, user_id, year, month, household_id=household_id
        )
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None


@router.delete("/{recurring_id}/{month_key}", status_code=status.HTTP_204_NO_CONTENT)
def stop_recurring_expense(
    recurring_id: str,
    month_key: str = Path(pattern=_MONTH_KEY_PATTERN),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    year, month = _parse_month_key(month_key)
    try:
        service.deactivate_recurring_expense(db, user_id, recurring_id, year, month)
    except RecurringExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Recurring expense not found.")
