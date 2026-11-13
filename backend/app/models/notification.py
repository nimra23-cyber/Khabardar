"""Notifications model (Req 20.1). Delivery flow is a Scope B placeholder."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_col, uuid_pk


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = uuid_pk()
    group_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("family_groups.id"), nullable=True, index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = created_at_col()
