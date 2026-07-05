from functools import lru_cache

import boto3
from botocore.client import BaseClient

from app.core.config import Settings, get_settings


class StorageNotConfiguredError(RuntimeError):
    pass


def _require_storage_config(settings: Settings) -> None:
    missing = [
        env_name
        for env_name, value in [
            ("S3_ENDPOINT_URL", settings.s3_endpoint_url),
            ("S3_REGION", settings.s3_region),
            ("S3_ACCESS_KEY_ID", settings.s3_access_key_id),
            ("S3_SECRET_ACCESS_KEY", settings.s3_secret_access_key),
            ("RECEIPTS_BUCKET", settings.receipts_bucket),
        ]
        if not value
    ]
    if missing:
        raise StorageNotConfiguredError(
            "Receipt storage is not configured; missing: " + ", ".join(missing)
        )


@lru_cache
def get_s3_client() -> BaseClient:
    settings = get_settings()
    _require_storage_config(settings)
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )


def get_receipts_bucket() -> str:
    settings = get_settings()
    _require_storage_config(settings)
    assert settings.receipts_bucket is not None
    return settings.receipts_bucket
