"""QR code decoding service (Req 12): extract decoded string values from images.

Security properties:
- Decoded URL values are NEVER auto-opened or fetched.
- Graceful degradation: returns available=False if neither pyzbar nor OpenCV available.
- Returns ALL QR codes found in the image (may be multiple).
- Decoded values are never logged (may contain sensitive data).
"""

from __future__ import annotations

import logging
from typing import TypedDict

from PIL import Image

_logger = logging.getLogger("khabardar.media.qr")


class QRResult(TypedDict):
    available: bool
    values: list[str]
    error: str | None


def _try_pyzbar(image: Image.Image) -> list[str] | None:
    """Try to decode QR codes using pyzbar. Returns None if pyzbar unavailable."""
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode  # type: ignore

        objects = pyzbar_decode(image)
        return [
            obj.data.decode("utf-8", errors="replace")
            for obj in objects
            if obj.type in ("QRCODE", "QR CODE")
        ]
    except ImportError:
        return None
    except Exception as exc:
        _logger.warning("pyzbar_error type=%s", type(exc).__name__)
        return None


def _try_opencv(image: Image.Image) -> list[str] | None:
    """Try to decode QR codes using OpenCV. Returns None if cv2 unavailable."""
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        # Convert PIL image to BGR numpy array for OpenCV.
        rgb = image.convert("RGB")
        arr = np.array(rgb)
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        detector = cv2.QRCodeDetector()
        # detectAndDecodeMulti handles multiple QR codes in one image.
        retval, decoded_infos, _, _ = detector.detectAndDecodeMulti(bgr)
        if not retval:
            return []
        return [v for v in decoded_infos if v]
    except ImportError:
        return None
    except Exception as exc:
        _logger.warning("opencv_qr_error type=%s", type(exc).__name__)
        return None


def decode_qr(image: Image.Image) -> QRResult:
    """Decode all QR codes in a PIL Image.

    Tries pyzbar first; falls back to OpenCV; reports unavailable if neither works.

    Returns
    -------
    QRResult
        ``available``: whether at least one decoder backend is installed.
        ``values``: list of decoded string values (may be empty).
        ``error``: error string if something went wrong.
    """
    # Try pyzbar first (preferred: faster, no display dependency).
    result = _try_pyzbar(image)
    if result is not None:
        # pyzbar is available; return its results.
        return {
            "available": True,
            "values": result,
            "error": None,
        }

    # Try OpenCV fallback.
    result = _try_opencv(image)
    if result is not None:
        return {
            "available": True,
            "values": result,
            "error": None,
        }

    # Neither backend available.
    return {
        "available": False,
        "values": [],
        "error": "QR decoder not available",
    }
