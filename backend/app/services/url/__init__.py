"""URL analysis services (Phase 3).

Local, keyless, deterministic URL phishing heuristics plus an SSRF address
policy used to classify whether a target is safe to reach. The MVP demo path
does NOT perform outbound fetches (network checks are reported "unavailable",
per Req 9.8); the SSRF policy is still enforced so any future fetch cannot
reach blocked ranges, and so a submitted private/metadata host is flagged and
never contacted.
"""

from app.services.url.pipeline import analyze_url, URL_RULESET_VERSION

__all__ = ["analyze_url", "URL_RULESET_VERSION"]
