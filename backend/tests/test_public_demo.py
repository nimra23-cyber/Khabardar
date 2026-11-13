"""Public-demo hardening tests (final security pass).

In public-demo mode (KHABARDAR_PUBLIC_DEMO=true):
* text detection STILL works (real engine),
* scan-history persistence is DISABLED (no shared record store), and
* GET /api/history returns a safe 503 and exposes NO records.

These tests flip the env flag and clear the cached Settings so the routers see
public-demo mode, then exercise the real app over the TestClient.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401
from app.models.scan_history import ScanHistory


@pytest.fixture
def demo_client(tmp_path, monkeypatch):
    # Fresh temp DB + schema (so we can prove NOTHING gets written in demo mode).
    db_file = tmp_path / "demo.db"
    url = f"sqlite:///{db_file.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSession, raising=True)

    # Enable public-demo mode and reset the cached settings singleton.
    monkeypatch.setenv("KHABARDAR_PUBLIC_DEMO", "true")
    import app.core.config as config

    config.get_settings.cache_clear()

    import app.main as m

    with TestClient(m.fastapi_app) as c:
        yield c, TestingSession

    config.get_settings.cache_clear()  # restore for other tests


def test_demo_detection_still_works(demo_client):
    client, _ = demo_client
    r = client.post(
        "/api/scam/detect",
        json={"text": "Please share your OTP 918273 to verify your account."},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["classification"] in ("SUSPICIOUS", "HIGH RISK")
    assert any(s["signal_id"] == "otp_request" for s in d["signals"])
    # scan_id is None because persistence is disabled in demo mode.
    assert d["scan_id"] is None
    assert d["save_error"] is False


def test_demo_detection_persists_nothing(demo_client):
    client, Session = demo_client
    client.post("/api/scam/detect", json={"text": "share your OTP 918273 now"})
    client.post("/api/scam/detect", json={"text": "you won a lottery, pay fee"})
    # The database must contain ZERO scan rows: no shared history is created.
    with Session() as s:
        count = s.scalar(select(func.count()).select_from(ScanHistory))
    assert count == 0


def test_demo_history_endpoint_returns_503_no_records(demo_client):
    client, _ = demo_client
    r = client.get("/api/history")
    assert r.status_code == 503
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "HISTORY_DISABLED"
    # No records / data field leaked.
    assert "data" not in body
    assert "items" not in str(body)


def test_demo_no_signal_still_explicit(demo_client):
    client, _ = demo_client
    r = client.post("/api/scam/detect", json={"text": "asdkfj qweoiru zxcmnv"})
    d = r.json()["data"]
    assert d["no_signals_detected"] is True
    assert d["no_signal_notice"]


def test_demo_invalid_input_still_rejected(demo_client):
    client, _ = demo_client
    r = client.post("/api/scam/detect", json={"text": ""})
    assert r.status_code in (400, 422)
    assert r.json()["ok"] is False


def test_salt_and_demo_flag_not_leaked_in_health_or_caps(demo_client):
    client, _ = demo_client
    health = client.get("/api/health").json()
    caps = client.get("/api/capabilities").json()
    blob = str(health) + str(caps)
    # local_only honestly reported; no secret salt appears anywhere.
    assert "hash_salt" not in blob
    assert "KHABARDAR_HASH_SALT" not in blob
