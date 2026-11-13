"""Media scanner router: POST /api/media/scan (Req 12).

Accepts an image upload (PNG/JPEG/WEBP, max 10 MB), runs OCR and QR decode,
extracts URLs, and feeds results through the existing detection pipelines.

Security properties:
- Magic-byte validation (not Content-Type trust).
- Temp files cleaned up in ALL paths (success + errors) via finally.
- Random temp filenames (uuid4) only.
- No permanent storage.
- Extracted text, QR values, and URLs are NEVER logged.
- In public-demo mode: db=None — no persistence of extracted content.
- Safe error envelopes: no filenames, paths, or stack traces leaked.
- Size check on Content-Length header as fast-fail before reading full body.
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.envelope import success
from app.schemas.media import MediaScanData, OCROutput, QROutput
from app.services.detection.pipeline import run_detection
from app.services.media.extract import extract_urls
from app.services.media.ocr import run_ocr
from app.services.media.qr_decode import decode_qr
from app.services.media.upload_validation import (
    MAX_FILE_BYTES,
    UploadValidationError,
    validate_upload,
)
from app.services.url.pipeline import analyze_url

_logger = logging.getLogger("khabardar.media")

router = APIRouter(prefix="/api/media", tags=["media"])

# Shared error envelope structure.
def _error(code: str, message: str, operation: str = "/api/media/scan") -> dict:
    return {"ok": False, "error": {"code": code, "message": message, "operation": operation}}


@router.post("/scan")
async def media_scan(request: Request, image: UploadFile) -> JSONResponse:
    """Analyze an uploaded image for OCR text, QR codes, and URLs.

    Accepts multipart/form-data with field ``image`` (PNG/JPEG/WEBP, max 10 MB).

    Returns a structured result with:
    - OCR extracted text and availability flag
    - QR decoded values and availability flag
    - All URLs found (from OCR text + QR values)
    - Text scam analysis (via existing detection pipeline)
    - URL analyses (via existing URL analyzer)
    """
    settings = get_settings()
    temp_path: str | None = None

    # Fast-fail: check Content-Length header BEFORE reading the full body.
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            cl = int(content_length)
            if cl > MAX_FILE_BYTES:
                return JSONResponse(
                    status_code=413,
                    content=_error(
                        "FILE_TOO_LARGE",
                        "File exceeds the maximum allowed size of 10 MB.",
                    ),
                )
        except (ValueError, TypeError):
            pass  # Malformed header; proceed and let actual read enforce limit.

    try:
        # Read the uploaded file bytes.
        try:
            data = await image.read()
        except Exception:
            return JSONResponse(
                status_code=400,
                content=_error("READ_ERROR", "Could not read the uploaded file."),
            )

        # Actual size check (overrides Content-Length spoofing).
        if len(data) > MAX_FILE_BYTES:
            return JSONResponse(
                status_code=413,
                content=_error(
                    "FILE_TOO_LARGE",
                    "File exceeds the maximum allowed size of 10 MB.",
                ),
            )

        # Validate the upload (magic bytes, dimensions, pixel count, Pillow open).
        try:
            validated = validate_upload(data)
        except UploadValidationError as exc:
            # Safe message: exc.args[0] is already a user-safe string (no paths/filenames).
            return JSONResponse(
                status_code=400,
                content=_error("INVALID_IMAGE", str(exc)),
            )
        except Exception:
            return JSONResponse(
                status_code=400,
                content=_error("INVALID_IMAGE", "The uploaded file could not be validated."),
            )

        temp_path = validated.temp_path
        pil_image = validated.image
        image_type = validated.image_type

        # --- OCR ---
        ocr_result = run_ocr(pil_image)
        ocr_text: str | None = ocr_result.get("text")

        # --- QR Decode ---
        qr_result = decode_qr(pil_image)
        qr_values: list[str] = qr_result.get("values", [])

        # --- URL Extraction ---
        # Collect URLs from OCR text + QR decoded values (treat each QR value as text too).
        urls_found: list[str] = []
        if ocr_text:
            urls_found.extend(extract_urls(ocr_text))
        for qr_val in qr_values:
            urls_found.extend(extract_urls(qr_val))
            # Also add QR value directly if it looks like a URL.
            if qr_val.startswith(("http://", "https://")) and qr_val not in urls_found:
                urls_found.append(qr_val)

        # Deduplicate while preserving order.
        seen: set[str] = set()
        unique_urls: list[str] = []
        for u in urls_found:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)
        urls_found = unique_urls

        # --- Text Scam Analysis ---
        text_analysis: dict | None = None
        if ocr_text:
            # Public demo: db=None, user_id=None — no persistence.
            text_analysis = run_detection(ocr_text, db=None, user_id=None)

        # --- URL Analysis ---
        url_analyses: list[dict] = []
        for url in urls_found:
            url_analyses.append(analyze_url(url))

        # --- Build response ---
        data_payload = MediaScanData(
            ocr=OCROutput(
                available=ocr_result["available"],
                text=ocr_text,
                error=ocr_result.get("error"),
            ),
            qr=QROutput(
                available=qr_result["available"],
                values=qr_values,
                error=qr_result.get("error"),
            ),
            urls_found=urls_found,
            text_analysis=text_analysis,
            url_analyses=url_analyses,
            image_type=image_type,
            public_demo=settings.public_demo,
        )

        return JSONResponse(
            status_code=200,
            content=success(data_payload.model_dump()),
        )

    finally:
        # Clean up temp file in ALL paths — success and all error branches.
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
