from arq.connections import RedisSettings

from app.core.config import get_settings


def get_arq_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(str(get_settings().redis_url))
