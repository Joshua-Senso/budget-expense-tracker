from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.features.expenses import service
from app.features.expenses.schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.features.expenses.service import CategoryOwnershipError, ExpenseNotFoundError

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    year: int | None = Query(default=None, ge=1, le=9999),
    month: int | None = Query(default=None, ge=1, le=12),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[ExpenseResponse]:
    return service.list_expenses(db, user_id, year=year, month=month)


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
        )
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
    except CategoryOwnershipError:
        raise HTTPException(status_code=404, detail="Category not found.")


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    try:
        service.delete_expense(db, user_id, expense_id)
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Expense not found.")
