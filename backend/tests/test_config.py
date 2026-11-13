"""Unit tests for the config/secrets loader (Task 1.1).

Acceptance criteria verified here:
* Config loads with NO optional keys set and never raises on a missing key.
* Absent providers/integrations report "unavailable" (never configured).
* No secret value is ever serialized / exposed by the settings object.
* The default host is loopback (local-only, MVP-AC-11).
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def fresh_settings(monkeypatch):
    """Build a Settings instance with all optional keys unset."""
    for key in (
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "OLLAMA_BASE_URL",
        "GOOGLE_SAFE_BROWSING_KEY",
        "VIRUSTOTAL_KEY",
        "URLSCAN_KEY",
        "KHABARDAR_HOST",
        "KHABARDAR_PORT",
        "KHABARDAR_RETENTION_DAYS",
    ):
        monkeypatch.delenv(key, raising=False)

    config = importlib.import_module("app.core.config")
    return config.Settings()


def test_loads_without_any_optional_keys(fresh_settings):
    # Should not raise; defaults applied.
    assert fresh_settings.host == "127.0.0.1"
    assert fresh_settings.port == 8000
    assert fresh_settings.is_local_only is True


def test_absent_providers_report_unavailable(fresh_settings):
    caps = fresh_settings.capabilities()
    assert caps["ai_providers"] == {
        "gemini": "unavailable",
        "groq": "unavailable",
        "ollama": "unavailable",
    }
    assert caps["integrations"] == {
        "safe_browsing": "unavailable",
        "virustotal": "unavailable",
        "urlscan": "unavailable",
    }


def test_configured_provider_reports_configured_not_value(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "super-secret-value-123")
    config = importlib.import_module("app.core.config")
    settings = config.Settings()

    caps = settings.capabilities()
    # Availability flips to "configured"...
    assert caps["ai_providers"]["groq"] == "configured"
    # ...but the secret VALUE never appears anywhere in the capabilities map.
    assert "super-secret-value-123" not in str(caps)


def test_no_secret_value_in_object_dict(monkeypatch):
    """Generic serialization of the settings object must not leak secrets."""
    monkeypatch.setenv("GEMINI_API_KEY", "leak-me-if-you-can")
    monkeypatch.setenv("VIRUSTOTAL_KEY", "another-secret")
    config = importlib.import_module("app.core.config")
    settings = config.Settings()

    # vars()/__dict__ is the most common accidental-serialization path.
    serialized = str(vars(settings))
    assert "leak-me-if-you-can" not in serialized
    assert "another-secret" not in serialized


def test_retention_days_clamped(monkeypatch):
    monkeypatch.setenv("KHABARDAR_RETENTION_DAYS", "99999")
    config = importlib.import_module("app.core.config")
    settings = config.Settings()
    assert settings.retention_days == 3650

    monkeypatch.setenv("KHABARDAR_RETENTION_DAYS", "0")
    settings = config.Settings()
    assert settings.retention_days == 1
