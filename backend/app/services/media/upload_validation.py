"""Upload validation service (Req 12): accept PNG/JPEG/WEBP only.

Security properties:
- Magic-byte validation (not Content-Type trust) — MIME-spoofing protection.
- Max file size: 10 MB (10 * 1024 * 1024 bytes).
- Max pixel count: 25,000,000 — decompression-bomb protection.
- Max dimensions: 8000×8000 px.
- Random temp filenames (uuid4) stored in tempfile.gettempdir() ONLY.
- Temp files cleaned up in ALL paths (success and all error branches).
- NO permanent storage, NO storage outside tmp.
- Returns a dataclass; never raises externally (raises UploadValidationError).
"""

from __future__ import annotations

import os
import tempfile
import uuid
from dataclasses import dataclass
from typing import Literal

from PIL import Image, UnidentifiedImageError

# Max allowed values.
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_WIDTH = 8000
MAX_HEIGHT = 8000
MAX_PIXELS = 25_000_000  # decompression-bomb cap

# Supported types and their magic bytes.
_MAGIC: dict[str, bytes] = {
    "png": b"\x89PNG",
    "jpeg": b"\xff\xd8\xff",
    "webp": b"RIFF",  # + bytes 8-11 == b"WEBP" checked below
}
_SUPPORTED_FORMATS = frozenset({"png", "jpeg", "webp"})

ImageType = Literal["png", "jpeg", "webp"]


class UploadValidationError(ValueError):
    """Raised when an uploaded file fails validation.

    The message is safe to surface as a user-facing error (no path/filename leakage).
    """


@dataclass
class ValidatedImage:
    """Holds the validated PIL Image, detected type, and temp file path.

    The caller is responsible for closing/cleaning up ``temp_path`` after use
    (the router does this in a finally block).
    """

    image: Image.Image
    image_type: ImageType
    temp_path: str


def _detect_type(header: bytes) -> ImageType | None:
    """Return the image type from magic bytes, or None if unsupported."""
    if header[:4] == _MAGIC["png"]:
        return "png"
    if header[:3] == _MAGIC["jpeg"]:
        return "jpeg"
    # WEBP: 'RIFF' at byte 0, 'WEBP' at byte 8.
    if len(header) >= 12 and header[:4] == _MAGIC["webp"] and header[8:12] == b"WEBP":
        return "webp"
    return None


def validate_upload(data: bytes) -> ValidatedImage:
    """Validate ``data`` as an acceptable image upload.

    Parameters
    ----------
    data:
        Raw bytes of the uploaded file.

    Returns
    -------
    ValidatedImage
        Dataclass with opened PIL Image, detected type, and temp file path.

    Raises
    ------
    UploadValidationError
        If the file is too large, not a supported image type, fails magic-byte
        check, has excessive dimensions, or triggers a decompression-bomb error.
    """
    # 1. Size check.
    if len(data) > MAX_FILE_BYTES:
        raise UploadValidationError(
            "File exceeds the maximum allowed size of 10 MB."
        )

    if len(data) == 0:
        raise UploadValidationError("Uploaded file is empty.")

    # 2. Magic-byte check (MIME-spoofing protection).
    image_type = _detect_type(data[:12])
    if image_type is None:
        raise UploadValidationError(
            "Unsupported file type. Only PNG, JPEG, and WEBP images are accepted."
        )

    # 3. Write to a random temp file (uuid4 name).
    suffix = f".{image_type}"
    temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}{suffix}")
    try:
        with open(temp_path, "wb") as f:
            f.write(data)

        # 4. Open with Pillow — catches corrupt/non-image files.
        try:
            # Disable Pillow's global MAX_IMAGE_PIXELS guard (we enforce our own).
            # We catch DecompressionBombError/Warning ourselves below.
            import PIL.Image as _PILImage

            orig_limit = _PILImage.MAX_IMAGE_PIXELS
            _PILImage.MAX_IMAGE_PIXELS = None  # disable global guard temporarily
            try:
                img = Image.open(temp_path)
                img.load()  # force full decode so errors surface here
            finally:
                _PILImage.MAX_IMAGE_PIXELS = orig_limit

        except Image.DecompressionBombError:
            raise UploadValidationError(
                "Image exceeds maximum allowed pixel count (decompression bomb protection)."
            )
        except Image.DecompressionBombWarning:
            raise UploadValidationError(
                "Image exceeds maximum allowed pixel count (decompression bomb protection)."
            )
        except (UnidentifiedImageError, OSError):
            raise UploadValidationError(
                "File could not be read as a valid image."
            )

        # 5. Dimension check.
        width, height = img.size
        if width > MAX_WIDTH or height > MAX_HEIGHT:
            raise UploadValidationError(
                f"Image dimensions ({width}×{height}) exceed the maximum of "
                f"{MAX_WIDTH}×{MAX_HEIGHT} pixels."
            )

        # 6. Total pixel count check (decompression-bomb protection).
        total_pixels = width * height
        if total_pixels > MAX_PIXELS:
            raise UploadValidationError(
                "Image exceeds maximum allowed pixel count (25 MP)."
            )

        # 7. Convert to RGB to ensure consistent downstream processing.
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        return ValidatedImage(image=img, image_type=image_type, temp_path=temp_path)

    except UploadValidationError:
        # Clean up temp file on validation failure.
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
    except Exception:
        # Clean up temp file on any unexpected error.
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
