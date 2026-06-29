from app.core.config import Settings, get_settings
from app.core.db import BETTER_AUTH_TABLES, include_app_object, is_app_table


def test_better_auth_tables_are_excluded_from_alembic() -> None:
    for table_name in BETTER_AUTH_TABLES:
        assert not is_app_table(table_name)
        assert not include_app_object(None, table_name, "table", True, None)


def test_app_tables_are_included_in_alembic() -> None:
    assert is_app_table("expenses")
    assert include_app_object(None, "expenses", "table", False, None)


def test_database_url_uses_installed_psycopg_driver() -> None:
    assert get_settings().sqlalchemy_database_url.startswith("postgresql+psycopg://")


def test_postgres_url_uses_installed_psycopg_driver() -> None:
    settings = Settings(
        database_url="postgres://expense:expense@localhost:5432/expense",
        redis_url="redis://localhost:6379/0",
        auth_jwks_url="http://localhost:4000/api/auth/jwks",
        auth_jwt_issuer="http://localhost:4000",
        auth_jwt_audience="expense-api",
    )

    assert settings.sqlalchemy_database_url.startswith("postgresql+psycopg://")
