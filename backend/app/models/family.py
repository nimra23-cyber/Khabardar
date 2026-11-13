"""FamilyGroups and FamilyMembers models (Req 20.1).

Tables exist for schema completeness; their consent/sharing write flows are
Scope B placeholders in the MVP. `masked_contact` stores a masked value only
(Req 21).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_col, uuid_pk


class FamilyGroup(Base):
    __tablename__ = "family_groups"

    id: Mapped[str] = uuid_pk()
    owner_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = created_at_col()


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[str] = uuid_pk()
    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("family_groups.id"), nullable=False, index=True
    )
    # Masked contact only (Req 21): never a raw phone/email.
    masked_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    invite_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )  # pending|accepted|expired
    invite_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
