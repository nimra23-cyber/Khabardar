"""ScamCampaigns model (Req 20.1). Groups related threat indicators; `origin`
distinguishes verified vs synthetic campaigns."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow, uuid_pk


class ScamCampaign(Base):
    __tablename__ = "scam_campaigns"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="verified")
    first_detected: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
