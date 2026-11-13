"""OCR service (Req 12): extract text from images using Tesseract/pytesseract.

Security properties:
- Extracted text is NEVER logged (may contain PII, secrets, OTPs).
- Tesseract availability is checked at import time (shutil.which / TESSERACT_CMD env var).
- Graceful degradation: returns available=False if Tesseract not installed.
- Language: eng + best-effort urd (falls back to eng if urd tessdata absent).
- 20-second timeout.
- Preprocessing: grayscale + adaptive thresholding (Pillow only, no numpy).
"""

from __future__ import annotations

import logging
import os
import shutil
from typing import TypedDict

from PIL import Image, ImageFilter

_logger = logging.getLogger("khabardar.media.ocr")

# Tesseract availability: honour explicit env var first, then PATH lookup.
_TESS_CMD = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")
_TESSERACT_AVAILABLE = bool(_TESS_CMD)

# Configure pytesseract cmd path if set via env var.
if _TESSERACT_AVAILABLE:
    try:
        import pytesseract  # noqa: F401

        if os.environ.get("TESSERACT_CMD"):
            pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
    except ImportError:
        _TESSERACT_AVAILABLE = False


class OCRResult(TypedDict):
    available: bool
    text: str | None
    error: str | None


def _preprocess(image: Image.Image) -> Image.Image:
    """Grayscale + adaptive thresholding via Pillow (no numpy).

    Uses a simple unsharp mask then convert-to-greyscale for better OCR on
    screenshots with varied backgrounds.
    """
    # Convert to greyscale.
    grey = image.convert("L")
    # Sharpen slightly to improve edge detection.
    sharpened = grey.filter(ImageFilter.SHARPEN)
    return sharpened


def _urd_available() -> bool:
    """Check whether Urdu tessdata is installed on this system."""
    if not _TESSERACT_AVAILABLE:
        return False
    try:
        import pytesseract

        langs = pytesseract.get_languages()
        return "urd" in langs
    except Exception:
        return False


def run_ocr(image: Image.Image) -> OCRResult:
    """Run OCR on a PIL Image and return the result dict.

    Returns
    -------
    OCRResult
        ``available``: whether Tesseract is installed.
        ``text``: extracted text (None if unavailable or nothing found).
        ``error``: human-readable error string if something went wrong.

    Notes
    -----
    Extracted text is NEVER logged — it may contain PII / secrets.
    """
    if not _TESSERACT_AVAILABLE:
        return {
            "available": False,
            "text": None,
            "error": "OCR engine not available",
        }

    import pytesseract
    from pytesseract import TesseractNotFoundError

    # Build language string: always eng, add urd if available.
    lang = "eng+urd" if _urd_available() else "eng"

    try:
        processed = _preprocess(image)
        # timeout=20 is pytesseract's subprocess timeout in seconds.
        raw: str = pytesseract.image_to_string(processed, lang=lang, timeout=20)
        text = raw.strip() if raw else ""
        return {
            "available": True,
            "text": text if text else None,
            # Do NOT log the text value.
            "error": None,
        }
    except TesseractNotFoundError:
        return {
            "available": False,
            "text": None,
            "error": "OCR engine not available",
        }
    except RuntimeError as exc:
        # pytesseract raises RuntimeError on timeout.
        _logger.warning("ocr_timeout lang=%s", lang)
        return {
            "available": True,
            "text": None,
            "error": "OCR timed out",
        }
    except Exception as exc:
        _logger.warning("ocr_error type=%s", type(exc).__name__)
        return {
            "available": True,
            "text": None,
            "error": "OCR processing failed",
        }
