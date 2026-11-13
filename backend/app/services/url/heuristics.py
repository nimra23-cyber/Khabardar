"""Keyless local URL phishing heuristics (Req 9.5, 9.6).

Always-available, deterministic, no-network indicators. Each returns a stable
indicator dict with id/name/evidence/weight when triggered. These feed the
transparent URL scorer. No outbound requests are made.
"""

from __future__ import annotations

from app.services.url.brand_lists import (
    BRAND_DOMAINS,
    BRAND_TOKENS,
    SHORTENER_DOMAINS,
    SUSPICIOUS_TLDS,
)
from app.services.url.url_normalize import ParsedURL


# Common two-label public suffixes where the registrable domain is the THIRD
# label from the end (e.g. example.com.pk). Not exhaustive; a full PSL is
# out of scope for the MVP, so this covers the PK/common cases we care about.
_MULTI_PART_SUFFIXES = {
    "com.pk", "gov.pk", "org.pk", "net.pk", "edu.pk",
    "co.uk", "org.uk", "gov.uk", "ac.uk",
    "com.au", "co.in", "co.jp",
}


def _registrable_tail(host: str) -> str:
    """Best-effort registrable domain (handles two-label public suffixes).

    For ``jazzcash.com.pk`` returns ``jazzcash.com.pk`` (not ``com.pk``); for
    ``evil.xyz`` returns ``evil.xyz``. Heuristic only -- not a full Public
    Suffix List.
    """
    labels = host.split(".")
    if len(labels) >= 3 and ".".join(labels[-2:]) in _MULTI_PART_SUFFIXES:
        return ".".join(labels[-3:])
    if len(labels) >= 2:
        return ".".join(labels[-2:])
    return host


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def evaluate_url_signals(parsed: ParsedURL, raw: str) -> list[dict]:
    """Return triggered indicator dicts for a parsed URL. Deterministic."""
    if not parsed.valid:
        return []

    host = parsed.host
    tail = _registrable_tail(host)
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    indicators: list[dict] = []

    def add(ind_id, name, evidence, weight):
        indicators.append(
            {"id": ind_id, "name": name, "evidence": evidence, "weight": weight}
        )

    # 1. No HTTPS.
    if parsed.scheme != "https":
        add("no_https", "No HTTPS", parsed.scheme + "://", 15)

    # 2. IP-literal host.
    if parsed.is_ip_literal:
        add("ip_url", "IP-address URL", host, 35)

    # 3. userinfo in URL (user:pass@host obfuscation).
    if parsed.had_userinfo:
        add("userinfo", "Embedded credentials in URL", "user@ in URL", 25)

    # 4. URL shortener.
    if tail in SHORTENER_DOMAINS or host in SHORTENER_DOMAINS:
        add("shortener", "URL shortener", tail, 20)

    # 5. Suspicious TLD.
    if tld in SUSPICIOUS_TLDS:
        add("suspicious_tld", "Suspicious top-level domain", "." + tld, 20)

    # 6. Punycode / IDNA (possible homograph).
    if "xn--" in host:
        add("punycode", "Punycode/IDNA homograph", host, 25)

    # 7. Excessive subdomain depth.
    if host.count(".") >= 4 and not parsed.is_ip_literal:
        add("deep_subdomain", "Excessive subdomain depth", host, 15)

    # 8. Brand token in subdomain/path but NOT the registrable domain
    #    (e.g. jazzcash.secure-login.xyz) -> impersonation.
    low_raw = raw.lower()
    for token in BRAND_TOKENS:
        if token in host and token not in tail:
            add(
                "brand_in_subdomain",
                "Brand name in subdomain (impersonation)",
                token,
                30,
            )
            break
        if token in low_raw and token not in host and token not in tail:
            add(
                "brand_in_path",
                "Brand name in URL path (impersonation)",
                token,
                18,
            )
            break

    # 9. Typosquatting: registrable tail is edit-distance 1-2 from a known brand
    #    domain but not equal (e.g. jazzcach.com.pk).
    if not parsed.is_ip_literal:
        for brand in BRAND_DOMAINS:
            d = _levenshtein(tail, brand)
            if 0 < d <= 2:
                add("typosquat", "Possible typosquatting of a known brand", f"{tail}~{brand}", 35)
                break

    return indicators
