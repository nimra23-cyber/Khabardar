"""Schemas for the report generation endpoint (Phase 6).

The request carries a detection result the client claims to have received. We
do NOT blindly trust it: the classification is constrained to the allowed set,
the score is range-checked, signals are bounded and structurally validated, and
every free-text field is length-capped. Semantic consistency (score vs
classification) and Markdown-injection neutralization are enforced in the
service layer (``services/reports/generate.py``).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# The only classifications the platform recognizes (Req 5.4).
ALLOWED_CLASSIFICATIONS = {"SAFE", "SUSPICIOUS", "HIGH RISK"}

MAX_SIGNALS = 50
MAX_EVIDENCE_PER_SIGNAL = 10
MAX_FIELD_LEN = 2000
MAX_EVIDENCE_LEN = 500


class ReportSignalIn(BaseModel):
    """A single signal in the report request (structurally validated)."""

    name: str = Field(min_length=1, max_length=200)
    evidence: list[str] = Field(default_factory=list, max_length=MAX_EVIDENCE_PER_SIGNAL)

    @field_validator("evidence")
    @classmethod
    def _cap_evidence(cls, v: list[str]) -> list[str]:
        # Cap each evidence string length; drop non-strings defensively.
        return [str(e)[:MAX_EVIDENCE_LEN] for e in v][:MAX_EVIDENCE_PER_SIGNAL]


class GenerateReportRequest(BaseModel):
    """A detection result to format. Fields are validated, not trusted blindly."""

    risk_score: int = Field(ge=0, le=100)
    classification: str
    category: str | None = Field(default=None, max_length=100)
    signals: list[ReportSignalIn] = Field(default_factory=list, max_length=MAX_SIGNALS)
    explanation_en: str = Field(default="", max_length=MAX_FIELD_LEN)
    explanation_ur: str = Field(default="", max_length=MAX_FIELD_LEN)
    ruleset_version: str | None = Field(default=None, max_length=100)

    @field_validator("classification")
    @classmethod
    def _allowed_classification(cls, v: str) -> str:
        up = (v or "").strip().upper()
        if up not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(
                f"classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}"
            )
        return up


class ReportResult(BaseModel):
    report: dict
    markdown: str
    filename: str
