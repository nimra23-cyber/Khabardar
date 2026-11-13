"""Scan history router: GET /api/history (Task 6.5).

Returns ONLY the acting (local) user's scan records, newest-first, with masked
content only. Empty account -> empty list (empty-state, not an error; Req 20.6).
User isolation via the parameterized repository (Req 20.5, 19.7).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.envelope import success
from app.core.errors import AppError
from app.db.session import get_db
from app.routers.deps import current_user_id
from app.repositories.scan_history import ScanHistoryRepository

router = APIRouter(prefix="/api", tags=["history"])

_HISTORY_LIMIT = 100


class HistoryUnavailableError(AppError):
    """History is disabled in public-demo mode. HTTP 503, no records exposed."""

    status_code = 503
    code = "HISTORY_DISABLED"


@router.get("/history")
def list_history(db: Session = Depends(get_db)) -> dict:
    """List the local user's recent scans (masked content only).

    DISABLED in public-demo mode: returns a safe 503 and NEVER reads or exposes
    any stored records to anonymous visitors.
    """
    settings = get_settings()
    if settings.public_demo:
        raise HistoryUnavailableError(
            "Scan history is unavailable in the public demo.",
            operation="/api/history",
        )

    user_id = current_user_id(db)
    repo = ScanHistoryRepository(db)
    rows = repo.list_for_user(user_id, limit=_HISTORY_LIMIT)
    items = [
        {
            "id": r.id,
            "scan_type": r.scan_type,
            "masked_content": r.masked_content,
            "risk_score": r.risk_score,
            "classification": r.classification,
            "category": r.category,
            "confidence": r.confidence,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return success({"items": items, "count": len(items)})
