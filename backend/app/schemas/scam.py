"""Request/response schemas for the scam detector endpoint (Task 2.13)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.detection.classify import Classification


class DetectRequest(BaseModel):
    """Scam detection request body (Req 5.1/5.2: 1..10000 chars)."""

    text: str = Field(min_length=1, max_length=10000)


class SignalOut(BaseModel):
    """A triggered signal as returned to the client."""

    signal_id: str
    name: str
    explanation: str
    direction: str
    evidence: list[str]
    languages: list[str]


class DetectResult(BaseModel):
    """Scam detection result payload (inside the success envelope's ``data``)."""

    risk_score: int = Field(ge=0, le=100)
    classification: Classification
    category: str | None
    signals: list[SignalOut]
    explanation_en: str
    explanation_ur: str
    confidence: float = Field(ge=0.0, le=1.0)
    detected_languages: list[str]
    no_signals_detected: bool
    no_signal_notice: str | None
    ruleset_version: str
    timestamp: str
    scan_id: str | None = None
    save_error: bool = False
