"""URLAnalysis model (Req 20.1). Optional detail linked to a scan; records the
redirect chain, indicators, and per-integration availability states."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, created_at_col, uuid_pk


class URLAnalysis(Base):
    __tablename__ = "url_analysis"

    id: Mapped[str] = uuid_pk()
    scan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_history.id"), nullable=False, index=True
    )
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redirect_chain: Mapped[list | None] = mapped_column(JSON, nullable=True)
    indicators: Mapped[list | None] = mapped_column(JSON, nullable=True)
    integration_states: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = created_at_col()
