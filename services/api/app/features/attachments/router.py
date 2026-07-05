from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.households import HouseholdRoleError
from app.core.security import get_current_user_id
from app.features.attachments import service
from app.features.attachments.schemas import (
    AttachmentConfirm,
    AttachmentDownloadURLResponse,
    AttachmentResponse,
    AttachmentUploadRequest,
    AttachmentUploadURLResponse,
)
from app.features.attachments.service import (
    AttachmentNotFoundError,
    AttachmentTooLargeError,
    ExpenseNotFoundError,
    InvalidContentTypeError,
    ObjectNotUploadedError,
)

router = APIRouter(prefix="/expenses/{expense_id}/attachments", tags=["attachments"])

_EXPENSE_NOT_FOUND = HTTPException(status_code=404, detail="Expense not found.")
_ATTACHMENT_NOT_FOUND = HTTPException(status_code=404, detail="Attachment not found.")
_HOUSEHOLD_OWNER_REQUIRED = HTTPException(
    status_code=403, detail="Only the household owner can do this."
)


@router.post(
    "/upload-url",
    response_model=AttachmentUploadURLResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_upload_url(
    expense_id: str,
    body: AttachmentUploadRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> AttachmentUploadURLResponse:
    try:
        upload_url, object_key = service.create_upload_url(
            db, user_id, expense_id, body.content_type, body.size_bytes
        )
    except ExpenseNotFoundError:
        raise _EXPENSE_NOT_FOUND from None
    except InvalidContentTypeError:
        raise HTTPException(
            status_code=422, detail="Unsupported receipt content type."
        ) from None
    except AttachmentTooLargeError:
        raise HTTPException(
            status_code=422, detail="Attachment exceeds the maximum allowed size."
        ) from None
    return AttachmentUploadURLResponse(
        upload_url=upload_url,
        object_key=object_key,
        expires_in=service.UPLOAD_URL_EXPIRES_IN,
    )


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
def confirm_attachment(
    expense_id: str,
    body: AttachmentConfirm,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> AttachmentResponse:
    try:
        return service.confirm_attachment(db, user_id, expense_id, body.object_key)
    except ExpenseNotFoundError:
        raise _EXPENSE_NOT_FOUND from None
    except InvalidContentTypeError:
        raise HTTPException(
            status_code=422, detail="Unsupported receipt content type."
        ) from None
    except AttachmentTooLargeError:
        raise HTTPException(
            status_code=422, detail="Attachment exceeds the maximum allowed size."
        ) from None
    except ObjectNotUploadedError:
        raise HTTPException(
            status_code=400,
            detail="Upload not found in object storage; it may have failed or is incomplete.",
        ) from None


@router.get("", response_model=list[AttachmentResponse])
def list_attachments(
    expense_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[AttachmentResponse]:
    try:
        return service.list_attachments(db, user_id, expense_id)
    except ExpenseNotFoundError:
        raise _EXPENSE_NOT_FOUND from None


@router.get(
    "/{attachment_id}/download-url", response_model=AttachmentDownloadURLResponse
)
def create_download_url(
    expense_id: str,
    attachment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> AttachmentDownloadURLResponse:
    try:
        download_url = service.create_download_url(
            db, user_id, expense_id, attachment_id
        )
    except ExpenseNotFoundError:
        raise _EXPENSE_NOT_FOUND from None
    except AttachmentNotFoundError:
        raise _ATTACHMENT_NOT_FOUND from None
    return AttachmentDownloadURLResponse(
        download_url=download_url, expires_in=service.DOWNLOAD_URL_EXPIRES_IN
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    expense_id: str,
    attachment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    try:
        service.delete_attachment(db, user_id, expense_id, attachment_id)
    except ExpenseNotFoundError:
        raise _EXPENSE_NOT_FOUND from None
    except AttachmentNotFoundError:
        raise _ATTACHMENT_NOT_FOUND from None
    except HouseholdRoleError:
        raise _HOUSEHOLD_OWNER_REQUIRED from None
