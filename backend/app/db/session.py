from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings


def build_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.db_connect_timeout},
    )


def session_scope(engine: Engine) -> Iterator[Session]:
    """Routes explicitly commit successful writes; uncommitted work is rolled back on close."""
    with Session(engine) as session:
        yield session
