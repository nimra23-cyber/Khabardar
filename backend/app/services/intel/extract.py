"""Local, keyless IOC extraction (Req 13.1, 13.2, 13.3).

Extracts indicators of compromise from free text: URLs, domains, IP addresses,
emails, phone numbers, crypto wallet addresses, and payment/bank references.
Each IOC is normalized (Req 13.4). Empty content yields zero IOCs without error
(Req 13.2). Never raises on malformed input.

This performs NO network calls and asserts NOTHING about maliciousness: it only
identifies and normalizes indicators plus local, explainable pattern notes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.intel.normalize import normalize_ioc

# --- patterns (deliberately conservative; over-capture is acceptable) ------
_URL = re.compile(r"\bhttps?://[^\s<>\"')]+", re.IGNORECASE)
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_IPV4 = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
# IPv6: a broad candidate token (hex groups + colons, incl. '::' compression).
# Candidates are validated with ``ipaddress`` before being accepted, so the
# regex only needs to capture plausible tokens.
_IPV6 = re.compile(r"(?<![0-9A-Fa-f:])(?=[0-9A-Fa-f:]*::|(?:[0-9A-Fa-f]{1,4}:){7})[0-9A-Fa-f:]{2,39}(?![0-9A-Fa-f:])")
_DOMAIN = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+"
    r"(?:com|net|org|pk|info|xyz|top|club|link|click|gov|edu)(?:\.[a-z]{2})?\b",
    re.IGNORECASE,
)
_PHONE = re.compile(
    r"(?<!\d)(?:\+?92|0092|0)[\s\-]?\d{2,3}[\s\-]?\d{3}[\s\-]?\d{3,4}(?!\d)"
)
# BTC (base58, 26-35) / ETH (0x + 40 hex) crypto wallets.
_BTC = re.compile(r"\b(?:bc1|[13])[a-km-zA-HJ-NP-Z1-9]{25,39}\b")
_ETH = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
# IBAN-like / long bank account digit runs.
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")


@dataclass(frozen=True)
class IOC:
    ioc_type: str
    value: str            # original matched substring (evidence)
    normalized_value: str


def _valid_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def _valid_ipv6(ip: str) -> bool:
    import ipaddress

    try:
        return isinstance(ipaddress.ip_address(ip), ipaddress.IPv6Address)
    except ValueError:
        return False


def extract_iocs(text: str) -> list[IOC]:
    """Extract and normalize IOCs from ``text``. Deterministic; never raises."""
    if not isinstance(text, str) or not text:
        return []

    found: dict[tuple[str, str], IOC] = {}

    def add(ioc_type: str, raw: str):
        norm = normalize_ioc(ioc_type, raw)
        if not norm:
            return
        key = (ioc_type, norm)
        if key not in found:  # dedup within a single extraction (Req 13.5)
            found[key] = IOC(ioc_type=ioc_type, value=raw, normalized_value=norm)

    urls = [m.group(0) for m in _URL.finditer(text)]
    for u in urls:
        add("url", u)

    for m in _EMAIL.finditer(text):
        add("email", m.group(0))

    for m in _IPV4.finditer(text):
        if _valid_ipv4(m.group(0)):
            add("ip", m.group(0))

    for m in _IPV6.finditer(text):
        cand = m.group(0)
        if _valid_ipv6(cand):
            add("ip", cand)

    # Domains: skip ones that are only part of an email/URL already captured.
    joined_urls = " ".join(urls).lower()
    for m in _DOMAIN.finditer(text):
        d = m.group(0)
        if "@" in text[max(0, m.start() - 1): m.start()]:
            continue
        if d.lower() in joined_urls:
            continue
        add("domain", d)

    for m in _PHONE.finditer(text):
        add("phone", m.group(0))

    for m in _ETH.finditer(text):
        add("wallet", m.group(0))
    for m in _BTC.finditer(text):
        add("wallet", m.group(0))

    for m in _IBAN.finditer(text):
        add("bank", m.group(0))

    # Stable ordering by (type, normalized) for determinism.
    return [found[k] for k in sorted(found.keys())]
