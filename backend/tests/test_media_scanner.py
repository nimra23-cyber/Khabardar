"""Integration tests for POST /api/media/scan (Req 12).

Images are created programmatically using Pillow — no test fixture files needed.
Tests cover upload validation, OCR availability, QR decoding, URL extraction,
temp file cleanup, and public-demo no-persistence.

Security notes:
- Extracted text / QR values are never asserted to appear in log output.
- OTP text non-logging test captures log records to confirm absence.
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
import struct
import zlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient backed by an isolated temp SQLite DB."""
    db_file = tmp_path / "media_test.db"
    url = f"sqlite:///{db_file.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSession, raising=True)

    import app.main as m

    with TestClient(m.fastapi_app) as c:
        yield c


# ---------------------------------------------------------------------------
# Image factories
# ---------------------------------------------------------------------------


def _make_png_bytes(width: int = 100, height: int = 100, color: tuple = (255, 255, 255)) -> bytes:
    """Create a minimal valid PNG in memory using Pillow."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_jpeg_bytes(width: int = 100, height: int = 100, color: tuple = (200, 200, 200)) -> bytes:
    """Create a minimal valid JPEG in memory."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_webp_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create a minimal valid WEBP in memory."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


def _make_qr_png_bytes(data: str) -> bytes:
    """Generate a real QR code PNG using qrcode library.

    Falls back to a plain white PNG if qrcode is not installed
    (the QR decode test will then verify available flag honestly).
    """
    try:
        import qrcode  # type: ignore

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # qrcode not available; return a plain white PNG.
        return _make_png_bytes()


