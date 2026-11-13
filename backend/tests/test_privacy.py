"""Tests for the shared masking/hashing privacy service (Task 2.2, Req 21).

Covers:
- masking reveals at most the final 4 chars (Req 21.2)
- masked form differs from original when len > 4 (Property 5 shape)
- short secrets (<=4) are fully masked (no near-total disclosure)
- masking is irreversible (hidden chars are discarded, not encoded)
- free-text masking preserves non-sensitive context and masks OTP/password/
  token/email/phone/CNIC/account spans, including mixed-language text
- one-way hashing: deterministic within an install, not reversible, salt-bound
- security: secret-laden strings never leave plaintext in the stored form
- robustness on empty / malformed / non-str input
"""

from __future__ import annotations

import pytest

from app.services import privacy
from app.services.privacy import (
    MAX_REVEAL,
    contains_plaintext_secret,
    hash_identifier,
    mask_text,
    mask_value,
    safe_for_storage,
)


# --- mask_value: core invariants (Req 21.2 / Property 5) -------------------


@pytest.mark.parametrize(
    "value",
    [
        "123456",            # OTP-like
        "hunter2password",   # password
        "+923001234567",     # phone
        "4111111111111111",  # card
        "aVeryLongSecretTokenValue1234",
        "ünïcodeSecret99",   # non-ASCII
        "اردوخفیہ1234",       # Urdu + digits
    ],
)
def test_mask_reveals_at_most_four_trailing_chars(value):
    masked = mask_value(value)
    # At most the final MAX_REVEAL chars of the original may appear as the tail.
    revealed_tail = value[len(value) - MAX_REVEAL:]
    assert masked.endswith(revealed_tail[-MAX_REVEAL:]) or len(value) <= MAX_REVEAL
    # Count trailing non-mask chars explicitly; never more than MAX_REVEAL.
    trailing = 0
    for ch in reversed(masked):
        if ch == privacy.MASK_CHAR:
            break
        trailing += 1
    assert trailing <= MAX_REVEAL


def test_masked_differs_from_original_when_longer_than_four():
    for value in ["12345", "password123", "abcdef", "0300-1234567"]:
        assert len(value) > MAX_REVEAL
        assert mask_value(value) != value


def test_short_secret_is_fully_masked():
    # Values of length <= 4 reveal nothing (no near-total disclosure).
    for value in ["a", "ab", "abc", "1234"]:
        masked = mask_value(value)
        assert set(masked) == {privacy.MASK_CHAR}
        assert len(masked) == len(value)
        assert masked != value or len(value) == 0


def test_mask_is_irreversible_hidden_chars_discarded():
    # The hidden prefix is pure mask glyphs; the original prefix is gone.
    value = "SuperSecretValue"
    masked = mask_value(value)
    hidden_prefix = masked[: len(masked) - MAX_REVEAL]
    assert set(hidden_prefix) == {privacy.MASK_CHAR}
    # Nothing in the masked form encodes the hidden original characters.
    assert "Super" not in masked
    assert "Secret" not in masked


def test_mask_value_empty_and_non_str():
    assert mask_value("") == ""
    assert mask_value(None) == ""
    assert mask_value(1234567) != "1234567"  # coerced + masked


# --- mask_text: free-text span masking (Req 21.1 context preserved) --------


def test_mask_text_masks_otp_preserves_context():
    original = "Your OTP is 918273 do not share it."
    masked = mask_text(original)
    assert "918273" not in masked
    # Non-sensitive context remains readable.
    assert "do not share it" in masked
    assert masked.startswith("Your OTP is")


def test_mask_text_masks_password_token_email_phone():
    original = (
        "login password: SuperSecret99 token=abcdef123456 "
        "email me at victim@example.com or call +923001234567"
    )
    masked = mask_text(original)
    assert "SuperSecret99" not in masked
    assert "abcdef123456" not in masked
    assert "victim@example.com" not in masked
    assert "+923001234567" not in masked
    # Context words survive.
    assert "login password" in masked
    assert "email me at" in masked


def test_mask_text_masks_cnic_and_account():
    original = "CNIC 35202-1234567-8 account 1234567890123456 transfer now"
    masked = mask_text(original)
    assert "35202-1234567-8" not in masked
    assert "1234567890123456" not in masked
    assert "transfer now" in masked


def test_mask_text_mixed_language_roman_urdu():
    # Roman-Urdu/English mixed scam text with an embedded OTP + phone.
    original = "Aap ka code 4821 hai, abhi call karein 0300-1234567 par."
    masked = mask_text(original)
    assert "4821" not in masked
    assert "0300-1234567" not in masked
    assert "Aap ka code" in masked
    assert "abhi call karein" in masked


def test_mask_text_malformed_and_empty_inputs():
    assert mask_text("") == ""
    assert mask_text(None) == ""
    # Content with no sensitive data is returned unchanged.
    benign = "This is a normal sentence with no secrets."
    assert mask_text(benign) == benign
    # Control chars / emoji don't crash and non-sensitive parts survive.
    weird = "hello \x00\x01 world 🚨 OTP 112233"
    masked = mask_text(weird)
    assert "112233" not in masked
    assert "hello" in masked and "world" in masked


# --- hashing (Req 21.3): one-way, fail-closed, configured-salt required ----

