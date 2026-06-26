from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(str(get_settings().database_url), pool_pre_ping=True)
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
    # Import feature model modules here as they are added so Alembic sees them.
    return None


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
