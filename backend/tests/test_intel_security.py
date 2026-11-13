"""IOC extraction security/validation tests (audit): per-type validation,
dedup, masking, no-raw-leak, adversarial input, IPv6."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as m
from app.services.intel import extract_iocs


def _norms(text, t):
    return [i.normalized_value for i in extract_iocs(text) if i.ioc_type == t]


# --- per-type extraction + validation --------------------------------------


def test_email_extracted_and_lowercased():
    assert _norms("Contact ME@Example.COM now", "email") == ["me@example.com"]


def test_phone_normalized_digits():
    assert _norms("call 0300-123 4567", "phone") == ["03001234567"]


def test_url_and_domain():
    assert _norms("go http://Evil.XYZ/Login", "url") == ["http://evil.xyz/Login"]
    # Bare domain
    assert "evil.top" in _norms("visit evil.top today", "domain")


def test_ipv4_valid_only():
    assert _norms("srv 203.0.113.9 ok", "ip") == ["203.0.113.9"]
    # Out-of-range octets are not accepted.
    assert _norms("bogus 999.999.999.999", "ip") == []


def test_ipv6_extracted():
    ips = _norms("server 2001:db8::1 responds", "ip")
    assert any(":" in x for x in ips)


def test_crypto_wallets():
    eth = _norms("pay 0x52908400098527886E0F7030069857D2E4169EE7", "wallet")
    assert eth
    btc = _norms("btc 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "wallet")
    assert btc


def test_bank_iban_only_not_arbitrary_digits():
    # IBAN-like reference is a bank IOC.
    assert _norms("acct PK36SCBL0000001123456702 pay", "bank")
    # A bare long number is NOT treated as a bank/payment reference.
    assert _norms("my lucky number is 1234567890123456789", "bank") == []


def test_dedup_identical_values():
    emails = _norms("a@b.com and A@B.COM", "email")
    assert emails == ["a@b.com"]


def test_empty_and_benign_no_iocs():
    assert extract_iocs("") == []
    assert extract_iocs("just a friendly hello message") == []


def test_adversarial_input_does_not_crash():
    for bad in ["@@@", "http://", "...", ":::::", "0x", "\x00\x01 2001:::", "a" * 5000]:
        extract_iocs(bad)  # must not raise


# --- API masking + no raw leak ---------------------------------------------


@pytest.fixture
def client():
    with TestClient(m.fastapi_app) as c:
        yield c


def test_api_masks_phone_email_wallet_bank_no_raw_leak(client):
    raw_phone = "03001234567"
    raw_email = "victim@example.com"
    raw_eth = "0x52908400098527886E0F7030069857D2E4169EE7"
    raw_iban = "PK36SCBL0000001123456702"
    text = f"call {raw_phone}, email {raw_email}, pay {raw_eth} or {raw_iban}"
    r = client.post("/api/iocs/extract", json={"text": text})
    assert r.status_code == 200
    blob = str(r.json())
    # None of the raw sensitive values appear anywhere in the response.
    assert raw_phone not in blob
    assert raw_email not in blob
    assert raw_eth not in blob
    assert raw_iban not in blob


def test_api_integrations_unavailable(client):
    r = client.post("/api/iocs/extract", json={"text": "visit evil.xyz"})
    d = r.json()["data"]
    assert all(v == "unavailable" for v in d["integration_states"].values())
    # No claim of maliciousness in the note.
    assert "malicious" not in d["note"].lower() or "no claim" in d["note"].lower()


def test_api_empty_rejected(client):
    r = client.post("/api/iocs/extract", json={"text": ""})
    assert r.status_code in (400, 422)
