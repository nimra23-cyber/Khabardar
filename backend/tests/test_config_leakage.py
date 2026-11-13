"""Deep secret-leakage tests for the config module (Task 1.1 hardening).

Goes beyond vars()/__dict__ and probes every realistic serialization and
diagnostic path a secret could escape through:

* repr() / str() of the Settings object
* f-string / format() interpolation
* logging a record that includes the object
* exception messages that include the object
* json.dumps on capabilities() and on __dict__ (default=str)
* pickle round-trip followed by a scan of the pickled bytes
* copy / deepcopy string scans
* traceback text when the object appears in a raised error

A sentinel secret value is injected via the environment and then searched for
in the output of each path. If the sentinel appears anywhere, the test fails.
"""

from __future__ import annotations

import copy
import importlib
import json
import logging
import pickle
import traceback

import pytest

SENTINEL = "SENTINEL-SECRET-DO-NOT-LEAK-abc123XYZ"


@pytest.fixture
def settings_with_secret(monkeypatch):
    # Set a sentinel in EVERY secret-bearing variable.
    for env in (
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "OLLAMA_BASE_URL",
        "GOOGLE_SAFE_BROWSING_KEY",
        "VIRUSTOTAL_KEY",
        "URLSCAN_KEY",
    ):
        monkeypatch.setenv(env, SENTINEL)
    config = importlib.import_module("app.core.config")
    return config.Settings()


def _assert_clean(text: str, path_name: str) -> None:
    assert SENTINEL not in text, f"SECRET LEAKED via {path_name}: {text!r}"


def test_repr_and_str_do_not_leak(settings_with_secret):
    _assert_clean(repr(settings_with_secret), "repr()")
    _assert_clean(str(settings_with_secret), "str()")


def test_fstring_and_format_do_not_leak(settings_with_secret):
    _assert_clean(f"{settings_with_secret}", "f-string")
    _assert_clean("{}".format(settings_with_secret), "str.format")
    _assert_clean(format(settings_with_secret), "format()")


def test_logging_does_not_leak(settings_with_secret, caplog):
    with caplog.at_level(logging.DEBUG):
        logging.getLogger("khabardar.test").debug("settings=%s", settings_with_secret)
        logging.getLogger("khabardar.test").debug("settings=%r", settings_with_secret)
    _assert_clean(caplog.text, "logging")


def test_exception_message_does_not_leak(settings_with_secret):
    try:
        raise ValueError(f"boom with {settings_with_secret!r}")
    except ValueError as exc:  # noqa: BLE001
        _assert_clean(str(exc), "exception str")
        _assert_clean("".join(traceback.format_exception(exc)), "traceback")


def test_vars_dict_do_not_leak(settings_with_secret):
    _assert_clean(str(vars(settings_with_secret)), "vars()")
    _assert_clean(str(settings_with_secret.__dict__), "__dict__")


def test_json_serialization_does_not_leak(settings_with_secret):
    # capabilities() is the only sanctioned serialization surface.
    _assert_clean(json.dumps(settings_with_secret.capabilities()), "json(capabilities)")
    # Even a careless json.dumps(default=str) over __dict__ must not leak.
    _assert_clean(
        json.dumps(settings_with_secret.__dict__, default=str),
        "json(__dict__, default=str)",
    )


def test_pickle_round_trip_does_not_leak(settings_with_secret):
    try:
        blob = pickle.dumps(settings_with_secret)
    except Exception:  # pragma: no cover - not picklable is acceptable & safe
        pytest.skip("Settings is not picklable (acceptable: no leak possible).")
    _assert_clean(blob.decode("latin-1", errors="ignore"), "pickle bytes")


def test_copy_and_deepcopy_do_not_leak(settings_with_secret):
    _assert_clean(str(vars(copy.copy(settings_with_secret))), "copy")
    _assert_clean(str(vars(copy.deepcopy(settings_with_secret))), "deepcopy")


def test_capabilities_reports_configured_without_value(settings_with_secret):
    caps = settings_with_secret.capabilities()
    # All secrets are set, so everything is "configured"...
    assert caps["ai_providers"]["gemini"] == "configured"
    assert caps["integrations"]["virustotal"] == "configured"
    # ...and the sentinel value is absent.
    _assert_clean(json.dumps(caps), "capabilities values")


def test_backend_can_still_read_secret_internally(settings_with_secret):
    # The sanctioned internal accessor DOES return the value (needed by providers).
    assert settings_with_secret.secret("gemini_key") == SENTINEL
    with pytest.raises(KeyError):
        settings_with_secret.secret("not_a_real_secret")
