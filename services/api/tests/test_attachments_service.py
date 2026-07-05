from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from app.features.attachments.models import ExpenseAttachment
from app.features.attachments.service import (
    MAX_SIZE_BYTES,
    AttachmentNotFoundError,
    AttachmentTooLargeError,
    ExpenseNotFoundError,
    InvalidContentTypeError,
    ObjectNotUploadedError,
    confirm_attachment,
    create_download_url,
    create_upload_url,
    delete_attachment,
    list_attachments,
)
from app.features.expenses.models import Expense


def _mock_db() -> MagicMock:
    return MagicMock()


def _make_expense(**kwargs) -> Expense:
    defaults = {
        "id": "exp-1",
        "user_id": "user-1",
        "household_id": None,
    }
    expense = MagicMock(spec=Expense)
    for k, v in {**defaults, **kwargs}.items():
        setattr(expense, k, v)
    return expense


def _make_attachment(**kwargs) -> ExpenseAttachment:
    defaults = {
        "id": "att-1",
        "expense_id": "exp-1",
        "user_id": "user-1",
        "object_key": "user-1/exp-1/att.jpg",
        "content_type": "image/jpeg",
        "size_bytes": 1024,
        "uploaded_at": datetime(2026, 7, 5, tzinfo=UTC),
    }
    attachment = MagicMock(spec=ExpenseAttachment)
    for k, v in {**defaults, **kwargs}.items():
        setattr(attachment, k, v)
    return attachment


def _result(scalar_one_or_none=None, all_=None) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if all_ is not None:
        result.scalars.return_value.all.return_value = all_
    return result


def _mock_s3(monkeypatch) -> MagicMock:
    client = MagicMock()
    monkeypatch.setattr(
        "app.features.attachments.service.get_s3_client", lambda: client
    )
    return client


# --- create_upload_url ---


def test_create_upload_url_returns_url_and_key_scoped_to_user_and_expense(
    monkeypatch,
) -> None:
    db = _mock_db()
    db.execute.return_value = _result(_make_expense())
    client = _mock_s3(monkeypatch)
    client.generate_presigned_url.return_value = "https://signed.example/put"

    url, object_key = create_upload_url(db, "user-1", "exp-1", "image/jpeg", 1024)

    assert url == "https://signed.example/put"
    assert object_key.startswith("user-1/exp-1/")
    assert object_key.endswith(".jpg")
    client.generate_presigned_url.assert_called_once()
    assert client.generate_presigned_url.call_args.args[0] == "put_object"


def test_create_upload_url_raises_when_expense_not_owned(monkeypatch) -> None:
    db = _mock_db()
    db.execute.return_value = _result(None)
    _mock_s3(monkeypatch)

    with pytest.raises(ExpenseNotFoundError):
        create_upload_url(db, "user-1", "exp-1", "image/jpeg", 1024)


def test_create_upload_url_rejects_unsupported_content_type(monkeypatch) -> None:
    db = _mock_db()
    db.execute.return_value = _result(_make_expense())
    _mock_s3(monkeypatch)

    with pytest.raises(InvalidContentTypeError):
        create_upload_url(db, "user-1", "exp-1", "application/pdf", 1024)


def test_create_upload_url_rejects_oversized_file(monkeypatch) -> None:
    db = _mock_db()
    db.execute.return_value = _result(_make_expense())
    _mock_s3(monkeypatch)

    with pytest.raises(AttachmentTooLargeError):
        create_upload_url(db, "user-1", "exp-1", "image/jpeg", MAX_SIZE_BYTES + 1)


# --- confirm_attachment ---


def test_confirm_attachment_creates_row_when_object_exists(monkeypatch) -> None:
    db = _mock_db()
    db.execute.return_value = _result(_make_expense())
    client = _mock_s3(monkeypatch)

    attachment = confirm_attachment(
        db, "user-1", "exp-1", "user-1/exp-1/abc.jpg", "image/jpeg", 1024
    )

    client.head_object.assert_called_once()
    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert attachment.object_key == "user-1/exp-1/abc.jpg"


def test_confirm_attachment_raises_when_object_key_not_owned(monkeypatch) -> None:
    db = _mock_db()
    db.execute.return_value = _result(_make_expense())
    _mock_s3(monkeypatch)

    with pytest.raises(ObjectNotUploadedError):
        confirm_attachment(
            db, "user-1", "exp-1", "other-user/exp-1/abc.jpg", "image/jpeg", 1024
        )


def test_confirm_attachment_raises_when_object_missing_from_bucket(monkeypatch) -> None:
    db = _mock_db()
    db.execute.return_value = _result(_make_expense())
    client = _mock_s3(monkeypatch)
    client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
    )

    with pytest.raises(ObjectNotUploadedError):
        confirm_attachment(
            db, "user-1", "exp-1", "user-1/exp-1/abc.jpg", "image/jpeg", 1024
        )


def test_confirm_attachment_raises_when_expense_not_owned(monkeypatch) -> None:
    db = _mock_db()
    db.execute.return_value = _result(None)
    _mock_s3(monkeypatch)

    with pytest.raises(ExpenseNotFoundError):
        confirm_attachment(
            db, "user-1", "exp-1", "user-1/exp-1/abc.jpg", "image/jpeg", 1024
        )


# --- list_attachments ---


def test_list_attachments_returns_all_for_expense() -> None:
    db = _mock_db()
    attachments = [_make_attachment(), _make_attachment(id="att-2")]
    db.execute.side_effect = [
        _result(_make_expense()),
        _result(all_=attachments),
    ]

    result = list_attachments(db, "user-1", "exp-1")

    assert result == attachments


def test_list_attachments_raises_when_expense_not_owned() -> None:
    db = _mock_db()
    db.execute.return_value = _result(None)

    with pytest.raises(ExpenseNotFoundError):
        list_attachments(db, "user-1", "exp-1")


# --- create_download_url ---


def test_create_download_url_returns_signed_url(monkeypatch) -> None:
    db = _mock_db()
    db.execute.side_effect = [
        _result(_make_expense()),
        _result(_make_attachment()),
    ]
    client = _mock_s3(monkeypatch)
    client.generate_presigned_url.return_value = "https://signed.example/get"

    url = create_download_url(db, "user-1", "exp-1", "att-1")

    assert url == "https://signed.example/get"
    assert client.generate_presigned_url.call_args.args[0] == "get_object"


def test_create_download_url_raises_when_attachment_not_found(monkeypatch) -> None:
    db = _mock_db()
    db.execute.side_effect = [_result(_make_expense()), _result(None)]
    _mock_s3(monkeypatch)

    with pytest.raises(AttachmentNotFoundError):
        create_download_url(db, "user-1", "exp-1", "att-1")


# --- delete_attachment ---


def test_delete_attachment_removes_object_and_row(monkeypatch) -> None:
    db = _mock_db()
    attachment = _make_attachment()
    db.execute.side_effect = [_result(_make_expense()), _result(attachment)]
    client = _mock_s3(monkeypatch)

    delete_attachment(db, "user-1", "exp-1", "att-1")

    client.delete_object.assert_called_once()
    db.delete.assert_called_once_with(attachment)
    db.commit.assert_called_once()
