"""IOC normalization (Req 13.4).

Canonicalizes an IOC value per type: trim whitespace; lowercase case-insensitive
types (email/domain/url); normalize phone digits. Idempotent: normalizing an
already-normalized value returns the same value. Pure, deterministic.
"""

from __future__ import annotations

import re

_CASE_INSENSITIVE = {"email", "domain"}


def _normalize_url(v: str) -> str:
    """Lowercase scheme+host only (paths/queries are case-sensitive); trim a
    trailing slash on the path-less form."""
    from urllib.parse import urlsplit, urlunsplit

    try:
        parts = urlsplit(v)
    except ValueError:
        return v
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path
    rebuilt = urlunsplit((scheme, netloc, path, parts.query, parts.fragment))
    # Trim a single trailing slash only when there is no query/fragment/path-body.
    if rebuilt.endswith("/") and not parts.query and not parts.fragment:
        rebuilt = rebuilt.rstrip("/")
    return rebuilt


def normalize_ioc(ioc_type: str, value: str) -> str:
    """Return the canonical form of an IOC value for its type."""
    if value is None:
        return ""
    v = value.strip()
    if ioc_type in _CASE_INSENSITIVE:
        v = v.lower()
    if ioc_type == "url":
        return _normalize_url(v)
    if ioc_type == "phone":
        # Keep a leading +, strip spaces/dashes/parens from the rest.
        plus = v.startswith("+")
        digits = re.sub(r"\D", "", v)
        v = ("+" + digits) if plus else digits
    return v
