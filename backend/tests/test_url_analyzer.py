"""URL analyzer tests (Phase 3): normalization, SSRF policy, heuristics, scoring,
and the /api/url/analyze endpoint. No network calls are made by these tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as m
from app.services.url import analyze_url
from app.services.url.address_policy import is_blocked_ip, host_is_blocked
from app.services.url.url_normalize import normalize_url


# --- normalization ---------------------------------------------------------


def test_normalize_rejects_non_http_scheme():
    assert normalize_url("ftp://example.com").valid is False
    assert normalize_url("javascript:alert(1)").valid is False


def test_normalize_rejects_empty_and_garbage():
    assert normalize_url("").valid is False
    assert normalize_url("not a url").valid is False


def test_normalize_accepts_http_https_and_lowercases_host():
    p = normalize_url("HTTPS://Example.COM/Path")
    assert p.valid and p.scheme == "https" and p.host == "example.com"


def test_normalize_detects_userinfo_and_ip():
    p = normalize_url("http://user:pass@127.0.0.1/")
    assert p.valid and p.had_userinfo and p.is_ip_literal


# --- SSRF address policy ---------------------------------------------------


@pytest.mark.parametrize(
    "ip",
    ["127.0.0.1", "10.0.0.5", "192.168.1.1", "172.16.0.1", "169.254.169.254", "::1"],
)
def test_blocked_ip_ranges(ip):
    assert is_blocked_ip(ip) is True


@pytest.mark.parametrize("ip", ["8.8.8.8", "1.1.1.1"])
def test_public_ip_not_blocked(ip):
    assert is_blocked_ip(ip) is False


def test_host_is_blocked_for_literal_private_ip():
    assert host_is_blocked("192.168.0.1") is True


# --- heuristics / scoring --------------------------------------------------


def test_legit_brand_domain_is_not_false_positive():
    r = analyze_url("https://jazzcash.com.pk/login")
    assert r["valid"] and r["classification"] == "SAFE"
    assert not any(i["id"] == "brand_in_subdomain" for i in r["indicators"])


def test_brand_in_subdomain_flagged():
    r = analyze_url("http://jazzcash.secure-login.xyz/verify")
    ids = {i["id"] for i in r["indicators"]}
    assert "brand_in_subdomain" in ids
    assert r["classification"] in ("SUSPICIOUS", "HIGH RISK")


def test_typosquat_flagged():
    r = analyze_url("https://jazzcach.com.pk")
    assert any(i["id"] == "typosquat" for i in r["indicators"])


def test_ip_url_and_ssrf_block():
    r = analyze_url("http://192.168.0.1/admin")
    assert r["blocked"] is True
    assert r["recommended_action"] == "do_not_visit"
    assert any(i["id"] == "ssrf_blocked" for i in r["indicators"])


def test_metadata_host_blocked_and_not_contacted():
    r = analyze_url("http://169.254.169.254/latest/meta-data")
    assert r["blocked"] is True
    assert r["redirect_chain"] == []  # no fetch performed


def test_shortener_detected():
    r = analyze_url("https://bit.ly/abc123")
    assert any(i["id"] == "shortener" for i in r["indicators"])


def test_score_is_bounded():
    r = analyze_url("http://user:pass@jazzcash.secure-login.xyz/verify")
    assert 0 <= r["risk_score"] <= 100


def test_integrations_reported_unavailable():
    r = analyze_url("https://example.com")
    assert set(r["integration_states"].values()) == {"unavailable"}


# --- API endpoint ----------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(m.fastapi_app) as c:
        yield c


def test_api_analyze_valid_url(client):
    r = client.post("/api/url/analyze", json={"url": "http://jazzcash.secure-login.xyz"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["domain"] == "jazzcash.secure-login.xyz"
    assert 0 <= d["risk_score"] <= 100
    assert d["integration_states"]["virustotal"] == "unavailable"


def test_api_analyze_invalid_url_rejected_no_network(client):
    r = client.post("/api/url/analyze", json={"url": "ftp://x"})
    assert r.status_code in (400, 422)
    assert r.json()["ok"] is False


def test_api_analyze_blocks_private_host(client):
    r = client.post("/api/url/analyze", json={"url": "http://127.0.0.1:8000/"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["blocked"] is True
