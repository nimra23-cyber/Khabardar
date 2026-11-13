"""Declarative base and shared column helpers (Req 20).

Portability: only portable column types are used across all models
(``String``/``Text``/``Integer``/``Boolean``/``DateTime(timezone=True)``/``JSON``),
string UUID primary keys, and no SQLite-only types -- so the same models run on
SQLite (dev) and PostgreSQL (prod).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all KHABARDAR ORM models."""


def uuid_pk():
    """A portable string UUID primary-key column."""
    return mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )


def utcnow() -> datetime:
    """Timezone-aware current UTC timestamp (portable default)."""
    return datetime.now(timezone.utc)


def created_at_col():
    """A timezone-aware created_at column defaulting to now()."""
    return mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
