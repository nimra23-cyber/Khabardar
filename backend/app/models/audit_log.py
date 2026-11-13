"""AuditLogs model (Req 19.5, 20.1).

Records security-relevant actions (auth, data deletion, report sharing,
provider failure, blocked security requests) with actor + timestamp. `detail`
holds non-sensitive diagnostic JSON only (no plaintext secrets).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, utcnow, uuid_pk


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = uuid_pk()
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
