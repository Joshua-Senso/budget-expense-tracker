import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://expense:expense@localhost:5432/expense"
)

from app.core.db import BETTER_AUTH_TABLES, include_app_object, is_app_table  # noqa: E402


def test_better_auth_tables_are_excluded_from_alembic() -> None:
    for table_name in BETTER_AUTH_TABLES:
        assert not is_app_table(table_name)
        assert not include_app_object(None, table_name, "table", True, None)


def test_app_tables_are_included_in_alembic() -> None:
    assert is_app_table("expenses")
    assert include_app_object(None, "expenses", "table", False, None)
