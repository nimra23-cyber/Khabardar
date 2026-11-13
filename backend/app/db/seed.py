"""Idempotent single-local-user seed (Task 2.1).

The MVP runs as a single local user (design: Users model note). That user has:
- a fixed, non-sensitive placeholder ``username`` (``LOCAL_USERNAME``),
- ``password_hash = None`` -- the MVP is auth-less; NO password/credential is
  created (full auth is Scope B, Req 18),
- ``role = None`` -- RBAC is Scope B.

The seed is idempotent: it inserts the local user only if absent, so repeated
application starts never create duplicates. It stores no credential and emits
no sensitive value to logs or responses.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

# Fixed, non-sensitive placeholder identity for the single local user. This is
# not a credential and contains no PII; it is a stable handle for ownership of
# local scans/history in single-user mode.
LOCAL_USERNAME = "local"


def get_or_create_local_user(db: Session) -> User:
    """Return the single local user, creating it idempotently if missing.

    Safe under concurrent/repeated starts: a UNIQUE(username) constraint backs
    the idempotency, and we re-query on the (rare) race where another starter
    inserted first.
    """
    existing = db.scalar(select(User).where(User.username == LOCAL_USERNAME))
    if existing is not None:
        return existing

    user = User(username=LOCAL_USERNAME)  # password_hash/role stay None
    db.add(user)
    try:
        db.commit()
    except Exception:
        # Lost a race (unique constraint): roll back and return the existing row.
        db.rollback()
        return db.scalar(select(User).where(User.username == LOCAL_USERNAME))
    db.refresh(user)
    return user


def seed_local_user() -> None:
    """Open a session and ensure the single local user exists (startup hook)."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        get_or_create_local_user(db)
    finally:
        db.close()
