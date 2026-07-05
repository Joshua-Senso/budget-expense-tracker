import uuid

from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.storage import get_s3_client
from app.features.attachments.models import ExpenseAttachment
from app.features.expenses.models import Expense

# Receipts are photos of paper receipts, not arbitrary documents -- restrict to
# common image types and map each to a fixed extension so the object key never
# has to carry a user-supplied filename (PRD §9.6: bucket stays private, keys
# are server-generated).
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}
MAX_SIZE_BYTES = 10 * 1024 * 1024
UPLOAD_URL_EXPIRES_IN = 300
DOWNLOAD_URL_EXPIRES_IN = 300


class ExpenseNotFoundError(Exception):
    pass


class AttachmentNotFoundError(Exception):
    pass


class InvalidContentTypeError(Exception):
    pass


class AttachmentTooLargeError(Exception):
    pass


class ObjectNotUploadedError(Exception):
    pass


def _get_owned_expense(db: Session, user_id: str, expense_id: str) -> Expense:
    expense = db.execute(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.user_id == user_id,
            Expense.household_id.is_(None),
        )
    ).scalar_one_or_none()
    if expense is None:
        raise ExpenseNotFoundError(expense_id)
    return expense


def _get_owned_attachment(
    db: Session, user_id: str, expense_id: str, attachment_id: str
) -> ExpenseAttachment:
    _get_owned_expense(db, user_id, expense_id)
    attachment = db.execute(
        select(ExpenseAttachment).where(
            ExpenseAttachment.id == attachment_id,
            ExpenseAttachment.expense_id == expense_id,
            ExpenseAttachment.user_id == user_id,
        )
    ).scalar_one_or_none()
    if attachment is None:
        raise AttachmentNotFoundError(attachment_id)
    return attachment


def _validate_content_type(content_type: str) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise InvalidContentTypeError(content_type)


def _validate_size(size_bytes: int) -> None:
    if size_bytes > MAX_SIZE_BYTES:
        raise AttachmentTooLargeError(size_bytes)


def create_upload_url(
    db: Session,
    user_id: str,
    expense_id: str,
    content_type: str,
    size_bytes: int,
) -> tuple[str, str]:
    """Mint a short-lived presigned PUT URL; the client uploads bytes directly
    to object storage, so receipt bytes never pass through this API."""
    _get_owned_expense(db, user_id, expense_id)
    _validate_content_type(content_type)
    _validate_size(size_bytes)

    extension = ALLOWED_CONTENT_TYPES[content_type]
    object_key = f"{user_id}/{expense_id}/{uuid.uuid4()}{extension}"
    settings = get_settings()
    upload_url = get_s3_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.receipts_bucket,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=UPLOAD_URL_EXPIRES_IN,
    )
    return upload_url, object_key


def confirm_attachment(
    db: Session, user_id: str, expense_id: str, object_key: str
) -> ExpenseAttachment:
    expense = _get_owned_expense(db, user_id, expense_id)

    expected_prefix = f"{user_id}/{expense_id}/"
    if not object_key.startswith(expected_prefix):
        raise ObjectNotUploadedError(object_key)

    settings = get_settings()
    try:
        # head_object is the source of truth for content_type/size_bytes -- a
        # client-supplied value here could misreport them to dodge the size cap
        # or the content-type allow-list.
        head = get_s3_client().head_object(
            Bucket=settings.receipts_bucket, Key=object_key
        )
    except ClientError as exc:
        raise ObjectNotUploadedError(object_key) from exc

    content_type = head["ContentType"]
    size_bytes = head["ContentLength"]
    _validate_content_type(content_type)
    _validate_size(size_bytes)

    attachment = ExpenseAttachment(
        expense_id=expense.id,
        user_id=user_id,
        object_key=object_key,
        content_type=content_type,
        size_bytes=size_bytes,
    )
    db.add(attachment)
    try:
        db.commit()
    except IntegrityError:
        # A retried confirm (e.g. the first request committed but the client
        # timed out waiting for the response) re-confirms the same object_key.
        # Treat it as idempotent rather than surfacing a 500.
        db.rollback()
        existing = db.execute(
            select(ExpenseAttachment).where(ExpenseAttachment.object_key == object_key)
        ).scalar_one_or_none()
        if existing is None:
            raise
        return existing
    return attachment


def list_attachments(
    db: Session, user_id: str, expense_id: str
) -> list[ExpenseAttachment]:
    _get_owned_expense(db, user_id, expense_id)
    return list(
        db.execute(
            select(ExpenseAttachment)
            .where(
                ExpenseAttachment.expense_id == expense_id,
                ExpenseAttachment.user_id == user_id,
            )
            .order_by(ExpenseAttachment.uploaded_at)
        )
        .scalars()
        .all()
    )


def create_download_url(
    db: Session, user_id: str, expense_id: str, attachment_id: str
) -> str:
    attachment = _get_owned_attachment(db, user_id, expense_id, attachment_id)
    settings = get_settings()
    return get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.receipts_bucket, "Key": attachment.object_key},
        ExpiresIn=DOWNLOAD_URL_EXPIRES_IN,
    )


def delete_attachment(
    db: Session, user_id: str, expense_id: str, attachment_id: str
) -> None:
    attachment = _get_owned_attachment(db, user_id, expense_id, attachment_id)
    object_key = attachment.object_key
    db.delete(attachment)
    db.commit()

    # DB row is the source of truth for what's listable/downloadable, so it's
    # deleted first: if this S3 call fails, the object is merely orphaned
    # (a storage-cost cleanup concern) rather than a row pointing at nothing.
    settings = get_settings()
    try:
        get_s3_client().delete_object(Bucket=settings.receipts_bucket, Key=object_key)
    except ClientError:
        pass
