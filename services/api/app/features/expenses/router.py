from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.core.security import get_current_user_id
from app.features.expenses import service
from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseInstallmentCreate,
    ExpenseResponse,
    ExpenseUpdate,
)
from app.features.expenses.service import CategoryOwnershipError, ExpenseNotFoundError

router = APIRouter(prefix="/expenses", tags=["expenses"])

_HOUSEHOLD_NOT_FOUND = HTTPException(status_code=404, detail="Household not found.")
_HOUSEHOLD_OWNER_REQUIRED = HTTPException(
    status_code=403, detail="Only the household owner can do this."
)


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    year: int | None = Query(default=None, ge=1, le=9999),
    month: int | None = Query(default=None, ge=1, le=12),
    household_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[ExpenseResponse]:
    try:
        return service.list_expenses(
            db, user_id, year=year, month=month, household_id=household_id
        )
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    try:
        return service.create_expense(
            db,
            user_id,
            body.category_id,
            body.description,
            body.amount,
            body.currency,
            body.spent_on,
            household_id=body.household_id,
        )
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None
    except CategoryOwnershipError:
        raise HTTPException(status_code=404, detail="Category not found.")


@router.post(
    "/installments",
    response_model=list[ExpenseResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_installment_expenses(
    body: ExpenseInstallmentCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[ExpenseResponse]:
    try:
        return service.create_installment_expenses(
            db,
            user_id,
            body.category_id,
            body.description,
            body.amount,
            body.currency,
            body.spent_on,
            body.installment_total,
            household_id=body.household_id,
        )
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None
    except CategoryOwnershipError:
        raise HTTPException(status_code=404, detail="Category not found.")


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: str,
    body: ExpenseUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    try:
        return service.update_expense(
            db,
            user_id,
            expense_id,
            category_id=body.category_id,
            description=body.description,
            amount=body.amount,
            currency=body.currency,
            spent_on=body.spent_on,
        )
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Expense not found.")
    except HouseholdRoleError:
        raise _HOUSEHOLD_OWNER_REQUIRED from None
    except CategoryOwnershipError:
        raise HTTPException(status_code=404, detail="Category not found.")


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: str,
    scope: Literal["row", "group"] = Query(default="row"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    try:
        service.delete_expense(db, user_id, expense_id, scope=scope)
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Expense not found.")
    except HouseholdRoleError:
        raise _HOUSEHOLD_OWNER_REQUIRED from None
