"""Tests for markup/XSS neutralization (Task 2.4, Req 19.6).

Covers HTML/script injection, event-handler attributes, dangerous URL schemes,
malformed HTML, unicode/encoded payloads, and safe ordinary-text preservation.
"""

from __future__ import annotations

import re

import pytest

from app.services.sanitize import is_neutralized, neutralize


# Realistic XSS payloads an attacker might paste as "scam text".
XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "<svg/onload=alert(1)>",
    "<a href=\"javascript:alert(1)\">click</a>",
    "<iframe src=\"javascript:alert(1)\"></iframe>",
    "<body onload=alert(1)>",
    "<div onclick=\"steal()\">tap</div>",
    "<SCRIPT>alert(1)</SCRIPT>",
    "<scr<script>ipt>alert(1)</scr</script>ipt>",  # nested/split
    "<img src=x onerror=\"fetch('//evil')\">",
    "<style>body{background:url('javascript:alert(1)')}</style>",
    "<object data=\"data:text/html,<script>alert(1)</script>\"></object>",
    "<a href=\"vbscript:msgbox(1)\">x</a>",
    "<math><mtext></mtext></math>",
    "plain <b>bold</b> text",
]


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_neutralize_removes_executable_markup(payload):
    out = neutralize(payload)
    # No markup delimiters survive.
    assert "<" not in out and ">" not in out
    # No active scheme tokens survive.
    assert "javascript:" not in out.lower()
    assert "vbscript:" not in out.lower()
    # No obvious script keyword as a tag survives (word may remain as text,
    # but never as "<script").
    assert "<script" not in out.lower()
    assert is_neutralized(out)


def test_script_contents_are_dropped():
    out = neutralize("<script>stealCookies()</script>safe tail")
    assert "stealCookies" not in out
    assert "safe tail" in out


def test_event_handler_attributes_removed():
    out = neutralize('<div onclick="evil()">Hello</div>')
    assert "onclick" not in out.lower()
    assert "evil()" not in out
    assert "Hello" in out


def test_dangerous_schemes_neutralized():
    for s in ["javascript:alert(1)", "JAVASCRIPT:x", "java\tscript:y", "vbscript:z"]:
        out = neutralize(f"link {s} here")
        assert "javascript:" not in out.lower()
        assert "vbscript:" not in out.lower()


def test_encoded_payload_is_decoded_then_neutralized():
    # Entity-encoded <script> must be decoded and then removed.
    encoded = "&lt;script&gt;alert(1)&lt;/script&gt;"
    out = neutralize(encoded)
    assert "<" not in out and ">" not in out
    assert "<script" not in out.lower()
    # Double-encoded.
    double = "&amp;lt;script&amp;gt;alert(1)&amp;lt;/script&amp;gt;"
    out2 = neutralize(double)
    assert "<script" not in out2.lower()


def test_numeric_char_reference_payload():
    # &#x6a;... decodes toward "javascript:"; must be neutralized.
    out = neutralize("&#106;avascript:alert(1)")
    assert "javascript:" not in out.lower()


def test_malformed_html_does_not_crash_and_is_inert():
    for bad in ["<<>>", "<script", "<<script>>", "<img src=", "< >", "a<b", "x>y"]:
        out = neutralize(bad)
        assert "<" not in out and ">" not in out


def test_unicode_and_ordinary_text_preserved():
    # Urdu + Roman-Urdu + emoji with no markup should pass through (trimmed).
    text = "یہ ایک عام پیغام ہے — aap ka din acha ho 🚨"
    assert neutralize(text) == text
    assert neutralize("Just a normal scam-free sentence.") == "Just a normal scam-free sentence."


def test_empty_and_none_inputs():
    assert neutralize("") == ""
    assert neutralize(None) == ""
    assert is_neutralized("") is True


def test_is_neutralized_detects_markup():
    assert is_neutralized("<script>") is False
    assert is_neutralized("onerror=alert(1)") is False
    assert is_neutralized("javascript:x") is False
    assert is_neutralized("clean text") is True


# --- regression: parser-based neutralization resists bypasses --------------

