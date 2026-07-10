from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from sqlalchemy.exc import IntegrityError

from app.core.households import HouseholdRoleError
from app.core.storage import StorageNotConfiguredError
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


def _mock_s3(monkeypatch, head_object: dict | None = None) -> MagicMock:
    client = MagicMock()
    client.head_object.return_value = head_object or {
        "ContentType": "image/jpeg",
        "ContentLength": 1024,
    }
    monkeypatch.setattr(
        "app.features.attachments.service.get_s3_client", lambda: client
    )
    return client


# --- create_upload_url ---


def test_create_upload_url_returns_url_and_key_scoped_to_user_and_expense(
    monkeypatch,
) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
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
    db.get.return_value = None
    _mock_s3(monkeypatch)

    with pytest.raises(ExpenseNotFoundError):
        create_upload_url(db, "user-1", "exp-1", "image/jpeg", 1024)


def test_create_upload_url_rejects_unsupported_content_type(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    _mock_s3(monkeypatch)

    with pytest.raises(InvalidContentTypeError):
        create_upload_url(db, "user-1", "exp-1", "application/pdf", 1024)


def test_create_upload_url_rejects_oversized_file(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    _mock_s3(monkeypatch)

    with pytest.raises(AttachmentTooLargeError):
        create_upload_url(db, "user-1", "exp-1", "image/jpeg", MAX_SIZE_BYTES + 1)


# --- confirm_attachment ---


def test_confirm_attachment_creates_row_using_actual_s3_metadata(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    client = _mock_s3(monkeypatch, {"ContentType": "image/png", "ContentLength": 2048})

    attachment = confirm_attachment(db, "user-1", "exp-1", "user-1/exp-1/abc.png")

    client.head_object.assert_called_once()
    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert attachment.object_key == "user-1/exp-1/abc.png"
    assert attachment.content_type == "image/png"
    assert attachment.size_bytes == 2048


def test_confirm_attachment_raises_when_object_key_not_owned(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    _mock_s3(monkeypatch)

    with pytest.raises(ObjectNotUploadedError):
        confirm_attachment(db, "user-1", "exp-1", "other-user/exp-1/abc.jpg")


def test_confirm_attachment_raises_when_object_missing_from_bucket(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    client = _mock_s3(monkeypatch)
    client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
    )

    with pytest.raises(ObjectNotUploadedError):
        confirm_attachment(db, "user-1", "exp-1", "user-1/exp-1/abc.jpg")


def test_confirm_attachment_raises_when_expense_not_owned(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = None
    _mock_s3(monkeypatch)

    with pytest.raises(ExpenseNotFoundError):
        confirm_attachment(db, "user-1", "exp-1", "user-1/exp-1/abc.jpg")


def test_confirm_attachment_rejects_actual_content_type_not_allowed(
    monkeypatch,
) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    _mock_s3(monkeypatch, {"ContentType": "application/pdf", "ContentLength": 1024})

    with pytest.raises(InvalidContentTypeError):
        confirm_attachment(db, "user-1", "exp-1", "user-1/exp-1/abc.jpg")


def test_confirm_attachment_rejects_actual_size_over_cap(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    _mock_s3(
        monkeypatch,
        {"ContentType": "image/jpeg", "ContentLength": MAX_SIZE_BYTES + 1},
    )

    with pytest.raises(AttachmentTooLargeError):
        confirm_attachment(db, "user-1", "exp-1", "user-1/exp-1/abc.jpg")


def test_confirm_attachment_is_idempotent_on_retry(monkeypatch) -> None:
    db = _mock_db()
    existing = _make_attachment(object_key="user-1/exp-1/abc.jpg")
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(existing)
    db.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate key"))
    _mock_s3(monkeypatch)

    attachment = confirm_attachment(db, "user-1", "exp-1", "user-1/exp-1/abc.jpg")

    db.rollback.assert_called_once()
    assert attachment is existing


def test_confirm_attachment_reraises_unexpected_integrity_error(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(None)
    db.commit.side_effect = IntegrityError("insert", {}, Exception("some other cause"))
    _mock_s3(monkeypatch)

    with pytest.raises(IntegrityError):
        confirm_attachment(db, "user-1", "exp-1", "user-1/exp-1/abc.jpg")


# --- list_attachments ---


def test_list_attachments_returns_all_for_expense() -> None:
    db = _mock_db()
    attachments = [_make_attachment(), _make_attachment(id="att-2")]
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(all_=attachments)

    result = list_attachments(db, "user-1", "exp-1")

    assert result == attachments


def test_list_attachments_raises_when_expense_not_owned() -> None:
    db = _mock_db()
    db.get.return_value = None

    with pytest.raises(ExpenseNotFoundError):
        list_attachments(db, "user-1", "exp-1")


# --- create_download_url ---


def test_create_download_url_returns_signed_url(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(_make_attachment())
    client = _mock_s3(monkeypatch)
    client.generate_presigned_url.return_value = "https://signed.example/get"

    url = create_download_url(db, "user-1", "exp-1", "att-1")

    assert url == "https://signed.example/get"
    assert client.generate_presigned_url.call_args.args[0] == "get_object"


def test_create_download_url_raises_when_attachment_not_found(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(None)
    _mock_s3(monkeypatch)

    with pytest.raises(AttachmentNotFoundError):
        create_download_url(db, "user-1", "exp-1", "att-1")


# --- delete_attachment ---


def test_delete_attachment_removes_object_and_row(monkeypatch) -> None:
    db = _mock_db()
    attachment = _make_attachment()
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(attachment)
    client = _mock_s3(monkeypatch)

    delete_attachment(db, "user-1", "exp-1", "att-1")

    client.delete_object.assert_called_once()
    db.delete.assert_called_once_with(attachment)
    db.commit.assert_called_once()


def test_delete_attachment_shared_expense_allowed_for_owner(monkeypatch) -> None:
    db = _mock_db()
    attachment = _make_attachment()
    db.get.return_value = _make_expense(household_id="household-1", user_id="user-2")
    db.scalar.return_value = "owner"  # requester owns household-1
    db.execute.return_value = _result(attachment)
    client = _mock_s3(monkeypatch)

    delete_attachment(db, "user-1", "exp-1", "att-1")

    client.delete_object.assert_called_once()
    db.delete.assert_called_once_with(attachment)


def test_delete_attachment_shared_expense_forbidden_for_non_owner_member(
    monkeypatch,
) -> None:
    """Only the household owner may delete a receipt from a shared expense
    (PRD §10); members may add/view but not edit/delete."""
    db = _mock_db()
    attachment = _make_attachment()
    db.get.return_value = _make_expense(household_id="household-1", user_id="user-2")
    db.scalar.return_value = "member"  # requester is a member, not the owner
    db.execute.return_value = _result(attachment)
    _mock_s3(monkeypatch)

    with pytest.raises(HouseholdRoleError):
        delete_attachment(db, "user-1", "exp-1", "att-1")

    db.delete.assert_not_called()


def test_delete_attachment_commits_db_row_before_deleting_s3_object(
    monkeypatch,
) -> None:
    """The DB row is deleted first so a failed S3 call orphans an object
    rather than leaving a row that points at nothing (see delete_attachment)."""
    db = _mock_db()
    attachment = _make_attachment()
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(attachment)
    client = _mock_s3(monkeypatch)
    calls: list[str] = []
    db.commit.side_effect = lambda: calls.append("commit")
    client.delete_object.side_effect = lambda **kwargs: calls.append("delete_object")

    delete_attachment(db, "user-1", "exp-1", "att-1")

    assert calls == ["commit", "delete_object"]


def test_delete_attachment_swallows_s3_failure_after_db_commit(monkeypatch) -> None:
    db = _mock_db()
    attachment = _make_attachment()
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(attachment)
    client = _mock_s3(monkeypatch)
    client.delete_object.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "boom"}}, "DeleteObject"
    )

    delete_attachment(db, "user-1", "exp-1", "att-1")

    db.commit.assert_called_once()


def test_confirm_attachment_mirrors_household_id_from_expense(monkeypatch) -> None:
    db = _mock_db()
    db.get.return_value = _make_expense(household_id="household-1")
    _mock_s3(monkeypatch)

    attachment = confirm_attachment(db, "user-1", "exp-1", "user-1/exp-1/abc.jpg")

    assert attachment.household_id == "household-1"


def test_list_attachments_visible_to_household_member_not_just_uploader() -> None:
    """Household members must see receipts other members uploaded to a shared
    expense -- not just their own."""
    db = _mock_db()
    db.get.return_value = _make_expense(household_id="household-1", user_id="user-2")
    db.scalar.return_value = "member-1"  # requester is a member of household-1
    other_members_attachment = _make_attachment(user_id="user-2")
    db.execute.return_value = _result(all_=[other_members_attachment])

    result = list_attachments(db, "user-1", "exp-1")

    assert result == [other_members_attachment]


def test_list_attachments_raises_for_household_non_member() -> None:
    db = _mock_db()
    db.get.return_value = _make_expense(household_id="household-1", user_id="user-2")
    db.scalar.return_value = None  # requester is not a member

    with pytest.raises(ExpenseNotFoundError):
        list_attachments(db, "user-1", "exp-1")


def test_delete_attachment_swallows_storage_not_configured_after_db_commit(
    monkeypatch,
) -> None:
    """The DB row is already deleted+committed by the time the storage cleanup
    step runs, so a StorageNotConfiguredError there must not surface as an
    error -- the caller already got the delete they asked for (see the
    Greptile finding on PR #101: this used to leak as an unhandled 503 after
    the row was already gone)."""
    db = _mock_db()
    attachment = _make_attachment()
    db.get.return_value = _make_expense()
    db.execute.return_value = _result(attachment)
    monkeypatch.setattr(
        "app.features.attachments.service.get_receipts_bucket",
        lambda: (_ for _ in ()).throw(
            StorageNotConfiguredError("Receipt storage is not configured")
        ),
    )
    monkeypatch.setattr(
        "app.features.attachments.service.get_s3_client", lambda: MagicMock()
    )

    delete_attachment(db, "user-1", "exp-1", "att-1")

    db.commit.assert_called_once()
    db.delete.assert_called_once_with(attachment)
