"""API integration tests for /api/scam/detect and /api/history (Task 2.13/6.5).

Uses a real FastAPI app + in-memory-backed temp SQLite schema so persistence
and user isolation are exercised against actual stored values.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401  (register models on Base.metadata)


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "api.db"
    url = f"sqlite:///{db_file.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    # Redirect the app's session factory to the temp DB.
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSession, raising=True)

    import app.main as m

    with TestClient(m.fastapi_app) as c:
        yield c


def _detect(client, text):
    return client.post("/api/scam/detect", json={"text": text})


def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_detect_otp_scam_high_or_suspicious(client):
    r = _detect(client, "Please share your OTP 918273 now to verify your account.")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["classification"] in ("SUSPICIOUS", "HIGH RISK")
    assert d["risk_score"] > 0
    assert any(s["signal_id"] == "otp_request" for s in d["signals"])
    assert d["explanation_en"] and d["explanation_ur"]


def test_detect_persists_masked_not_raw(client):
    _detect(client, "share your OTP 918273 immediately")
    h = client.get("/api/history").json()["data"]
    assert h["count"] >= 1
    for item in h["items"]:
        assert "918273" not in (item["masked_content"] or "")


def test_detect_benign_is_safe_no_signals(client):
    r = _detect(client, "Hi, are we meeting for lunch tomorrow?")
    d = r.json()["data"]
    assert d["classification"] == "SAFE"
    assert d["signals"] == []
    assert d["no_signals_detected"] is True
    assert d["no_signal_notice"]


def test_detect_no_signal_message(client):
    r = _detect(client, "asdkfj qweoiru zxcmnv")
    d = r.json()["data"]
    assert d["no_signals_detected"] is True


def test_detect_empty_rejected_with_envelope(client):
    r = _detect(client, "")
    assert r.status_code in (400, 422)
    body = r.json()
    assert body["ok"] is False
    assert "error" in body


def test_detect_too_long_rejected(client):
    r = _detect(client, "a" * 10001)
    assert r.status_code in (400, 422)
    assert r.json()["ok"] is False


def test_history_empty_state(client):
    r = client.get("/api/history")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["count"] == 0
    assert d["items"] == []


def test_urdu_scam_detected_via_api(client):
    r = _detect(client, "آپ کا اکاؤنٹ بند ہو جائے گا، فوراً تصدیق کریں۔")
    d = r.json()["data"]
    assert d["classification"] in ("SUSPICIOUS", "HIGH RISK")
    assert any(s["signal_id"] == "account_suspension" for s in d["signals"])
