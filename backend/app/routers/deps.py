"""Shared router dependencies (Task 2.13).

``current_user_id`` resolves the single local user (MVP single-user mode, the
``get_current_user`` seam from the design). It is a no-op resolver now and
becomes a JWT validator in Scope B (Req 18) without changing routers.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.seed import LOCAL_USERNAME, get_or_create_local_user

__all__ = ["get_db", "current_user_id", "Session", "Iterator"]


def current_user_id(db: Session) -> str:
    """Return the single local user's id, creating it if absent (idempotent)."""
    user = get_or_create_local_user(db)
    return user.id
