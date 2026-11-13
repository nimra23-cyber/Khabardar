"""Brand/shortener/TLD reference lists for URL heuristics (Phase 3).

INITIAL, PARTIAL lists focused on the Pakistani context. Not exhaustive
(Req 23 honesty). Used by heuristics.py for typosquatting and brand-in-subdomain
detection.
"""

from __future__ import annotations

# Legitimate brand/bank domains commonly impersonated in PK scams.
BRAND_DOMAINS: list[str] = [
    "jazzcash.com.pk",
    "easypaisa.com.pk",
    "hbl.com",
    "ubldigital.com",
    "meezanbank.com",
    "bankalfalah.com",
    "mcb.com.pk",
    "nadra.gov.pk",
    "fbr.gov.pk",
    "google.com",
    "facebook.com",
    "whatsapp.com",
    "daraz.pk",
]

# Brand NAME tokens (for brand-in-subdomain / path impersonation checks).
BRAND_TOKENS: list[str] = [
    "jazzcash",
    "easypaisa",
    "hbl",
    "ubl",
    "meezan",
    "alfalah",
    "nadra",
    "fbr",
    "google",
    "facebook",
    "whatsapp",
    "daraz",
    "paypal",
]

# Known URL shortener domains.
SHORTENER_DOMAINS: set[str] = {
    "bit.ly",
    "tinyurl.com",
    "goo.gl",
    "t.co",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "rb.gy",
    "cutt.ly",
    "shorturl.at",
}

# TLDs disproportionately abused for throwaway phishing domains.
SUSPICIOUS_TLDS: set[str] = {
    "zip",
    "mov",
    "xyz",
    "top",
    "club",
    "click",
    "link",
    "gq",
    "tk",
    "ml",
    "cf",
    "ga",
    "work",
    "rest",
}