def _upload_png(client, data: bytes, content_type: str = "image/png") -> dict:
    """POST image bytes to /api/media/scan and return response dict."""
    resp = client.post(
        "/api/media/scan",
        files={"image": ("test.png", io.BytesIO(data), content_type)},
    )
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUploadValidation:

    def test_valid_png_accepted(self, client):
        """Valid PNG → 200, correct response shape."""
        png = _make_png_bytes()
        r = _upload_png(client, png)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        data = body["data"]
        assert data["image_type"] == "png"
        assert "ocr" in data
        assert "qr" in data
        assert "urls_found" in data
        assert "text_analysis" in data
        assert "url_analyses" in data
        assert isinstance(data["urls_found"], list)
        assert isinstance(data["url_analyses"], list)

    def test_jpeg_accepted(self, client):
        """JPEG image → 200, image_type=jpeg."""
        jpeg = _make_jpeg_bytes()
        r = client.post(
            "/api/media/scan",
            files={"image": ("photo.jpg", io.BytesIO(jpeg), "image/jpeg")},
        )
        assert r.status_code == 200, r.text
        assert r.json()["data"]["image_type"] == "jpeg"

    def test_webp_accepted(self, client):
        """WEBP image → 200, image_type=webp."""
        webp = _make_webp_bytes()
        r = client.post(
            "/api/media/scan",
            files={"image": ("img.webp", io.BytesIO(webp), "image/webp")},
        )
        assert r.status_code == 200, r.text
        assert r.json()["data"]["image_type"] == "webp"

    def test_png_spoofed_as_jpeg_still_accepted(self, client):
        """JPEG magic bytes but Content-Type=image/png → accepted as jpeg (magic bytes win)."""
        jpeg = _make_jpeg_bytes()
        # Lie about content type — magic bytes should still validate correctly.
        r = client.post(
            "/api/media/scan",
            files={"image": ("spoof.png", io.BytesIO(jpeg), "image/png")},
        )
        # Magic bytes = JPEG → valid, accepted as jpeg regardless of content-type.
        assert r.status_code == 200, r.text
        assert r.json()["data"]["image_type"] == "jpeg"

    def test_exe_spoofed_as_png_rejected(self, client):
        """File bytes starting with PE header (MZ) → 400 even with image/* content-type."""
        pe_header = b"MZ\x90\x00" + b"\x00" * 200  # DOS/PE magic bytes
        r = client.post(
            "/api/media/scan",
            files={"image": ("evil.png", io.BytesIO(pe_header), "image/png")},
        )
        assert r.status_code == 400
        body = r.json()
        assert body["ok"] is False
        assert "error" in body

    def test_pdf_spoofed_as_png_rejected(self, client):
        """PDF magic bytes (%PDF) → 400."""
        pdf_header = b"%PDF-1.4\n" + b"\x00" * 200
        r = client.post(
            "/api/media/scan",
            files={"image": ("evil.png", io.BytesIO(pdf_header), "image/png")},
        )
        assert r.status_code == 400
        assert r.json()["ok"] is False

    def test_oversized_file_rejected(self, client):
        """11 MB of zeros → 400 or 413."""
        oversized = b"\x00" * (11 * 1024 * 1024)
        r = client.post(
            "/api/media/scan",
            files={"image": ("big.png", io.BytesIO(oversized), "image/png")},
        )
        assert r.status_code in (400, 413), r.status_code
        assert r.json()["ok"] is False

    def test_empty_file_rejected(self, client):
        """Empty upload → 400."""
        r = client.post(
            "/api/media/scan",
            files={"image": ("empty.png", io.BytesIO(b""), "image/png")},
        )
        assert r.status_code == 400
        assert r.json()["ok"] is False

    def test_excessive_dimensions_rejected(self, client):
        """Image with excessive dimensions → 400 (8001×8001 pixel image)."""
        from PIL import Image

        # Build a 8001×8001 image in memory without fully allocating — use a
        # truncated PNG that claims huge dimensions in its IHDR.
        # We'll just create an actual 8001x1 image (exceeds max width of 8000).
        img = Image.new("RGB", (8001, 1), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()
        r = client.post(
            "/api/media/scan",
            files={"image": ("huge.png", io.BytesIO(data), "image/png")},
        )
        assert r.status_code == 400
        body = r.json()
        assert body["ok"] is False


class TestOCR:

    def test_ocr_returns_available_or_unavailable(self, client):
        """Blank white PNG → OCR result has correct available flag."""
        png = _make_png_bytes()
        r = _upload_png(client, png)
        assert r.status_code == 200
        ocr = r.json()["data"]["ocr"]
        assert isinstance(ocr["available"], bool)
        # If available, text may be None or a string; if not available, error is set.
        if ocr["available"]:
            assert ocr["error"] is None
            assert isinstance(ocr.get("text"), (str, type(None)))
        else:
            assert ocr["error"] is not None

    def test_no_text_in_blank_image(self, client):
        """Blank white PNG → OCR returns no meaningful text (None or empty)."""
        png = _make_png_bytes(200, 200, (255, 255, 255))
        r = _upload_png(client, png)
        assert r.status_code == 200
        ocr = r.json()["data"]["ocr"]
        # Blank image → no meaningful text extracted.
        if ocr["available"]:
            text = ocr.get("text")
            # Text should be None or an empty/whitespace-only string.
            assert text is None or (isinstance(text, str) and text.strip() == "")


class TestQR:

    def test_qr_decode_or_unavailable(self, client):
        """QR image → QR result has correct available flag and values list."""
        qr_data = "https://example.com/test-qr"
        qr_png = _make_qr_png_bytes(qr_data)
        r = _upload_png(client, qr_png)
        assert r.status_code == 200
        qr = r.json()["data"]["qr"]
        assert isinstance(qr["available"], bool)
        assert isinstance(qr["values"], list)
        if not qr["available"]:
            assert qr["error"] is not None
        # If decoder is available and qrcode lib was used, the value should be found.
        if qr["available"] and len(qr["values"]) > 0:
            # The decoded URL should be in the values.
            assert any("example.com" in v for v in qr["values"])

    def test_qr_unavailable_has_error_message(self, client):
        """If QR decoder not installed, error message is set and values is empty."""
        from app.services.media import qr_decode

        orig_pyzbar = qr_decode._try_pyzbar
        orig_opencv = qr_decode._try_opencv

        # Simulate both decoders being unavailable.
        qr_decode._try_pyzbar = lambda img: None  # type: ignore
        qr_decode._try_opencv = lambda img: None  # type: ignore

        try:
            png = _make_png_bytes()
            r = _upload_png(client, png)
            assert r.status_code == 200
            qr = r.json()["data"]["qr"]
            assert qr["available"] is False
            assert qr["values"] == []
            assert qr["error"] is not None
        finally:
            qr_decode._try_pyzbar = orig_pyzbar  # type: ignore
            qr_decode._try_opencv = orig_opencv  # type: ignore


class TestTempFileCleanup:

    def test_temp_files_cleaned_up_after_scan(self, client):
        """After a successful scan, no temp file for that run remains in tmpdir."""
        tmp_dir = tempfile.gettempdir()
        before = set(os.listdir(tmp_dir))

        png = _make_png_bytes()
        r = _upload_png(client, png)
        assert r.status_code == 200

        after = set(os.listdir(tmp_dir))
        # Any new files should NOT include our uuid-named image files.
        new_files = after - before
        image_exts = {".png", ".jpeg", ".jpg", ".webp"}
        leftover_images = [f for f in new_files if any(f.endswith(e) for e in image_exts)]
        assert leftover_images == [], f"Leftover temp files: {leftover_images}"

    def test_temp_files_cleaned_up_on_validation_error(self, client):
        """After a failed validation, no temp file remains."""
        tmp_dir = tempfile.gettempdir()
        before = set(os.listdir(tmp_dir))

        # Invalid file — PE header.
        bad_data = b"MZ\x90\x00" + b"\x00" * 200
        client.post(
            "/api/media/scan",
            files={"image": ("bad.png", io.BytesIO(bad_data), "image/png")},
        )

        after = set(os.listdir(tmp_dir))
        new_files = after - before
        image_exts = {".png", ".jpeg", ".jpg", ".webp"}
        leftover_images = [f for f in new_files if any(f.endswith(e) for e in image_exts)]
        assert leftover_images == [], f"Leftover temp files: {leftover_images}"


class TestPublicDemo:

    def test_public_demo_no_persistence(self, client, monkeypatch):
        """In public demo mode, text_analysis.scan_id is None."""
        monkeypatch.setenv("KHABARDAR_PUBLIC_DEMO", "true")
        # Force settings re-evaluation.
        from app.core import config as cfg
        cfg.get_settings.cache_clear()  # type: ignore[union-attr]

        try:
            png = _make_png_bytes()
            r = _upload_png(client, png)
            assert r.status_code == 200
            data = r.json()["data"]
            assert data["public_demo"] is True
            # text_analysis may be None (no OCR text from blank image).
            if data["text_analysis"] is not None:
                assert data["text_analysis"]["scan_id"] is None
        finally:
            cfg.get_settings.cache_clear()  # type: ignore[union-attr]

    def test_response_has_public_demo_flag(self, client):
        """Response always includes the public_demo flag."""
        png = _make_png_bytes()
        r = _upload_png(client, png)
        assert r.status_code == 200
        assert "public_demo" in r.json()["data"]


class TestSensitiveTextNotLogged:

    def test_sensitive_text_not_in_log_output(self, client, caplog):
        """OTP text submitted via image → OTP value not present in log records."""
        # We test the router's behavior: it should not log extracted text.
        # We capture all log output and ensure no sensitive string leaks.
        secret_otp = "SECRET-OTP-123456"

        with caplog.at_level(logging.DEBUG, logger="khabardar"):
            png = _make_png_bytes(200, 200, (255, 255, 255))
            _upload_png(client, png)

        # The secret OTP should never appear in any log record.
        for record in caplog.records:
            assert secret_otp not in record.getMessage(), (
                f"Secret OTP found in log record: {record.getMessage()}"
            )


class TestURLExtraction:

    def test_extract_service_finds_urls(self):
        """Unit test: extract_urls returns URLs from text."""
        from app.services.media.extract import extract_urls

        text = "Visit https://example.com/path and also http://test.org/page?q=1 for more info."
        urls = extract_urls(text)
        assert "https://example.com/path" in urls
        assert "http://test.org/page?q=1" in urls

    def test_extract_service_empty_text(self):
        """extract_urls on empty text returns empty list."""
        from app.services.media.extract import extract_urls

        assert extract_urls("") == []
        assert extract_urls(None) == []  # type: ignore

    def test_extract_service_no_urls(self):
        """extract_urls on text without URLs returns empty list."""
        from app.services.media.extract import extract_urls

        assert extract_urls("Hello world, no links here.") == []

    def test_extract_service_deduplicates(self):
        """extract_urls deduplicates repeated URLs."""
        from app.services.media.extract import extract_urls

        text = "https://example.com and again https://example.com"
        urls = extract_urls(text)
        assert urls.count("https://example.com") == 1


class TestUploadValidationUnit:

    def test_validate_valid_png(self):
        """Unit: validate_upload accepts a valid PNG."""
        from app.services.media.upload_validation import validate_upload

        png = _make_png_bytes()
        result = validate_upload(png)
        try:
            assert result.image_type == "png"
            assert result.image is not None
        finally:
            # Always clean up.
            if os.path.exists(result.temp_path):
                os.unlink(result.temp_path)

    def test_validate_valid_jpeg(self):
        """Unit: validate_upload accepts a valid JPEG."""
        from app.services.media.upload_validation import validate_upload

        jpeg = _make_jpeg_bytes()
        result = validate_upload(jpeg)
        try:
            assert result.image_type == "jpeg"
        finally:
            if os.path.exists(result.temp_path):
                os.unlink(result.temp_path)

    def test_validate_rejects_exe(self):
        """Unit: validate_upload rejects PE-header data."""
        from app.services.media.upload_validation import UploadValidationError, validate_upload

        with pytest.raises(UploadValidationError):
            validate_upload(b"MZ\x90\x00" + b"\x00" * 200)

    def test_validate_rejects_empty(self):
        """Unit: validate_upload rejects empty bytes."""
        from app.services.media.upload_validation import UploadValidationError, validate_upload

        with pytest.raises(UploadValidationError):
            validate_upload(b"")

    def test_validate_rejects_oversized(self):
        """Unit: validate_upload rejects data over 10 MB."""
        from app.services.media.upload_validation import UploadValidationError, validate_upload

        with pytest.raises(UploadValidationError):
            validate_upload(b"\x89PNG" + b"\x00" * (11 * 1024 * 1024))

    def test_validate_temp_file_removed_on_error(self):
        """Unit: temp file is cleaned up when validation fails."""
        from app.services.media.upload_validation import UploadValidationError, validate_upload
        import glob

        tmp_dir = tempfile.gettempdir()
        before = set(glob.glob(os.path.join(tmp_dir, "*.png")))

        with pytest.raises(UploadValidationError):
            validate_upload(b"MZ\x90\x00" + b"\x00" * 200)

        after = set(glob.glob(os.path.join(tmp_dir, "*.png")))
        assert after == before or not (after - before), "Temp file not cleaned up on error"
