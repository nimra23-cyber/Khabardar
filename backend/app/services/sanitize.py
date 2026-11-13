"""Markup/XSS neutralization for attacker-controlled scam text (Req 19.6).

Scam content is attacker-controlled: a user may paste a phishing SMS/email that
embeds ``<script>``, event-handler attributes, or ``javascript:`` URLs. Req
19.6 requires the platform to **neutralize executable script or markup before
storing or rendering it**.

Boundary & approach
-------------------
This is INPUT NEUTRALIZATION applied before persistence (and available again
before render). It is NOT a substitute for safe rendering: the stored value is
plain inert text, and the frontend MUST still render stored content as text
(never ``dangerouslySetInnerHTML`` / HTML injection). Storage-time
neutralization and text-only rendering are complementary controls, not
alternatives.

Implementation: rather than parse nested/malformed HTML with regexes (which is
bypassable), we tokenize with Python's standard-library ``html.parser`` based
tokenizer and **emit only text nodes**, dropping every tag and dropping the
*contents* of active elements (``<script>``, ``<style>``, etc.) entirely. We
then apply defense-in-depth passes:

1. Iteratively decode HTML entities / numeric refs BEFORE parsing so obfuscated
   payloads (``&lt;script&gt;``, double-encoded, ``&#106;avascript:``) are
   visible to the tokenizer and the scheme filter.
2. Tokenize and keep only text data; discard tags; discard active-element
   bodies.
3. Neutralize dangerous URL schemes (``javascript:``/``data:``/``vbscript:``),
   including whitespace-obfuscated variants, in the surviving text.
4. Final guard: strip any residual ``<``/``>`` so no markup delimiter survives
   even if a tokenizer edge case emitted one as text.

The result is plain, inert text. Ordinary English / Urdu / Roman-Urdu / Unicode
/ emoji text passes through unchanged apart from entity decoding and whitespace
collapsing.

Parser limitations (precise)
----------------------------
``html.parser.HTMLParser`` is a tokenizer, NOT a full HTML5 tree-construction
parser, so for deeply MALFORMED input (e.g. a null byte inside a tag name, or
mismatched/stray end tags that close an active region early) it may surface
fragments of an active element's text as DATA. Because of that we (a) pre-strip
comment / CDATA / declaration / PI and active-element BODY regions with
bounded, end-anchored patterns before tokenizing, and (b) apply a final guard
that removes every ``<`` / ``>`` and every dangerous scheme / ``on*=`` handler
from the surviving text.

Consequence: the stored output is ALWAYS inert (no ``<``/``>``, no
``javascript:``/``data:``/``vbscript:`` scheme, no inline event handler), which
is the Req 19.6 requirement. In rare deeply-malformed cases an active element's
*text* (e.g. the characters ``alert(1)``) may survive as plain, non-executable
words -- harmless because it is stored and rendered as text. We do NOT adopt a
heavier HTML5 parser (e.g. ``bleach``/``lxml``/``html5lib``) for the MVP: the
inert-text guarantee plus text-only frontend rendering already satisfies the
requirement, and those dependencies carry native-build / maintenance cost not
justified here. If future requirements demand preserving safe formatting, a
maintained HTML5 sanitizer should be revisited then.

Determinism & safety: pure function; never raises on malformed input.
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser

# Elements whose TEXT CONTENT is active/executable: we drop their bodies too,
# not just the tags.
_ACTIVE_ELEMENTS = frozenset(
    {
        "script",
        "style",
        "iframe",
        "object",
        "embed",
        "svg",
        "math",
        "template",
        "noscript",
        "title",  # title text is not body content; drop to avoid confusion
        "xmp",
        "noembed",
        "noframes",
    }
)

# Dangerous URL schemes. ``\s*`` between letters defeats "java\tscript:" and
# newline-split tricks; case-insensitive.
_DANGEROUS_SCHEME = re.compile(
    r"(?is)(?:j\s*a\s*v\s*a\s*s\s*c\s*r\s*i\s*p\s*t|v\s*b\s*s\s*c\s*r\s*i\s*p\s*t|"
    r"d\s*a\s*t\s*a)\s*:"
)

# Residual inline event-handler construct (defense-in-depth on surviving text).
_EVENT_HANDLER = re.compile(r"(?is)\bon[a-z]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)")

_MAX_DECODE_ITERS = 5

# Pre-pass removal of markup "container" regions that HTMLParser may fail to
# recognize when they are MALFORMED or UNTERMINATED (e.g. an unclosed
# "<!-- ...", a bogus "<!FOOBAR ...>", a "<![CDATA[ ... ]]>", or "<? ... ?>").
# In such regions HTMLParser can surface the *contents* (including an inner
# "<script>alert(1)" body) as plain text. The output is still inert (the final
# angle-bracket guard removes delimiters), but to avoid leaking active-element
# BODIES as text we drop these regions wholesale first. Each pattern tolerates
# the unterminated case by anchoring to end-of-string.
_COMMENT_REGION = re.compile(r"(?s)<!--.*?(?:-->|$)")
_CDATA_REGION = re.compile(r"(?s)<!\[CDATA\[.*?(?:\]\]>|$)")
_DECL_REGION = re.compile(r"(?s)<![^>]*(?:>|$)")
_PI_REGION = re.compile(r"(?s)<\?.*?(?:\?>|>|$)")
# Active-element body removal (incl. unterminated), applied as a pre-pass so a
# missing/mismatched close still drops the executable body. Non-greedy to the
# matching close tag, else to end-of-string.
_ACTIVE_BODY = re.compile(
    r"(?is)<\s*(script|style|iframe|object|embed|svg|math|template|noscript|"
    r"xmp|noembed|noframes|title)\b.*?(?:<\s*/\s*\1\s*>|$)"
)


def _strip_container_regions(text: str) -> str:
    """Remove comment/CDATA/declaration/PI and active-element body regions.

    Runs BEFORE tokenizing so that malformed or unterminated variants (which
    HTMLParser may otherwise expose as text) cannot leak active-element bodies.
    Bounded, idempotent-ish loop to handle regions revealed after an outer
    region is removed.
    """
    work = text
    for _ in range(_MAX_DECODE_ITERS):
        before = work
        work = _COMMENT_REGION.sub(" ", work)
        work = _CDATA_REGION.sub(" ", work)
        work = _ACTIVE_BODY.sub(" ", work)
        work = _PI_REGION.sub(" ", work)
        work = _DECL_REGION.sub(" ", work)
        if work == before:
            break
    return work


def _decode_entities(text: str) -> str:
    """Iteratively decode HTML entities / numeric refs until stable (bounded).

    Attackers nest encodings (``&amp;lt;script&amp;gt;``). We decode repeatedly
    so later passes see the fully-decoded payload, with a hard iteration cap so
    a crafted input cannot loop.
    """
    prev = text
    for _ in range(_MAX_DECODE_ITERS):
        decoded = html.unescape(prev)
        if decoded == prev:
            return decoded
        prev = decoded
    return prev


class _TextOnlyExtractor(HTMLParser):
    """Collect only text nodes; drop all tags and active-element bodies.

    Using the stdlib tokenizer avoids regex HTML-parsing bypasses: malformed
    tags, attributes containing ``>``, unusual nesting, and CDATA are handled
    by the tokenizer, and because we emit NO tags (only text) there is no way
    for markup to survive through re-emission.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._suppress_depth = 0  # >0 while inside an active element

    # --- tag handling: we never emit tags, only track active-element depth --
    def handle_starttag(self, tag, attrs):
        if tag.lower() in _ACTIVE_ELEMENTS:
            self._suppress_depth += 1

    def handle_startendtag(self, tag, attrs):
        # Self-closing active element has no body to suppress.
        return

    def handle_endtag(self, tag):
        if tag.lower() in _ACTIVE_ELEMENTS and self._suppress_depth > 0:
            self._suppress_depth -= 1

    # --- data: keep text only when not inside an active element ------------
    def handle_data(self, data):
        if self._suppress_depth == 0 and data:
            self._chunks.append(data)

    # comments, declarations, processing instructions, CDATA -> dropped
    def handle_comment(self, data):
        return

    def handle_decl(self, decl):
        return

    def handle_pi(self, data):
        return

    def unknown_decl(self, data):
        return

    def get_text(self) -> str:
        return "".join(self._chunks)