BYPASS_PAYLOADS = [
    # Attribute value containing a '>' that would break a naive regex tag match.
    '<img src="x>y" onerror="alert(1)">tail',
    # Malformed/unterminated tag.
    "<script>alert(1)",
    # Mixed/alternating case and extra spaces.
    "<ScRiPt >alert(1)</ScRiPt >after",
    # Nested active elements.
    "<svg><script>alert(1)</script></svg>visible",
    # CDATA-ish / declaration content.
    "<![CDATA[<script>alert(1)</script>]]>text",
    # Attribute with encoded javascript scheme.
    '<a href="jav&#x09;ascript:alert(1)">x</a>',
    # Event handler with no quotes.
    "<div onmouseover=alert(1)>hi</div>",
    # Backtick / unusual whitespace in scheme.
    "java\nscript:alert(1)",
    # Comment hiding a tag.
    "<!-- <script>alert(1)</script> -->shown",
    # Two tags whose text would reform a keyword if naively concatenated.
    "<b>scr</b><b>ipt</b>",
]


@pytest.mark.parametrize("payload", BYPASS_PAYLOADS)
def test_neutralize_resists_known_bypass_shapes(payload):
    out = neutralize(payload)
    assert "<" not in out and ">" not in out
    assert "javascript:" not in out.lower()
    assert "vbscript:" not in out.lower()
    assert "onerror" not in out.lower()
    assert "onmouseover" not in out.lower()
    assert is_neutralized(out)


def test_attribute_with_angle_bracket_does_not_leak_markup():
    # The '>' inside the attribute must not let the tokenizer emit markup.
    out = neutralize('<img src="a>b" onerror="x">keep')
    assert "keep" in out
    assert "onerror" not in out.lower()
    assert "<" not in out and ">" not in out


def test_active_element_body_fully_dropped_even_when_malformed():
    out = neutralize("before<script>secret_payload()")  # unterminated
    assert "secret_payload" not in out
    assert "before" in out


def test_ordinary_text_with_math_symbols_is_preserved_as_text():
    # Non-tag angle usage like "a < b and c > d" is math text, not markup. The
    # neutralizer errs safe (removes the bare delimiters) but keeps the words.
    out = neutralize("a < b and c > d")
    assert "<" not in out and ">" not in out
    assert "a" in out and "b" in out and "and" in out


# --- audit regression: malformed container regions & parser-limit cases ----

MALFORMED_CONTAINER_PAYLOADS = [
    # Unterminated comment hiding a script (HTMLParser leaves it incomplete).
    "<!-- <script>alert(1)</script>",
    # Bogus declaration swallowing a script start tag.
    "<!FOOBAR <script>alert(1)</script> >decl-tail",
    # CDATA wrapping a script.
    "<![CDATA[<script>alert(1)</script>]]>cdtext",
    # Conditional-comment style.
    "<!--[if IE]><script>alert(1)</script><![endif]-->visible",
    # Processing instruction.
    "<?xml echo('x') ?>pi-tail",
    # Unterminated style element.
    "intro<style>.x{color:red}",
    # Entity-encoded tag that only appears after decoding.
    "safe &lt;img src=x onerror=alert(1)&gt; done",
]


@pytest.mark.parametrize("payload", MALFORMED_CONTAINER_PAYLOADS)
def test_malformed_container_regions_leave_inert_output(payload):
    out = neutralize(payload)
    assert "<" not in out and ">" not in out
    assert "javascript:" not in out.lower()
    assert "vbscript:" not in out.lower()
    assert not re.search(r"(?i)\bon[a-z]+\s*=", out)
    assert is_neutralized(out)


def test_unterminated_comment_script_body_dropped():
    # Regression: previously the unterminated comment leaked "script alert(1)".
    out = neutralize("<!-- <script>alert(1)</script>")
    assert out == ""


def test_bogus_declaration_script_body_dropped():
    out = neutralize("<!FOOBAR <script>alert(1)</script> >decl-tail")
    assert "alert(1)" not in out
    assert "decl-tail" in out


def test_null_byte_in_tag_name_is_inert_text_only():
    # HTMLParser does not recognize "scri\x00pt" as the script tag; the body
    # may survive as INERT TEXT, but no executable markup/scheme/handler does.
    out = neutralize("<scri\x00pt>alert(1)</script>after")
    assert "<" not in out and ">" not in out
    assert "javascript:" not in out.lower()
    assert is_neutralized(out)
    assert "after" in out


def test_mismatched_nesting_leaves_only_inert_text():
    out = neutralize("<svg><script>bad()</svg>stillbad()</script>tail")
    assert "<" not in out and ">" not in out
    assert is_neutralized(out)
