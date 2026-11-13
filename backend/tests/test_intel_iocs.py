"""IOC extraction + endpoint tests (Phase 5). Local, keyless, no network."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as m
from app.services.intel import extract_iocs
from app.services.intel.normalize import normalize_ioc


def _types(text):
    return {i.ioc_type for i in extract_iocs(text)}


def test_extract_url_email_ip_phone():
    text = (
        "Visit http://evil.example.xyz/login, email scam@fraud.com, "
        "server 203.0.113.9, call 0300-1234567"
    )
    ids = _types(text)
    assert {"url", "email", "ip", "phone"}.issubset(ids)


def test_extract_crypto_and_bank():
    text = "Send to 0x52908400098527886E0F7030069857D2E4169EE7 or PK36SCBL0000001123456702"
    ids = _types(text)
    assert "wallet" in ids
    assert "bank" in ids


def test_empty_text_zero_iocs_no_error():
    assert extract_iocs("") == []
    assert extract_iocs("just a normal sentence") == []


def test_normalization_is_idempotent():
    assert normalize_ioc("email", "  Foo@BAR.com ") == "foo@bar.com"
    assert normalize_ioc("email", "foo@bar.com") == "foo@bar.com"
    assert normalize_ioc("phone", "0300-123 4567") == "03001234567"
    assert normalize_ioc("url", "https://x.com/") == "https://x.com"


def test_dedup_identical_type_value():
    text = "mail me at a@b.com and again a@b.com"
    emails = [i for i in extract_iocs(text) if i.ioc_type == "email"]
    assert len(emails) == 1


@pytest.fixture
def client():
    with TestClient(m.fastapi_app) as c:
        yield c


def test_api_extract_masks_sensitive_iocs(client):
    r = client.post(
        "/api/iocs/extract",
        json={"text": "call 0300-1234567 or email victim@example.com"},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["count"] >= 2
    # Masked: the full raw phone/email must not appear verbatim.
    blob = str(d["iocs"])
    assert "03001234567" not in blob
    assert "victim@example.com" not in blob
    assert all(v == "unavailable" for v in d["integration_states"].values())


def test_api_extract_url_not_masked_but_present(client):
    r = client.post("/api/iocs/extract", json={"text": "see http://evil.xyz/login"})
    d = r.json()["data"]
    assert any(i["ioc_type"] == "url" for i in d["iocs"])


def test_api_extract_empty_rejected(client):
    r = client.post("/api/iocs/extract", json={"text": ""})
    assert r.status_code in (400, 422)
    assert r.json()["ok"] is False
