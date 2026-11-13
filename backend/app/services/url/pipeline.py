"""URL analysis pipeline (Req 9, 10, 11): validate -> SSRF policy -> local
heuristics -> score -> indicators -> explanation -> recommended action.

Keyless and local: no outbound fetch is performed in this MVP path, so
network-dependent checks (WHOIS, SSL, live reputation) are reported as
"unavailable" honestly (Req 9.3/9.4/9.8, 10.3/10.5). A submitted host that
resolves to a blocked (loopback/private/metadata/reserved) range is flagged
``blocked`` and is NEVER contacted (Req 11.2/11.3).
"""

from __future__ import annotations

from app.core.config import get_settings
from app.services.detection.classify import classify
from app.services.url.address_policy import host_is_blocked
from app.services.url.heuristics import evaluate_url_signals
from app.services.url.scoring import score_url_indicators
from app.services.url.url_normalize import normalize_url

URL_RULESET_VERSION = "url-rules-3.0.0"

# Integrations that require credentials / live calls -> Scope B. Always honest
# "unavailable" in the MVP (Req 10.3/10.5).
_INTEGRATION_NAMES = ("safe_browsing", "virustotal", "urlscan", "whois", "ssl")


def _integration_states() -> dict[str, str]:
    """Report each external integration as 'unavailable' (keyless MVP).

    We never present an integration as available without a verified live call
    (Req 10.5). The MVP performs no live calls, so all are 'unavailable'.
    """
    return {name: "unavailable" for name in _INTEGRATION_NAMES}


def _recommended_action(classification: str, blocked: bool) -> str:
    if blocked:
        return "do_not_visit"
    return {
        "SAFE": "likely_safe_but_verify",
        "SUSPICIOUS": "do_not_enter_credentials",
        "HIGH RISK": "do_not_visit",
    }.get(classification, "verify")


def analyze_url(raw_url: str) -> dict:
    """Analyze a URL locally. Returns a plain dict (validated by the schema).

    Raises nothing; invalid URLs are reported via ``valid=False`` so the router
    can map them to a 400 with no network action.
    """
    parsed = normalize_url(raw_url)
    if not parsed.valid:
        return {
            "valid": False,
            "reason": parsed.reason or "invalid_url",
        }

    # SSRF address policy: resolve-and-check. If blocked, flag and DO NOT fetch.
    blocked = host_is_blocked(parsed.host)

    indicators = evaluate_url_signals(parsed, raw_url)
    if blocked:
        indicators = indicators + [
            {
                "id": "ssrf_blocked",
                "name": "Resolves to a private/loopback/metadata address",
                "evidence": parsed.host,
                "weight": 60,
            }
        ]

    score = score_url_indicators(indicators)
    classification = classify(score)
    action = _recommended_action(classification, blocked)

    explanation_en = (
        f"The URL host '{parsed.host}' was analyzed with local heuristics. "
        + (
            "It resolves to a blocked internal/metadata address and was not contacted. "
            if blocked
            else ""
        )
        + (
            f"{len(indicators)} indicator(s) contributed to the score."
            if indicators
            else "No local phishing indicators were detected (not a guarantee of safety)."
        )
    )

    return {
        "valid": True,
        "url": raw_url,
        "domain": parsed.host,
        "scheme": parsed.scheme,
        "is_ip_url": parsed.is_ip_literal,
        "blocked": blocked,
        "risk_score": score,
        "classification": classification,
        "indicators": indicators,
        "integration_states": _integration_states(),
        "redirect_chain": [],  # no fetch performed (network checks unavailable)
        "network_checks": "unavailable",
        "recommended_action": action,
        "explanation_en": explanation_en,
        "ruleset_version": URL_RULESET_VERSION,
        "public_demo": get_settings().public_demo,
    }
