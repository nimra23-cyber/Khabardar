"""User model (Req 20.1).

MVP seeds a single local user. `password_hash` and `role` exist now (nullable)
so Scope B JWT + RBAC + lockout slot in without a schema rewrite. No plaintext
password is ever stored here (hashing is handled by the auth seam in Scope B).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_col, uuid_pk


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = uuid_pk()
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # Scope B: nullable in single-user mode; never a plaintext password.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = created_at_col()
