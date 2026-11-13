"""Shared masking/hashing privacy service (Task 2.2, Req 21.1-21.4).

Every persistence path routes sensitive values through this single service
BEFORE anything reaches the database, so plaintext OTPs/passwords/tokens/PII
are never stored (Req 21.4). Two primitives:

* ``mask_value`` / ``mask_text`` -- irreversible masking that reveals at most
  the final 4 characters (Req 21.2). Used when a small, non-reconstructable
  hint (e.g. "last 4 of a phone/account") is useful for display.
* ``hash_identifier`` -- one-way, irreversible HMAC-SHA256 of an identifier,
  used when the exact value is NOT needed for display but a stable token is
  useful for dedup/correlation (Req 21.3). Deterministic within an install
  (same salt -> same hash) but not reversible.

HMAC key policy (hardened)
--------------------------
``hash_identifier`` **fails closed**: it requires an explicitly configured
``KHABARDAR_HASH_SALT`` that is sufficiently random (``MIN_SALT_CHARS`` chars).
If the salt is missing or too weak, it raises ``HashSaltNotConfigured`` rather
than silently falling back to a predictable key. The key is NEVER derived from
the database URL, a username, a fixed application string, or any other
predictable value, and the salt is never logged or exposed (it is held in the
config secret closure, excluded from repr/capabilities/serialization).

Design choices and guarantees:

* **At most 4 trailing chars revealed.** For values longer than 4 characters,
  all but the final 4 are replaced with a fixed mask glyph, so the masked form
  differs from the original (Property 5). For values of length <= 4 we reveal
  NOTHING (full mask), because revealing even 1-4 chars of a <=4-char secret
  would disclose most/all of it -- "at most 4" is an upper bound, and being
  stricter here is safe and still satisfies Req 21.2.
* **Irreversible.** Masking discards the hidden characters entirely (they are
  replaced, not encoded), and hashing is a one-way HMAC. Neither stores any
  recoverable form of the original.
* **Length is not leaked verbatim for long secrets.** To avoid turning the
  mask into a length oracle for long high-entropy secrets, the masked prefix
  is a FIXED number of glyphs rather than one-per-hidden-char once a value
  exceeds a small threshold. (Short values keep positional masking so a phone
  "last 4" stays readable.)

``mask_text`` detects sensitive spans (see ``pii_detectors``) inside free-form
scam content and masks each span in place, preserving the surrounding
non-sensitive context (Req 21.1 data minimization / useful context retained).
"""

from __future__ import annotations

import hashlib
import hmac

from app.core.config import Settings, get_settings
from app.services.pii_detectors import detect_spans, merge_spans

# Visible trailing characters allowed by Req 21.2 (upper bound).
MAX_REVEAL = 4
# Mask glyph. ASCII bullet-like char, safe in SQLite TEXT and JSON.
MASK_CHAR = "*"
# For values longer than this, use a FIXED-width mask prefix so the masked
# form does not encode the exact original length (anti length-oracle). Short
# values below this keep one-glyph-per-hidden-char so a readable "last 4" of a
# phone/account remains intuitive.
_FIXED_MASK_THRESHOLD = 12
_FIXED_MASK_WIDTH = 8

# Minimum length for a configured HMAC salt. 32 chars ~= 128+ bits when the
# operator uses a random value (e.g. `secrets.token_urlsafe(32)` ~ 43 chars).
# This is a guard against trivially weak salts, not a full entropy estimator.
MIN_SALT_CHARS = 32


class HashSaltNotConfigured(RuntimeError):
    """Raised when one-way hashing is requested but no adequate salt is set.

    Fail-closed behavior (Req 21.3): rather than hashing with a predictable or
    weak key, the service refuses and tells the operator exactly what to set.
    The message never contains the salt value (there is none to leak).
    """

    def __init__(self) -> None:
        super().__init__(
            "KHABARDAR_HASH_SALT is not configured or is too short. "
            f"Set it to a random secret of at least {MIN_SALT_CHARS} characters "
            "(e.g. `python -c \"import secrets; print(secrets.token_urlsafe(32))\"`) "
            "before using one-way identifier hashing."
        )


def _reveal_count(length: int) -> int:
    """How many trailing chars to reveal for a value of the given length.

    Never more than ``MAX_REVEAL``. For very short values (<=4) reveal 0 so we
    do not disclose most of a short secret.
    """
    if length <= MAX_REVEAL:
        return 0
    return MAX_REVEAL


