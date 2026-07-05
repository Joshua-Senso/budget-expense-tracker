from datetime import UTC, datetime, timedelta
from io import BytesIO
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


def test_export_expenses_returns_workbook_with_filename(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.features.import_export.router.service.build_export_workbook",
        lambda db, user_id, year: BytesIO(b"fake-xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.features.import_export.router.service.export_filename",
        lambda year: f"expenses-{year}-2026-07-05.xlsx",
    )
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key)

    response = client.get(
        "/import-export/export/2026", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.content == b"fake-xlsx-bytes"
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="expenses-2026-2026-07-05.xlsx"'
    )


def test_export_expenses_requires_auth(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())

    response = client.get("/import-export/export/2026")

    assert response.status_code == 401


def test_export_expenses_rejects_non_numeric_year(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key)

    response = client.get(
        "/import-export/export/abcd", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


def _upload(
    client: Any, token: str, year: str = "2026", filename: str = "expenses.xlsx"
):
    return client.post(
        f"/import-export/import/{year}",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, BytesIO(b"fake-bytes"), "application/octet-stream")},
    )


def test_import_expenses_returns_summary(monkeypatch) -> None:
    from app.features.import_export.schemas import ImportSummary

    monkeypatch.setattr(
        "app.features.import_export.router.service.import_workbook",
        lambda db, user_id, contents, filename, year: ImportSummary(
            inserted=1, updated=2, deleted=3
        ),
    )
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key)

    response = _upload(client, token)

    assert response.status_code == 200
    assert response.json() == {"inserted": 1, "updated": 2, "deleted": 3}


def test_import_expenses_requires_auth(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())

    response = client.post(
        "/import-export/import/2026",
        files={"file": ("expenses.xlsx", BytesIO(b"fake"), "application/octet-stream")},
    )

    assert response.status_code == 401


def test_import_expenses_returns_400_on_parse_error(monkeypatch) -> None:
    from app.features.import_export.service import WorkbookParseError

    def raise_parse_error(db, user_id, contents, filename, year):
        raise WorkbookParseError("Missing required columns: Amount")

    monkeypatch.setattr(
        "app.features.import_export.router.service.import_workbook", raise_parse_error
    )
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key)

    response = _upload(client, token)

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_import_expenses_returns_422_with_row_errors_on_validation_failure(
    monkeypatch,
) -> None:
    from app.features.import_export.service import ImportValidationError

    def raise_validation_error(db, user_id, contents, filename, year):
        raise ImportValidationError(
            [{"row": 3, "messages": ["Description is required."]}]
        )

    monkeypatch.setattr(
        "app.features.import_export.router.service.import_workbook",
        raise_validation_error,
    )
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client = make_client_with_jwk(monkeypatch, private_key.public_key())
    token = make_token(private_key)

    response = _upload(client, token)

    assert response.status_code == 422
    assert response.json()["detail"] == [
        {"row": 3, "messages": ["Description is required."]}
    ]
