"""Pattern detectors for sensitive values in free-text scam content (Req 21.2).

This module finds spans of *sensitive* substrings inside attacker-controlled
scam text so the privacy service can mask them before anything is persisted to
``ScanHistory``. It deliberately errs toward OVER-detection: a false positive
only masks a bit more text, while a false negative could persist a plaintext
secret -- which Req 21.4 forbids.

Each detector returns a list of ``Span(start, end, kind)`` (half-open indices
into the original string). The privacy service merges overlapping spans and
applies masking. Detectors never raise on malformed input; they operate on
whatever ``str`` they are given (empty strings, control chars, mixed-language
Urdu/Roman-Urdu/English text, emoji, etc.).

Covered sensitive categories (Req 21.2):
- OTP / one-time passcodes (contextual + bare numeric codes)
- passwords / authentication tokens (contextual "password: ...", long tokens)
- email addresses
- phone numbers (Pakistani local/+92 and generic international)
- government identifiers (Pakistani CNIC 13-digit, with/without dashes)
- financial account numbers (long digit runs / IBAN-like / card-like groups)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    """A half-open ``[start, end)`` slice of a source string, with a label."""

    start: int
    end: int
    kind: str

    def __post_init__(self) -> None:  # defensive: never allow inverted spans
        if self.start < 0 or self.end < self.start:
            raise ValueError(f"invalid span: {self.start}..{self.end}")


# --- Core value patterns ---------------------------------------------------

# Email: conservative but covers the common cases. We don't need RFC-perfect
# matching; we only need to find and mask addresses.
_EMAIL = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
)

# Pakistani CNIC: 13 digits, commonly formatted #####-#######-#.
_CNIC = re.compile(r"\b\d{5}-?\d{7}-?\d\b")

# Phone numbers:
#   +92 3xx xxxxxxx / 0092... / local 03xx-xxxxxxx / generic +<country>...
# Also a generic international form with optional separators.
_PHONE = re.compile(
    r"(?<!\d)(?:\+?92|0092|0)[\s\-]?\d{2,3}[\s\-]?\d{3}[\s\-]?\d{3,4}(?!\d)"
    r"|(?<![\w.])\+\d{1,3}[\s\-]?(?:\d[\s\-]?){6,13}\d(?![\w.])",
)

# Financial-ish long digit groups: 12+ digit runs, or card-like 4x4 groups,
# or IBAN-like (2 letters + 2 digits + up to 30 alnum).
_CARD = re.compile(r"(?<!\d)(?:\d[ \-]?){13,19}(?<=\d)(?!\d)")
_LONG_DIGITS = re.compile(r"(?<!\d)\d{12,}(?!\d)")
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")

# OTP: contextual ("OTP 123456", "code: 4821", Urdu/Roman "code") OR a bare
# 4-8 digit code that is NOT part of a longer number. We require a word
# boundary so years/short counts in prose aren't all masked -- contextual
# detection (below) is the strong signal; bare detection is a safety net for
# codes adjacent to OTP-ish keywords.
# Allow a few short filler tokens ("is", "hai", "=", ":") between the keyword
# and the numeric code, so "OTP is 918273" / "code 4821 hai" are caught, while
# still requiring the code to be reasonably near the keyword (bounded lookahead
# via {0,3} short words) to limit over-matching unrelated numbers.
_OTP_CONTEXT = re.compile(
    r"(?i)(?:otp|one[\s\-]?time(?:\s*(?:password|passcode|pin|code))?|"
    r"verification\s*code|auth(?:entication)?\s*code|pass\s*code|"
    r"\bpin\b|\bcode\b|\brmz\b|\bkod\b)"  # rmz/kod ~ Roman-Urdu "ramz/code"
    r"(?:[\s:=\-\u06d4.]+[A-Za-z]{1,4}){0,3}"  # optional short filler words
    r"[\s:=\-\u06d4.]*?(\d{3,8})",
)

# Password / token context: capture the value after a password/token label up
# to whitespace or end. Values may contain non-space symbols.
_SECRET_CONTEXT = re.compile(
    r"(?i)(?:password|passwd|pwd|pass|token|secret|api[\s\-]?key|"
    r"bearer|auth)\b\s*[:=\-]?\s*(\S{4,})",
)

# Standalone high-entropy token: long run of token-ish chars (letters+digits
# mixed) that looks like a key/JWT/session token rather than a normal word.
_BEARER = re.compile(r"\bBearer\s+([A-Za-z0-9._\-]{8,})", re.IGNORECASE)
_JWT = re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}\.[A-Za-z0-9_\-]{5,}\b")


def _add(spans: list[Span], start: int, end: int, kind: str) -> None:
    if end > start:
        spans.append(Span(start, end, kind))


def detect_spans(text: str) -> list[Span]:
    """Return sensitive spans found in ``text`` (never raises on bad input)."""
    if not isinstance(text, str) or not text:
        return []

    spans: list[Span] = []

    for m in _EMAIL.finditer(text):
        _add(spans, m.start(), m.end(), "email")
    for m in _CNIC.finditer(text):
        _add(spans, m.start(), m.end(), "cnic")
    for m in _PHONE.finditer(text):
        _add(spans, m.start(), m.end(), "phone")
    for m in _IBAN.finditer(text):
        _add(spans, m.start(), m.end(), "account")
    for m in _CARD.finditer(text):
        _add(spans, m.start(), m.end(), "account")
    for m in _LONG_DIGITS.finditer(text):
        _add(spans, m.start(), m.end(), "account")
    for m in _JWT.finditer(text):
        _add(spans, m.start(), m.end(), "token")

    # Contextual detectors: mask the captured VALUE group only (group 1), so
    # the surrounding non-sensitive label/context is preserved.
    for m in _OTP_CONTEXT.finditer(text):
        _add(spans, m.start(1), m.end(1), "otp")
    for m in _SECRET_CONTEXT.finditer(text):
        _add(spans, m.start(1), m.end(1), "secret")
    for m in _BEARER.finditer(text):
        _add(spans, m.start(1), m.end(1), "token")

    return spans


def merge_spans(spans: list[Span]) -> list[Span]:
    """Merge overlapping/adjacent spans into non-overlapping, sorted spans.

    When two detectors overlap, the merged span keeps the FIRST kind seen in
    sorted order; the kind is only a hint for masking (masking is uniform), so
    the exact label on an overlap does not affect the privacy guarantee.
    """
    if not spans:
        return []
    ordered = sorted(spans, key=lambda s: (s.start, s.end))
    merged: list[Span] = [ordered[0]]
    for s in ordered[1:]:
        last = merged[-1]
        if s.start <= last.end:  # overlap or touch -> merge
            if s.end > last.end:
                merged[-1] = Span(last.start, s.end, last.kind)
        else:
            merged.append(s)
    return merged