from app.services.privacy import (  # noqa: E402  (grouped with hashing tests)
    HashSaltNotConfigured,
    MIN_SALT_CHARS,
    hash_salt_configured,
)

# Two distinct, adequately-long salts for deterministic/variation tests.
_SALT_A = "A" * MIN_SALT_CHARS + "_random_salt_alpha_value"
_SALT_B = "B" * MIN_SALT_CHARS + "_random_salt_bravo_value"


def _settings_with_salt(salt):
    """Build a fresh, real Settings instance whose only configured secret is
    the given hash salt. This mimics a separate configuration/service instance
    (a separate "application restart") rather than mocking the hash function."""
    from app.core.config import Settings

    s = Settings()
    original = s.secret

    def _reader(name):
        if name == "hash_salt":
            return salt
        return original(name)

    # Patch only the salt lookup; all other secrets behave normally.
    object.__setattr__(s, "secret", _reader)
    return s


def test_hash_fails_closed_when_salt_missing():
    s = _settings_with_salt(None)
    with pytest.raises(HashSaltNotConfigured):
        hash_identifier("user@example.com", settings=s)


def test_hash_fails_closed_when_salt_too_short():
    s = _settings_with_salt("short")  # < MIN_SALT_CHARS
    assert hash_salt_configured(s) is False
    with pytest.raises(HashSaltNotConfigured):
        hash_identifier("user@example.com", settings=s)


def test_hash_salt_configured_reports_true_for_adequate_salt():
    assert hash_salt_configured(_settings_with_salt(_SALT_A)) is True


def test_same_salt_same_digest_across_separate_instances():
    # Two independently-constructed Settings instances with the SAME salt must
    # produce the SAME digest (stable across "restarts" within an install).
    s1 = _settings_with_salt(_SALT_A)
    s2 = _settings_with_salt(_SALT_A)
    assert s1 is not s2
    d1 = hash_identifier("user@example.com", settings=s1)
    d2 = hash_identifier("user@example.com", settings=s2)
    assert d1 == d2
    assert len(d1) == 64  # sha256 hex


def test_different_salts_produce_different_digests():
    d1 = hash_identifier("same-value", settings=_settings_with_salt(_SALT_A))
    d2 = hash_identifier("same-value", settings=_settings_with_salt(_SALT_B))
    assert d1 != d2


def test_hash_differs_for_different_values():
    s = _settings_with_salt(_SALT_A)
    assert hash_identifier("value-a", settings=s) != hash_identifier(
        "value-b", settings=s
    )


def test_hash_is_not_the_plaintext():
    s = _settings_with_salt(_SALT_A)
    secret = "0300-1234567"
    digest = hash_identifier(secret, settings=s)
    assert secret not in digest
    assert digest != secret


def test_hash_empty_and_non_str():
    s = _settings_with_salt(_SALT_A)
    assert len(hash_identifier("", settings=s)) == 64
    assert len(hash_identifier(None, settings=s)) == 64
    assert hash_identifier(123, settings=s) == hash_identifier("123", settings=s)


def test_salt_is_not_exposed_in_repr_capabilities_or_serialization():
    secret_salt = "SENSITIVE_SALT_" + ("Z" * MIN_SALT_CHARS)
    s = _settings_with_salt(secret_salt)
    blob = repr(s) + str(s) + str(vars(s)) + str(s.capabilities())
    assert secret_salt not in blob
    # capabilities() must not even reference the hash_salt key.
    assert "hash_salt" not in str(s.capabilities())
    # The HashSaltNotConfigured message never contains a salt value.
    assert "SENSITIVE" not in str(HashSaltNotConfigured())


def test_salt_is_not_written_to_logs(caplog):
    import logging

    secret_salt = "LOGSAFE_SALT_" + ("Q" * MIN_SALT_CHARS)
    s = _settings_with_salt(secret_salt)
    with caplog.at_level(logging.DEBUG):
        hash_identifier("user@example.com", settings=s)
        try:
            hash_identifier("x", settings=_settings_with_salt(None))
        except HashSaltNotConfigured:
            pass
    assert secret_salt not in caplog.text


# --- security: stored form never contains a plaintext secret ---------------


SECRET_LADEN = [
    "Your OTP is 918273, enter it now",
    "password: hunter2password",
    "Authorization: Bearer abc123def456ghi789",
    "token=eyJhbGciOiJIUzI1Ni9.payloadpart.signaturepart",
    "CNIC 35202-1234567-8",
    "card 4111 1111 1111 1111",
    "call +92 300 1234567 urgently",
    "email victim@example.com for prize",
    "Aap ka verification code 442211 hai",
]


@pytest.mark.parametrize("text", SECRET_LADEN)
def test_safe_for_storage_leaves_no_plaintext_secret(text):
    stored = safe_for_storage(text)
    assert not contains_plaintext_secret(stored, text), (
        f"plaintext secret survived masking: {text!r} -> {stored!r}"
    )


def test_contains_plaintext_secret_is_not_vacuous():
    # Guard: the leakage check must actually catch an unmasked secret.
    text = "Your OTP is 918273 now"
    assert contains_plaintext_secret(text, text) is True  # nothing masked -> leak
    assert contains_plaintext_secret(safe_for_storage(text), text) is False
