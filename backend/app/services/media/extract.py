"""URL extraction from plain text (Req 12).

Reuses the ``_URL`` regex from ``app.services.intel.extract`` for consistent
URL detection across the platform. Never fetches or opens URLs.
"""

from __future__ import annotations

import re

# Same conservative pattern used by the IOC extractor (Req 13.1).
_URL = re.compile(r"\bhttps?://[^\s<>\"')]+", re.IGNORECASE)


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from ``text``. Returns a list of URL strings.

    Parameters
    ----------
    text:
        Any string; may be OCR output or QR decoded text.

    Returns
    -------
    list[str]
        Unique URLs found in the text, in order of first appearance.
    """
    if not isinstance(text, str) or not text:
        return []
    seen: set[str] = set()
    urls: list[str] = []
    for match in _URL.finditer(text):
        url = match.group(0)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls
