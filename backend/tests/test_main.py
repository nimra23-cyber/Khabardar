"""API tests for the app skeleton (Task 1.1).

Verifies the root, health, and capabilities endpoints respond with the expected
envelope and that capabilities never leak a secret value.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_ok():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["service"] == "khabardar"
    assert body["data"]["tagline"] == "Think Before You Trust."


def test_health_ok():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["local_only"] is True


def test_health_alias_matches_canonical():
    assert client.get("/health").json() == client.get("/api/health").json()


def test_capabilities_no_secret_values():
    r = client.get("/api/capabilities")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    text = r.text
    # With no keys set in the test environment, all report unavailable.
    for group in body["data"].values():
        for state in group.values():
            assert state in {"configured", "unavailable"}
    # No obviously-secret-looking long token leaks into the response text.
    assert "API_KEY" not in text
