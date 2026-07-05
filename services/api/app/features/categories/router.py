from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.households import HouseholdAccessError, HouseholdRoleError
from app.core.security import get_current_user_id
from app.features.categories import service
from app.features.categories.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.features.categories.service import (
    CategoryInUseError,
    CategoryNotFoundError,
    DuplicateCategoryNameError,
    LastCategoryError,
)

router = APIRouter(prefix="/categories", tags=["categories"])

_HOUSEHOLD_NOT_FOUND = HTTPException(status_code=404, detail="Household not found.")
_HOUSEHOLD_OWNER_REQUIRED = HTTPException(
    status_code=403, detail="Only the household owner can do this."
)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    household_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[CategoryResponse]:
    try:
        return service.list_categories(db, user_id, household_id=household_id)
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    try:
        return service.create_category(
            db,
            user_id,
            body.name,
            body.color,
            body.expense_group,
            household_id=body.household_id,
        )
    except HouseholdAccessError:
        raise _HOUSEHOLD_NOT_FOUND from None
    except DuplicateCategoryNameError:
        raise HTTPException(
            status_code=409, detail="A category with that name already exists."
        )


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    body: CategoryUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    try:
        return service.update_category(
            db,
            user_id,
            category_id,
            name=body.name,
            color=body.color,
            expense_group=body.expense_group,
        )
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="Category not found.")
    except HouseholdRoleError:
        raise _HOUSEHOLD_OWNER_REQUIRED from None
    except DuplicateCategoryNameError:
        raise HTTPException(
            status_code=409, detail="A category with that name already exists."
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    try:
        service.delete_category(db, user_id, category_id)
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="Category not found.")
    except HouseholdRoleError:
        raise _HOUSEHOLD_OWNER_REQUIRED from None
    except LastCategoryError:
        raise HTTPException(
            status_code=409, detail="Cannot delete the last remaining category."
        )
    except CategoryInUseError:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a category that still has expenses or "
            "recurring rules referencing it.",
        )
