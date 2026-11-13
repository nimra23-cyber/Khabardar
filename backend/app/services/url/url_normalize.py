"""Safe URL parsing & normalization (Req 11.9).

Validates scheme (http/https only), extracts and IDNA-normalizes the hostname,
strips userinfo, and reports whether the URL is syntactically valid. No network
access. Rejecting a malformed URL here means no fetch is ever attempted
(Req 11.10).
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

ALLOWED_SCHEMES = {"http", "https"}


@dataclass(frozen=True)
class ParsedURL:
    valid: bool
    scheme: str
    host: str            # IDNA/lowercased hostname (no userinfo, no port)
    port: int | None
    had_userinfo: bool
    is_ip_literal: bool
    reason: str | None   # why invalid, when valid is False


def _is_ip_literal(host: str) -> bool:
    import ipaddress

    h = host.strip("[]")  # IPv6 literals are bracketed in URLs
    try:
        ipaddress.ip_address(h)
        return True
    except ValueError:
        return False


def normalize_url(raw: str) -> ParsedURL:
    """Parse and normalize ``raw``. Never raises; returns a ParsedURL."""
    invalid = ParsedURL(False, "", "", None, False, False, None)
    if not isinstance(raw, str) or not raw.strip():
        return ParsedURL(False, "", "", None, False, False, "empty")

    candidate = raw.strip()
    try:
        parts = urlsplit(candidate)
    except ValueError:
        return ParsedURL(False, "", "", None, False, False, "unparseable")

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        return ParsedURL(False, scheme, "", None, False, False, "scheme_not_allowed")

    had_userinfo = "@" in (parts.netloc or "")
    hostname = parts.hostname  # urlsplit strips userinfo + port already
    if not hostname:
        return ParsedURL(False, scheme, "", None, had_userinfo, False, "no_host")

    host = hostname.lower()
    # IDNA-normalize unicode hostnames to punycode; reject if it fails.
    try:
        if any(ord(ch) > 127 for ch in host):
            host = host.encode("idna").decode("ascii")
    except (UnicodeError, ValueError):
        return ParsedURL(False, scheme, "", None, had_userinfo, False, "bad_idna")

    try:
        port = parts.port
    except ValueError:
        return ParsedURL(False, scheme, host, None, had_userinfo, False, "bad_port")

    return ParsedURL(
        valid=True,
        scheme=scheme,
        host=host,
        port=port,
        had_userinfo=had_userinfo,
        is_ip_literal=_is_ip_literal(host),
        reason=None,
    )
