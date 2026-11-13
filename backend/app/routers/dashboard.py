"""SOC dashboard router: GET /api/dashboard/stats (Phase 6).

Returns real aggregated metrics from persisted scans. In public-demo mode no
scans are persisted, so metrics are all 0 with ``empty: true`` (honest empty
state, never fabricated). Labeled a prototype environment (Req 15.8).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.envelope import success
from app.db.session import get_db
from app.schemas.dashboard import DashboardStats
from app.services.dashboard import compute_stats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    """Aggregate real dashboard metrics from the scan history."""
    settings = get_settings()
    data = compute_stats(db, public_demo=settings.public_demo)
    validated = DashboardStats(**data)
    return success(validated.model_dump())
