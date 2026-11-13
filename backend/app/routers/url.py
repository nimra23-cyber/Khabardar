"""URL analyzer router: POST /api/url/analyze (Phase 3).

Validates the URL format (no network request on failure, Req 11.10), runs the
local SSRF-safe heuristic analyzer, and returns the standard success envelope.
A URL that resolves to a blocked range is returned with ``blocked: true`` and
is never contacted (Req 11.3). No external keys required.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.envelope import success
from app.core.errors import ValidationAppError
from app.schemas.url import AnalyzeURLRequest, URLAnalysisResult
from app.services.url import analyze_url

router = APIRouter(prefix="/api/url", tags=["url"])


@router.post("/analyze")
def analyze(payload: AnalyzeURLRequest) -> dict:
    """Analyze a URL for phishing indicators (local heuristics + SSRF policy)."""
    result = analyze_url(payload.url)
    if not result.get("valid"):
        raise ValidationAppError(
            "The submitted URL is invalid or uses an unsupported scheme.",
            operation="/api/url/analyze",
            code="INVALID_URL",
        )
    validated = URLAnalysisResult(**{k: v for k, v in result.items() if k in URLAnalysisResult.model_fields})
    return success(validated.model_dump())
