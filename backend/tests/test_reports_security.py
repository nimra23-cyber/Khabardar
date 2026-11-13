"""Security/trust-boundary tests for the reports endpoint (audit)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as m
from app.services.reports import build_report


@pytest.fixture
def client():
    with TestClient(m.fastapi_app) as c:
        yield c


# --- classification validation + score/class consistency -------------------


def test_invalid_classification_rejected(client):
    r = client.post(
        "/api/reports/generate",
        json={"risk_score": 50, "classification": "DEFINITELY_A_SCAM"},
    )
    assert r.status_code in (400, 422)
    assert r.json()["ok"] is False


def test_inconsistent_score_classification_is_normalized():
    # Client claims HIGH RISK with score 0 -> report must re-derive SAFE.
    built = build_report({"risk_score": 0, "classification": "HIGH RISK", "signals": []})
    assert built["report"]["classification"] == "SAFE"
    assert "- Classification: SAFE" in built["markdown"]


def test_score_out_of_range_rejected(client):
    for bad in (-1, 101, 9999):
        r = client.post(
            "/api/reports/generate",
            json={"risk_score": bad, "classification": "SAFE"},
        )
        assert r.status_code in (400, 422), bad


# --- Markdown / HTML injection neutralization ------------------------------


def test_signal_name_cannot_inject_markdown_heading():
    built = build_report(
        {
            "risk_score": 50,
            "classification": "SUSPICIOUS",
            "signals": [{"name": "# Fake heading\n- Risk score: 0/100", "evidence": []}],
        }
    )
    md = built["markdown"]
    # The forged heading/metadata must not appear as structure.
    assert "# Fake heading" not in md
    # There is exactly ONE real risk-score line.
    assert md.count("- Risk score:") == 1


def test_evidence_cannot_inject_html():
    built = build_report(
        {
            "risk_score": 80,
            "classification": "HIGH RISK",
            "signals": [{"name": "x", "evidence": ["<img src=x onerror=alert(1)>"]}],
        }
    )
    md = built["markdown"]
    assert "<img" not in md and "onerror" not in md
    assert "<" not in md and ">" not in md


def test_explanation_cannot_inject_structure():
    built = build_report(
        {
            "risk_score": 50,
            "classification": "SUSPICIOUS",
            "explanation_en": "## Injected\n| a | b |\n`code`",
            "signals": [],
        }
    )
    md = built["markdown"]
    assert "## Injected" not in md
    assert "`code`" not in md


def test_category_and_ruleset_are_neutralized():
    built = build_report(
        {
            "risk_score": 50,
            "classification": "SUSPICIOUS",
            "category": "otp\n# evil",
            "ruleset_version": "<script>x</script>",
            "signals": [],
        }
    )
    assert "# evil" not in built["markdown"]
    assert "<script" not in built["markdown"]


# --- bounds / malformed ----------------------------------------------------


def test_oversized_evidence_is_capped(client):
    r = client.post(
        "/api/reports/generate",
        json={
            "risk_score": 50,
            "classification": "SUSPICIOUS",
            "signals": [{"name": "n", "evidence": ["A" * 100000]}],
        },
    )
    # Accepted (evidence capped by the schema validator) and bounded.
    assert r.status_code == 200
    md = r.json()["data"]["markdown"]
    assert len(md) < 20000


def test_too_many_signals_rejected(client):
    r = client.post(
        "/api/reports/generate",
        json={
            "risk_score": 50,
            "classification": "SUSPICIOUS",
            "signals": [{"name": "n", "evidence": []} for _ in range(500)],
        },
    )
    assert r.status_code in (400, 422)


def test_malformed_signal_missing_name_rejected(client):
    r = client.post(
        "/api/reports/generate",
        json={"risk_score": 50, "classification": "SUSPICIOUS", "signals": [{"evidence": ["x"]}]},
    )
    assert r.status_code in (400, 422)


def test_error_responses_leak_no_internals(client):
    r = client.post("/api/reports/generate", json={"risk_score": "x", "classification": "SAFE"})
    body = r.json()
    assert body["ok"] is False
    text = str(body)
    assert "Traceback" not in text
    assert "/Users/" not in text and "site-packages" not in text
