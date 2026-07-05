import pytest

from app.core.config import Settings
from app.core.storage import (
    StorageNotConfiguredError,
    get_receipts_bucket,
    get_s3_client,
)


def _settings(**overrides) -> Settings:
    defaults = {
        "database_url": "postgresql://expense:expense@localhost:5432/expense",
        "redis_url": "redis://localhost:6379/0",
        "auth_jwks_url": "http://localhost:4000/api/auth/jwks",
        "auth_jwt_issuer": "http://localhost:4000",
        "auth_jwt_audience": "expense-api",
        "frontend_origin": "http://localhost:3000",
        "s3_endpoint_url": None,
        "s3_region": None,
        "s3_access_key_id": None,
        "s3_secret_access_key": None,
        "receipts_bucket": None,
    }
    return Settings(**{**defaults, **overrides})


def test_settings_do_not_require_s3_config() -> None:
    settings = _settings()

    assert settings.s3_endpoint_url is None
    assert settings.receipts_bucket is None


def test_get_s3_client_raises_when_storage_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr("app.core.storage.get_settings", _settings)
    get_s3_client.cache_clear()

    with pytest.raises(StorageNotConfiguredError):
        get_s3_client()

    get_s3_client.cache_clear()


def test_get_s3_client_succeeds_when_storage_configured(monkeypatch) -> None:
    configured = _settings(
        s3_endpoint_url="http://localhost:9000",
        s3_region="auto",
        s3_access_key_id="minioadmin",
        s3_secret_access_key="minioadmin",
        receipts_bucket="receipts",
    )
    monkeypatch.setattr("app.core.storage.get_settings", lambda: configured)
    get_s3_client.cache_clear()

    client = get_s3_client()

    assert client is not None
    get_s3_client.cache_clear()


def test_get_receipts_bucket_raises_when_storage_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr("app.core.storage.get_settings", _settings)

    with pytest.raises(StorageNotConfiguredError):
        get_receipts_bucket()


def test_get_receipts_bucket_returns_configured_bucket(monkeypatch) -> None:
    configured = _settings(
        s3_endpoint_url="http://localhost:9000",
        s3_region="auto",
        s3_access_key_id="minioadmin",
        s3_secret_access_key="minioadmin",
        receipts_bucket="receipts",
    )
    monkeypatch.setattr("app.core.storage.get_settings", lambda: configured)

    assert get_receipts_bucket() == "receipts"
