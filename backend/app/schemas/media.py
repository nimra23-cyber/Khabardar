"""Pydantic output schemas for the media scan endpoint (Req 12).

Matches the response structure documented in the router docstring.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class OCROutput(BaseModel):
    """OCR extraction result."""

    available: bool
    text: str | None = None
    error: str | None = None


class QROutput(BaseModel):
    """QR code decode result."""

    available: bool
    values: list[str] = []
    error: str | None = None


class MediaScanData(BaseModel):
    """Data payload for a successful media scan response."""

    ocr: OCROutput
    qr: QROutput
    urls_found: list[str]
    # text_analysis: the full DetectResult dict or None if no OCR text.
    text_analysis: dict[str, Any] | None = None
    # url_analyses: one result dict per URL found.
    url_analyses: list[dict[str, Any]] = []
    image_type: Literal["png", "jpeg", "webp"]
    public_demo: bool


class MediaScanResponse(BaseModel):
    """Standard envelope for POST /api/media/scan."""

    ok: bool = True
    data: MediaScanData
