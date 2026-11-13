"""Report generation tests (Phase 6)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as m
from app.services.reports import build_report


def test_build_report_structure():
    result = {
        "risk_score": 71,
        "classification": "HIGH RISK",
        "category": "otp_theft",
        "signals": [{"name": "OTP request", "evidence": ["share your OTP"]}],
        "explanation_en": "Strong indicators.",
        "explanation_ur": "مضبوط آثار۔",
        "ruleset_version": "rules-2.6.0",
    }
    built = build_report(result)
    assert built["report"]["classification"] == "HIGH RISK"
    assert built["report"]["recommendations"]
    assert "# KHABARDAR Scam Analysis Report" in built["markdown"]
    assert "share your OTP" in built["markdown"]
    assert built["filename"].endswith(".md")


def test_build_report_no_signals():
    built = build_report({"risk_score": 0, "classification": "SAFE", "signals": []})
    assert "No contributing signals" in built["markdown"]


@pytest.fixture
def client():
    with TestClient(m.fastapi_app) as c:
        yield c


def test_api_generate_report(client):
    r = client.post(
        "/api/reports/generate",
        json={
            "risk_score": 55,
            "classification": "SUSPICIOUS",
            "category": "account_takeover",
            "signals": [{"name": "Urgency", "evidence": ["immediately"]}],
            "explanation_en": "Caution.",
            "explanation_ur": "احتیاط۔",
            "ruleset_version": "rules-2.6.0",
        },
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["report"]["classification"] == "SUSPICIOUS"
    assert "immediately" in d["markdown"]
    assert d["filename"]


def test_api_generate_report_validates_score(client):
    r = client.post(
        "/api/reports/generate",
        json={"risk_score": 999, "classification": "SAFE"},
    )
    assert r.status_code in (400, 422)
    assert r.json()["ok"] is False
