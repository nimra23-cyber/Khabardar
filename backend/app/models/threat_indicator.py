"""ThreatIndicators model (Req 20.1, 13.5).

Dedup is enforced by a UNIQUE constraint on `(ioc_type, normalized_value)`.
Every row carries an `origin` (verified|synthetic) for provenance.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow, uuid_pk


class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"
    __table_args__ = (
        UniqueConstraint("ioc_type", "normalized_value", name="uq_ioc_type_value"),
    )

    id: Mapped[str] = uuid_pk()
    # phone|email|domain|url|wallet|bank|payment_ref|brand|category|campaign
    ioc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(512), nullable=False)
    campaign_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scam_campaigns.id"), nullable=True, index=True
    )
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="verified")
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