def mask_value(value: str) -> str:
    """Return an irreversible masked form of a single sensitive ``value``.

    Reveals at most the final ``MAX_REVEAL`` characters; for values longer than
    4 chars the result is guaranteed to differ from the original. Empty input
    returns empty. Non-str input is coerced via ``str`` defensively.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    n = len(value)
    if n == 0:
        return ""

    reveal = _reveal_count(n)
    hidden = n - reveal
    tail = value[n - reveal:] if reveal else ""

    if hidden <= 0:
        # Only possible when reveal == n, i.e. n <= MAX_REVEAL and reveal==0
        # handled above; here reveal>0 and hidden==0 cannot occur, but guard.
        return MASK_CHAR * n

    if n > _FIXED_MASK_THRESHOLD:
        prefix = MASK_CHAR * _FIXED_MASK_WIDTH
    else:
        prefix = MASK_CHAR * hidden
    return f"{prefix}{tail}"


def mask_text(text: str) -> str:
    """Mask every detected sensitive span inside free-form ``text`` in place.

    Non-sensitive context is preserved. Safe on empty/malformed/mixed-language
    input (returns the input unchanged when nothing sensitive is detected).
    """
    if not isinstance(text, str) or not text:
        return text if isinstance(text, str) else ""

    spans = merge_spans(detect_spans(text))
    if not spans:
        return text

    out: list[str] = []
    cursor = 0
    for span in spans:
        if span.start > cursor:
            out.append(text[cursor:span.start])
        out.append(mask_value(text[span.start:span.end]))
        cursor = span.end
    if cursor < len(text):
        out.append(text[cursor:])
    return "".join(out)


def contains_plaintext_secret(stored: str, original: str) -> bool:
    """True if any detected sensitive value from ``original`` survives verbatim
    in ``stored``. Used by tests/guards to assert masking left no plaintext.

    A sensitive substring is considered leaked only if its *hidden* portion
    (everything except the allowed trailing reveal) appears verbatim in the
    stored form. The last <=4 chars are permitted by Req 21.2 and are ignored.
    """
    if not original:
        return False
    for span in merge_spans(detect_spans(original)):
        raw = original[span.start:span.end]
        reveal = _reveal_count(len(raw))
        hidden = raw[: len(raw) - reveal] if len(raw) - reveal > 0 else ""
        if len(hidden) >= 2 and hidden in stored:
            return True
    return False


def _salt(settings: Settings | None) -> bytes:
    """Resolve the configured HMAC salt, failing closed if inadequate.

    The ONLY accepted source is ``KHABARDAR_HASH_SALT`` (a secret held in the
    config closure). There is deliberately NO derived fallback: a key derived
    from the database URL / username / fixed string would be predictable and is
    not a secret. If the configured salt is missing or shorter than
    ``MIN_SALT_CHARS``, raise ``HashSaltNotConfigured`` (Req 21.3 fail-closed).
    """
    s = settings or get_settings()
    configured = s.secret("hash_salt")
    if not configured or len(configured.strip()) < MIN_SALT_CHARS:
        raise HashSaltNotConfigured()
    return configured.encode("utf-8")


def hash_salt_configured(settings: Settings | None = None) -> bool:
    """True if a usable (adequately long) hash salt is configured.

    Lets callers decide whether to attempt hashing without triggering the
    fail-closed exception. Never returns or logs the salt value itself.
    """
    s = settings or get_settings()
    configured = s.secret("hash_salt")
    return bool(configured and len(configured.strip()) >= MIN_SALT_CHARS)


def hash_identifier(value: str, *, settings: Settings | None = None) -> str:
    """Return a one-way, irreversible HMAC-SHA256 hex digest of ``value``.

    Requires an explicitly configured, adequately random ``KHABARDAR_HASH_SALT``
    (fails closed with ``HashSaltNotConfigured`` otherwise). Deterministic
    within an install (same salt + same value -> same digest), enabling
    dedup/correlation without storing the raw identifier (Req 21.3). Not
    reversible; the raw value cannot be recovered from the digest. Empty input
    hashes the empty string (still a stable, non-reversible token).
    """
    if value is None:
        value = ""
    if not isinstance(value, str):
        value = str(value)
    return hmac.new(_salt(settings), value.encode("utf-8"), hashlib.sha256).hexdigest()


def safe_for_storage(text: str) -> str:
    """Convenience: the masked form to persist for attacker-controlled content.

    This is the single call persistence paths (e.g. ScanHistory) use so that
    no raw OTP/password/token/PII is written (Req 21.1, 21.4). Equivalent to
    ``mask_text`` today; kept as the stable persistence API so future policy
    changes land in one place.
    """
    return mask_text(text)
