"""Dashboard stats tests (Phase 6): real aggregation from persisted scans,
honest zero/empty states, user-independent totals."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401
from app.repositories.scan_history import ScanHistoryRepository
from app.services.dashboard import compute_stats


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    with Session() as s:
        yield s


def test_empty_stats_are_zero(session):
    stats = compute_stats(session, public_demo=True)
    assert stats["total_scans"] == 0
    assert stats["detected_scams"] == 0
    assert stats["risk_distribution"] == {"SAFE": 0, "SUSPICIOUS": 0, "HIGH RISK": 0}
    assert stats["category_breakdown"] == {}
    assert stats["empty"] is True


def test_stats_reflect_persisted_scans(session):
    repo = ScanHistoryRepository(session)
    # Need a user row for FK.
    from app.models.user import User

    u = User(username="local")
    session.add(u)
    session.commit()
    repo.create_scan(user_id=u.id, scan_type="text", raw_content="a",
                     risk_score=10, classification="SAFE", category=None)
    repo.create_scan(user_id=u.id, scan_type="text", raw_content="b",
                     risk_score=55, classification="SUSPICIOUS", category="account_takeover")
    repo.create_scan(user_id=u.id, scan_type="text", raw_content="c",
                     risk_score=80, classification="HIGH RISK", category="otp_theft")

    stats = compute_stats(session, public_demo=False)
    assert stats["total_scans"] == 3
    assert stats["detected_scams"] == 2  # SUSPICIOUS + HIGH RISK
    assert stats["risk_distribution"]["SAFE"] == 1
    assert stats["risk_distribution"]["SUSPICIOUS"] == 1
    assert stats["risk_distribution"]["HIGH RISK"] == 1
    assert stats["category_breakdown"]["otp_theft"] == 1
    assert stats["empty"] is False
    assert len(stats["trend_30d"]) >= 1


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "dash.db"
    url = f"sqlite:///{db_file.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSession, raising=True)
    with TestClient(m_app()) as c:
        yield c


def m_app():
    import app.main as m
    return m.fastapi_app


def test_api_dashboard_stats_empty(client):
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["total_scans"] == 0
    assert d["empty"] is True
    assert d["environment"] == "prototype"
