"""ScamReports model (Req 20.1). Derived from a scan; `shared_with` is a
Scope B family-sharing placeholder (no write flow in the MVP)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, created_at_col, uuid_pk


class ScamReport(Base):
    __tablename__ = "scam_reports"

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    scan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_history.id"), nullable=False, index=True
    )
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    shared_with: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = created_at_col()
