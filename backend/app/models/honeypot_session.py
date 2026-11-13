"""HoneypotSessions model (Req 20.1, 14.5).

Scope B placeholder table. Every row's `origin` is always "synthetic" (Req
14.5): honeypot data is simulated and must be machine-distinguishable from
verified real-world intelligence.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, created_at_col, uuid_pk


class HoneypotSession(Base):
    __tablename__ = "honeypot_sessions"

    id: Mapped[str] = uuid_pk()
    campaign_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scam_campaigns.id"), nullable=True, index=True
    )
    # Always "synthetic" for honeypot data (Req 14.5).
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="synthetic")
    synthetic_conversation: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = created_at_col()
