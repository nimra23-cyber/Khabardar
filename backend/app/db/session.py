"""Engine and session factory (Req 20.2).

The database URL comes from env-based config (``KHABARDAR_DATABASE_URL``),
defaulting to a local SQLite file. A FastAPI dependency (``get_db``) yields a
scoped session per request.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# SQLite needs check_same_thread=False for the dev server's threaded access;
# the arg is ignored by other backends (PostgreSQL), keeping this portable.
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session, future=True
)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yield a session and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