def neutralize(text: str) -> str:
    """Return an inert, markup-free version of ``text`` (Req 19.6).

    Guarantees on the output:
    * contains no ``<`` or ``>`` characters (no markup delimiters survive),
    * contains no ``<script>``/``<style>``/etc. element or its contents,
    * contains no ``javascript:``/``data:``/``vbscript:`` scheme token,
    * contains no inline ``on*=`` event-handler construct,
    while preserving ordinary readable text.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    if not text:
        return ""

    # 1) Fully decode nested entities so obfuscated payloads are visible to the
    #    tokenizer and the scheme filter.
    work = _decode_entities(text)

    # 1b) Pre-strip comment/CDATA/declaration/PI and active-element BODY regions
    #     so malformed/unterminated variants cannot leak executable bodies as
    #     text (HTMLParser does not reliably suppress those).
    work = _strip_container_regions(work)

    # 2) Tokenize and keep text only (drops tags + active-element bodies).
    parser = _TextOnlyExtractor()
    try:
        parser.feed(work)
        parser.close()
        work = parser.get_text()
    except Exception:
        # Tokenizer must never break neutralization; fall back to a hard strip.
        work = re.sub(r"(?s)<[^>]*>", " ", work)

    # 3) Decode again (the tokenizer may surface entities inside text) and
    #    neutralize dangerous URL schemes in the surviving text.
    work = _decode_entities(work)
    work = _EVENT_HANDLER.sub(" ", work)
    work = _DANGEROUS_SCHEME.sub("[removed]:", work)

    # 4) Final guard: no angle brackets may survive under any circumstance.
    work = work.replace("<", " ").replace(">", " ")

    # Collapse runs of horizontal whitespace introduced by removals.
    work = re.sub(r"[ \t\f\v]{2,}", " ", work)
    return work.strip()


def is_neutralized(text: str) -> bool:
    """True if ``text`` already contains no executable markup indicators.

    Used by tests/guards to assert a stored value is inert.
    """
    if not text:
        return True
    if "<" in text or ">" in text:
        return False
    if _DANGEROUS_SCHEME.search(text):
        return False
    if _EVENT_HANDLER.search(text):
        return False
    return True
