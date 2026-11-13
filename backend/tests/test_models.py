"""Unit tests for the ORM models and schema (Task 2.1, Req 20).

Covers:
- All 11 models are registered and create on a fresh SQLite DB.
- The IOC (ioc_type, normalized_value) UNIQUE constraint is enforced.
- Models instantiate and round-trip with portable types (String/Text/Integer/
  Boolean/DateTime(tz)/JSON) and string UUID PKs.
- ScanHistory exposes a `masked_content` field and NO raw-content/secret
  column (the model-level half of the Req 21 "masked only" guarantee).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app import models
from app.models import (
    AuditLog,
    FamilyGroup,
    FamilyMember,
    HoneypotSession,
    Notification,
    ScamCampaign,
    ScamReport,
    ScanHistory,
    ThreatIndicator,
    URLAnalysis,
    User,
)

EXPECTED_TABLES = {
    "users",
    "scan_history",
    "scam_reports",
    "url_analysis",
    "threat_indicators",
    "scam_campaigns",
    "family_groups",
    "family_members",
    "notifications",
    "audit_logs",
    "honeypot_sessions",
}


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def test_all_eleven_tables_created(db):
    engine = db.get_bind()
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES.issubset(tables)
    assert len(EXPECTED_TABLES) == 11


def test_models_instantiate_and_round_trip(db):
    user = User(username="local")
    db.add(user)
    db.flush()  # assigns id

    assert isinstance(user.id, str)
    uuid.UUID(user.id)  # valid UUID string PK
    assert user.created_at is not None

    scan = ScanHistory(
        user_id=user.id,
        scan_type="text",
        masked_content="OTP is ****",
        risk_score=72,
        classification="HIGH RISK",
        category="phishing",
        signals=[{"name": "otp_request", "triggered": True}],
        explanation_en="en",
        explanation_ur="ur",
        confidence=0.8,
        origin="verified",
    )
    db.add(scan)
    db.flush()
    db.commit()

    fetched = db.get(ScanHistory, scan.id)
    assert fetched is not None
    assert fetched.user_id == user.id
    assert fetched.signals == [{"name": "otp_request", "triggered": True}]
    assert fetched.risk_score == 72
    assert fetched.origin == "verified"


def test_ioc_unique_constraint_enforced(db):
    db.add(ThreatIndicator(ioc_type="phone", normalized_value="+923001234567"))
    db.commit()

    # Same (type, value) must violate the UNIQUE constraint.
    db.add(ThreatIndicator(ioc_type="phone", normalized_value="+923001234567"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Same value but DIFFERENT type is allowed (distinct pair).
    db.add(ThreatIndicator(ioc_type="email", normalized_value="+923001234567"))
    db.commit()


def test_scan_history_stores_masked_content_only(db):
    # Model-level guarantee: the column is named masked_content, and there is
    # no raw/plaintext content column that could hold secrets.
    cols = {c.name for c in ScanHistory.__table__.columns}
    assert "masked_content" in cols
    for forbidden in ("content", "raw_content", "plaintext", "password", "otp", "token"):
        assert forbidden not in cols, f"ScanHistory must not expose a {forbidden!r} column"


def test_honeypot_origin_defaults_to_synthetic(db):
    hp = HoneypotSession(synthetic_conversation=[{"from": "scammer", "text": "hi"}])
    db.add(hp)
    db.commit()
    fetched = db.get(HoneypotSession, hp.id)
    # Req 14.5: honeypot records are always synthetic.
    assert fetched.origin == "synthetic"


def test_remaining_models_instantiate(db):
    user = User(username="u2")
    db.add(user)
    db.flush()
    campaign = ScamCampaign(name="c1", origin="synthetic")
    db.add(campaign)
    db.flush()
    scan = ScanHistory(user_id=user.id, scan_type="url")
    db.add(scan)
    db.flush()

    db.add_all([
        ScamReport(user_id=user.id, scan_id=scan.id, status="open"),
        URLAnalysis(scan_id=scan.id, domain="example.test", risk_score=10),
        FamilyGroup(owner_user_id=user.id),
        AuditLog(action="test_action", actor=user.id, detail={"k": "v"}),
    ])
    db.commit()

    group = db.query(FamilyGroup).first()
    db.add(FamilyMember(group_id=group.id, masked_contact="****7890", consent=False))
    db.add(Notification(group_id=group.id, user_id=user.id, type="alert"))
    db.commit()

    assert db.query(ScamReport).count() == 1
    assert db.query(URLAnalysis).count() == 1
    assert db.query(FamilyMember).count() == 1
    assert db.query(Notification).count() == 1
    assert db.query(AuditLog).count() == 1
    assert models.ScamCampaign is ScamCampaign
