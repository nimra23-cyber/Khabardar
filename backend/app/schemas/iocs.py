"""Schemas for the IOC extraction endpoint (Phase 5)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractIOCRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


class IOCOut(BaseModel):
    ioc_type: str
    # Masked display value (sensitive IOCs are masked; non-sensitive kept).
    display_value: str
    note: str


class IOCExtractResult(BaseModel):
    count: int
    iocs: list[IOCOut]
    integration_states: dict[str, str]
    note: str
