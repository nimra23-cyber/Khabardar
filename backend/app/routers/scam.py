"""Scam detector router: POST /api/scam/detect (Task 2.13).

Validates input (1..10000 chars), runs the local rule-based pipeline, persists
a masked record for the local user, and returns the standard success envelope.
Length violations raise ``ValidationAppError`` -> 400 INVALID_LENGTH. No AI
keys, no network, no raw-content logging.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.envelope import success
from app.core.errors import ValidationAppError
from app.db.session import get_db
from app.routers.deps import current_user_id
from app.schemas.scam import DetectRequest, DetectResult
from app.services.detection.pipeline import run_detection

router = APIRouter(prefix="/api/scam", tags=["scam"])

MAX_TEXT = 10000


@router.post("/detect")
def detect(payload: DetectRequest, db: Session = Depends(get_db)) -> dict:
    """Analyze submitted text for scam indicators (Req 5, 7).

    In PUBLIC DEMO mode the result is computed but NOT persisted: no shared,
    unauthenticated scan-history store is created. Detection itself is
    unaffected.
    """
    text = payload.text
    # Pydantic already enforces 1..10000; defensive re-check for a clear code.
    if not text or len(text) > MAX_TEXT:
        raise ValidationAppError(
            "Submitted text must be between 1 and 10000 characters.",
            operation="/api/scam/detect",
            code="INVALID_LENGTH",
        )

    settings = get_settings()
    if settings.public_demo:
        # No persistence: do not create/read a shared history for anon visitors.
        result = run_detection(text, db=None, user_id=None)
    else:
        user_id = current_user_id(db)
        result = run_detection(text, db=db, user_id=user_id)

    # Validate the outbound shape before returning (no internal leakage).
    validated = DetectResult(**result)
    return success(validated.model_dump())
