"""Request/response schemas for the URL analyzer endpoint (Phase 3)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.detection.classify import Classification


class AnalyzeURLRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class URLIndicator(BaseModel):
    id: str
    name: str
    evidence: str
    weight: int


class URLAnalysisResult(BaseModel):
    url: str
    domain: str
    scheme: str
    is_ip_url: bool
    blocked: bool
    risk_score: int = Field(ge=0, le=100)
    classification: Classification
    indicators: list[URLIndicator]
    integration_states: dict[str, str]
    redirect_chain: list[str]
    network_checks: str
    recommended_action: str
    explanation_en: str
    ruleset_version: str
