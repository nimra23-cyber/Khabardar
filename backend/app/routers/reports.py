"""Reports router: POST /api/reports/generate (Phase 6).

Formats a REAL detection result (passed by the client) into a structured report
plus a downloadable Markdown document. Stateless and privacy-safe: it reformats
data the user already received and persists nothing, so it respects public-demo
mode and never exposes other users' records.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.envelope import success
from app.schemas.reports import GenerateReportRequest, ReportResult
from app.services.reports import build_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate")
def generate(payload: GenerateReportRequest) -> dict:
    """Generate a structured + Markdown report from a detection result."""
    built = build_report(payload.model_dump())
    return success(ReportResult(**built).model_dump())
