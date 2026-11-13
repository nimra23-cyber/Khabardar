"""Generic parameterized ORM repository (Req 19.7).

A small, typed base class that all concrete repositories build on. Every
operation uses the SQLAlchemy ORM / Core expression API, which binds values as
query parameters -- there is NO raw SQL string formatting here, so crafted
input cannot alter query structure (SQL-injection mitigation, threat T5).

Transaction discipline: write helpers commit on success and roll back on any
failure so a failed write never leaves a partial/inconsistent row (Req 20.4).
On rollback the original exception is re-raised for the caller to surface.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Parameterized CRUD over a single ORM model."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- reads (all parameterized via ORM expression binding) --------------

    def get(self, id_: str) -> ModelT | None:
        """Fetch one row by primary key (value is bound, never interpolated)."""
        return self.db.get(self.model, id_)

    def list(self, *, limit: int | None = None, offset: int = 0) -> list[ModelT]:
        """List rows (optionally paginated); newest-first if the model has
        ``created_at``."""
        stmt = select(self.model)
        order_col = getattr(self.model, "created_at", None)
        if order_col is not None:
            stmt = stmt.order_by(order_col.desc())
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        from sqlalchemy import func

        return int(
            self.db.scalar(select(func.count()).select_from(self.model)) or 0
        )

    # --- writes (commit/rollback, no partial rows) -------------------------

    def add(self, obj: ModelT) -> ModelT:
        """Persist a new/changed ORM instance atomically.

        Commits on success; on ANY error rolls back (so no partial row is
        left) and re-raises. The caller decides how to surface the failure
        (e.g. Req 20.4 ``save_error`` while still returning the computed
        result).
        """
        try:
            self.db.add(obj)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        """Delete a row atomically (commit on success, rollback on failure)."""
        try:
            self.db.delete(obj)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
