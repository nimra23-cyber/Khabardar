"""ScanHistory repository -- the enforced privacy + XSS boundary (Req 19.6, 21).

Every scan persisted to the database goes through ``create_scan`` here. That
method is the SINGLE write path for user-submitted scan content, and it always:

1. masks sensitive values (privacy service) so no plaintext OTP/password/token/
   email/phone/CNIC/account survives (Req 21.1, 21.2, 21.4), THEN
2. neutralizes executable markup (sanitize service) so the stored text contains
   no XSS/script/markup (Req 19.6),

before writing. The two transforms are composed so the stored ``masked_content``
is both privacy-masked AND inert.

Raw submitted content is NEVER accepted into any other column: the method
signature takes ``raw_content`` and writes only the transformed form into
``masked_content``. There is no setter that stores the raw value, so direct
repository use cannot bypass the masking/neutralization boundary.

All access is parameterized ORM (via ``BaseRepository``) -- no raw SQL (Req
19.7). Writes are atomic: a failed insert rolls back with no partial row
(Req 20.4).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scan_history import ScanHistory
from app.repositories.base import BaseRepository
from app.services.privacy import safe_for_storage
from app.services.sanitize import neutralize


def harden_content(raw_content: str | None) -> str | None:
    """Apply the full persistence transform to attacker-controlled content.

    Order matters: mask sensitive values FIRST (so secrets are gone before any
    other processing), THEN neutralize markup (so the stored form is inert).
    Returns ``None`` for ``None`` input (nothing to store).

    This is the one place the transform is defined; both the repository and any
    test/guard call it so there is a single, auditable boundary.
    """
    if raw_content is None:
        return None
    masked = safe_for_storage(raw_content)
    return neutralize(masked)


class ScanHistoryRepository(BaseRepository[ScanHistory]):
    model = ScanHistory

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create_scan(
        self,
        *,
        user_id: str,
        scan_type: str,
        raw_content: str | None,
        risk_score: int | None = None,
        classification: str | None = None,
        category: str | None = None,
        signals: list | dict | None = None,
        explanation_en: str | None = None,
        explanation_ur: str | None = None,
        confidence: float | None = None,
        origin: str = "verified",
    ) -> ScanHistory:
        """Persist a scan with content hardened at the boundary.

        ``raw_content`` is the user's submitted scam text. It is masked +
        neutralized into ``masked_content``; the raw value is NOT stored in any
        field. Commits atomically; rolls back (no partial row) and re-raises on
        failure so the caller can honour Req 20.4.
        """
        record = ScanHistory(
            user_id=user_id,
            scan_type=scan_type,
            masked_content=harden_content(raw_content),
            risk_score=risk_score,
            classification=classification,
            category=category,
            signals=signals,
            explanation_en=explanation_en,
            explanation_ur=explanation_ur,
            confidence=confidence,
            origin=origin,
        )
        return self.add(record)  # BaseRepository.add -> commit/rollback

    def list_for_user(
        self, user_id: str, *, limit: int | None = None, offset: int = 0
    ) -> list[ScanHistory]:
        """Return a user's scans, newest-first (parameterized; user-scoped).

        ``user_id`` is bound as a query parameter (Req 19.7); results are
        restricted to the owning user (supports Req 20.5 isolation).
        """
        stmt = (
            select(ScanHistory)
            .where(ScanHistory.user_id == user_id)
            .order_by(ScanHistory.created_at.desc())
        )
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())
