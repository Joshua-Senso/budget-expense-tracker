from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.main import create_app


class SigningKey:
    def __init__(self, key: Any) -> None:
        self.key = key


class FakeJwkClient:
    def __init__(self, public_key: Any) -> None:
        self.public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        del token
        return SigningKey(self.public_key)


def make_client_with_jwk(monkeypatch, public_key: Any) -> TestClient:
    monkeypatch.setattr(
        "app.core.security.get_jwk_client",
        lambda jwks_url: FakeJwkClient(public_key),
    )
    return TestClient(create_app())


def make_token(private_key: Any) -> str:
    payload = {
        "sub": "user-123",
        "iss": "http://localhost:4000",
        "aud": "expense-api",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def _authed_client(monkeypatch) -> tuple[TestClient, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    return client, make_token(private_key)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- upload-url ---


def test_create_upload_url_returns_signed_url(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.attachments.router.service.create_upload_url",
        lambda db, user_id, expense_id, content_type, size_bytes: (
            "https://signed.example/put",
            "user-123/exp-1/abc.jpg",
        ),
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses/exp-1/attachments/upload-url",
        headers=_auth_header(token),
        json={"content_type": "image/jpeg", "size_bytes": 1024},
    )

    assert response.status_code == 201
    assert response.json() == {
        "upload_url": "https://signed.example/put",
        "object_key": "user-123/exp-1/abc.jpg",
        "expires_in": 300,
    }


def test_create_upload_url_requires_auth(monkeypatch) -> None:
    client, _ = _authed_client(monkeypatch)

    response = client.post(
        "/expenses/exp-1/attachments/upload-url",
        json={"content_type": "image/jpeg", "size_bytes": 1024},
    )

    assert response.status_code == 401


def test_create_upload_url_returns_404_when_expense_not_found(monkeypatch) -> None:
    from app.features.attachments.service import ExpenseNotFoundError

    def raise_not_found(db, user_id, expense_id, content_type, size_bytes):
        raise ExpenseNotFoundError(expense_id)

    monkeypatch.setattr(
        "app.features.attachments.router.service.create_upload_url", raise_not_found
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses/exp-1/attachments/upload-url",
        headers=_auth_header(token),
        json={"content_type": "image/jpeg", "size_bytes": 1024},
    )

    assert response.status_code == 404


def test_create_upload_url_returns_422_for_invalid_content_type(monkeypatch) -> None:
    from app.features.attachments.service import InvalidContentTypeError

    def raise_invalid(db, user_id, expense_id, content_type, size_bytes):
        raise InvalidContentTypeError(content_type)

    monkeypatch.setattr(
        "app.features.attachments.router.service.create_upload_url", raise_invalid
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses/exp-1/attachments/upload-url",
        headers=_auth_header(token),
        json={"content_type": "application/pdf", "size_bytes": 1024},
    )

    assert response.status_code == 422


# --- confirm ---


def test_confirm_attachment_returns_created_attachment(monkeypatch) -> None:
    from app.features.attachments.models import ExpenseAttachment

    attachment = ExpenseAttachment(
        id="att-1",
        expense_id="exp-1",
        user_id="user-123",
        object_key="user-123/exp-1/abc.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
        uploaded_at=datetime(2026, 7, 5, tzinfo=UTC),
    )
    monkeypatch.setattr(
        "app.features.attachments.router.service.confirm_attachment",
        lambda db, user_id, expense_id, object_key: attachment,
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses/exp-1/attachments",
        headers=_auth_header(token),
        json={"object_key": "user-123/exp-1/abc.jpg"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "att-1"
    assert "object_key" not in body


def test_confirm_attachment_returns_400_when_object_missing(monkeypatch) -> None:
    from app.features.attachments.service import ObjectNotUploadedError

    def raise_missing(db, user_id, expense_id, object_key):
        raise ObjectNotUploadedError(object_key)

    monkeypatch.setattr(
        "app.features.attachments.router.service.confirm_attachment", raise_missing
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses/exp-1/attachments",
        headers=_auth_header(token),
        json={"object_key": "user-123/exp-1/abc.jpg"},
    )

    assert response.status_code == 400


# --- list ---


def test_list_attachments_returns_metadata(monkeypatch) -> None:
    from app.features.attachments.models import ExpenseAttachment

    attachments = [
        ExpenseAttachment(
            id="att-1",
            expense_id="exp-1",
            user_id="user-123",
            object_key="user-123/exp-1/abc.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
            uploaded_at=datetime(2026, 7, 5, tzinfo=UTC),
        )
    ]
    monkeypatch.setattr(
        "app.features.attachments.router.service.list_attachments",
        lambda db, user_id, expense_id: attachments,
    )
    client, token = _authed_client(monkeypatch)

    response = client.get("/expenses/exp-1/attachments", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "att-1"
    assert "object_key" not in body[0]


def test_list_attachments_returns_404_when_expense_not_found(monkeypatch) -> None:
    from app.features.attachments.service import ExpenseNotFoundError

    def raise_not_found(db, user_id, expense_id):
        raise ExpenseNotFoundError(expense_id)

    monkeypatch.setattr(
        "app.features.attachments.router.service.list_attachments", raise_not_found
    )
    client, token = _authed_client(monkeypatch)

    response = client.get("/expenses/exp-1/attachments", headers=_auth_header(token))

    assert response.status_code == 404


# --- download-url ---


def test_create_download_url_returns_signed_url(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.attachments.router.service.create_download_url",
        lambda db, user_id, expense_id, attachment_id: "https://signed.example/get",
    )
    client, token = _authed_client(monkeypatch)

    response = client.get(
        "/expenses/exp-1/attachments/att-1/download-url", headers=_auth_header(token)
    )

    assert response.status_code == 200
    assert response.json() == {
        "download_url": "https://signed.example/get",
        "expires_in": 300,
    }


def test_create_download_url_returns_404_when_attachment_not_found(monkeypatch) -> None:
    from app.features.attachments.service import AttachmentNotFoundError

    def raise_not_found(db, user_id, expense_id, attachment_id):
        raise AttachmentNotFoundError(attachment_id)

    monkeypatch.setattr(
        "app.features.attachments.router.service.create_download_url", raise_not_found
    )
    client, token = _authed_client(monkeypatch)

    response = client.get(
        "/expenses/exp-1/attachments/att-1/download-url", headers=_auth_header(token)
    )

    assert response.status_code == 404


# --- delete ---


def test_delete_attachment_returns_204(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.attachments.router.service.delete_attachment",
        lambda db, user_id, expense_id, attachment_id: None,
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete(
        "/expenses/exp-1/attachments/att-1", headers=_auth_header(token)
    )

    assert response.status_code == 204


def test_delete_attachment_returns_404_when_not_found(monkeypatch) -> None:
    from app.features.attachments.service import AttachmentNotFoundError

    def raise_not_found(db, user_id, expense_id, attachment_id):
        raise AttachmentNotFoundError(attachment_id)

    monkeypatch.setattr(
        "app.features.attachments.router.service.delete_attachment", raise_not_found
    )
    client, token = _authed_client(monkeypatch)

    response = client.delete(
        "/expenses/exp-1/attachments/att-1", headers=_auth_header(token)
    )

    assert response.status_code == 404


# --- storage not configured ---


def test_create_upload_url_returns_503_when_storage_not_configured(monkeypatch) -> None:
    from app.core.storage import StorageNotConfiguredError

    def raise_unconfigured(db, user_id, expense_id, content_type, size_bytes):
        raise StorageNotConfiguredError("Receipt storage is not configured; missing: ")

    monkeypatch.setattr(
        "app.features.attachments.router.service.create_upload_url", raise_unconfigured
    )
    client, token = _authed_client(monkeypatch)

    response = client.post(
        "/expenses/exp-1/attachments/upload-url",
        headers=_auth_header(token),
        json={"content_type": "image/jpeg", "size_bytes": 1024},
    )

    assert response.status_code == 503
