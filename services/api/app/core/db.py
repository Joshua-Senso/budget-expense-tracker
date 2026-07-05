from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


BETTER_AUTH_TABLES = frozenset(
    {
        "accounts",
        "invitations",
        "jwks",
        "members",
        "organizations",
        "sessions",
        "users",
        "verifications",
    }
)


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().sqlalchemy_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def import_app_models() -> None:
    import app.features.attachments.models  # noqa: F401
    import app.features.budget.models  # noqa: F401
    import app.features.categories.models  # noqa: F401
    import app.features.expenses.models  # noqa: F401
    import app.features.recurring.models  # noqa: F401


def is_app_table(name: str | None) -> bool:
    if name is None:
        return True
    return name not in BETTER_AUTH_TABLES


def include_app_object(
    object_: Any,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    del reflected, compare_to
    if type_ == "table":
        return is_app_table(name)
    table = getattr(object_, "table", None)
    if table is not None:
        return is_app_table(table.name)
    return True
