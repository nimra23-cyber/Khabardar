"""ScanHistory model (Req 20.1, 20.3, 21).

The central scan record. `masked_content` stores ONLY masked content -- never
plaintext OTPs/passwords/tokens/PII (Req 21.2, 21.4). `origin` distinguishes
verified vs synthetic data.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, created_at_col, uuid_pk


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    scan_type: Mapped[str] = mapped_column(String(16), nullable=False)  # text|url|media
    # Masked content only (Req 21). Never plaintext secrets.
    masked_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0..100
    classification: Mapped[str | None] = mapped_column(String(16), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signals: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    explanation_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_ur: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0..1
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="verified")
    created_at: Mapped[datetime] = created_at_col()
