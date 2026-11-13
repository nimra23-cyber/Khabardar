"""Signal definitions and context-sensitive matching (Task 2.6, Req 7.1/7.2).

A *signal* is one explainable scam indicator (e.g. "otp_request"). Each
evaluated signal is recorded as EITHER triggered (with the exact evidence
extracted from the input and its contribution direction) OR not detected --
this is the explainability backbone from the design.

Matching is deterministic and local:

* The input is normalized to lower-case Latin for English / Roman-Urdu term
  matching, with a parallel index map so matched spans map back to the ORIGINAL
  text (evidence is always a real substring of the input -- never fabricated).
* Urdu Unicode terms are matched as substrings over the original text.
* ``otp_request`` and ``credential_request`` are NEGATION-AWARE: if a protective
  cue ("never share your OTP", "kisi ko na batayein", "کسی کو نہ بتائیں")
  appears in the message, those request signals are NOT triggered -- a warning
  against sharing is not a request to share.

No network, no persistence, no logging of the raw message happens here.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from app.services.detection.lexicons import en, ur, ur_latn

# All signal ids with human-readable name + explanation + contribution
# direction. "increases" = raises risk; this engine has no risk-decreasing
# signals (absence-of-safety: lack of a scam cue is NOT positive safety).
SIGNALS: dict[str, dict[str, str]] = {
    "urgency_threat": {
        "name": "Urgency / threatening language",
        "explanation": "Language pressuring the reader to act immediately or face a consequence.",
        "direction": "increases",
    },
    "account_suspension": {
        "name": "Account suspension / verification threat",
        "explanation": "Claims an account will be blocked/suspended unless the reader verifies or acts now.",
        "direction": "increases",
    },
    "otp_request": {
        "name": "OTP / verification code request",
        "explanation": "Asks the reader to share a one-time password, PIN, or verification code.",
        "direction": "increases",
    },
    "credential_request": {
        "name": "Credential / sensitive data request",
        "explanation": "Asks for passwords, card/CNIC/account details, or other sensitive credentials.",
        "direction": "increases",
    },
    "payment_demand": {
        "name": "Suspicious payment demand",
        "explanation": "Requests a transfer, fee, or payment, often via JazzCash/Easypaisa/bank transfer.",
        "direction": "increases",
    },
    "prize_lottery": {
        "name": "Prize / lottery / unexpected reward",
        "explanation": "Claims the reader has won a prize, lottery, giveaway, or unexpected reward.",
        "direction": "increases",
    },
    "authority_impersonation": {
        "name": "Authority / brand impersonation",
        "explanation": "Impersonates a bank, government body, courier, or other trusted organization.",
        "direction": "increases",
    },
    "suspicious_link": {
        "name": "Suspicious link indicator",
        "explanation": "Contains a link, shortener, or 'click here' prompt typical of phishing (not fetched).",
        "direction": "increases",
    },
    "app_install": {
        "name": "App install / file download request",
        "explanation": "Asks the reader to install an app/APK or download a file (e.g. remote-access tools).",
        "direction": "increases",
    },
    "social_pressure": {
        "name": "Social engineering / pressure tactic",
        "explanation": "Uses secrecy, exclusivity, or pressure to manipulate the reader.",
        "direction": "increases",
    },
}

# Signals that are protective-context sensitive (a warning != a request).
_NEGATION_SENSITIVE = frozenset({"otp_request", "credential_request"})

_LANG_LEXICONS = {
    "en": (en.LEXICON, en.NEGATION_CUES, "latin"),
    "ur-Latn": (ur_latn.LEXICON, ur_latn.NEGATION_CUES, "latin"),
    "ur": (ur.LEXICON, ur.NEGATION_CUES, "unicode"),
}

_MAX_EVIDENCE_ITEMS = 5  # cap evidence per signal (privacy / bounded output)


@dataclass(frozen=True)
class SignalHit:
    """A triggered signal with traceable evidence."""

    signal_id: str
    name: str
    explanation: str
    direction: str
    evidence: tuple[str, ...]
    languages: tuple[str, ...]


@dataclass
class _Accumulator:
    """Internal per-signal evidence collector during evaluation."""

    evidence: list[str] = field(default_factory=list)
    languages: set[str] = field(default_factory=set)


def _normalize_latin(text: str) -> str:
    """Lower-case + NFKC-normalize for Latin matching, preserving length-ish
    structure. We DO NOT use this for evidence extraction (we extract from the
    original text); it is only the haystack for case-insensitive matching.
    """
    return unicodedata.normalize("NFKC", text).lower()


def _find_latin_terms(original: str, haystack_lower: str, terms: list[str]) -> list[str]:
    """Return original-text evidence substrings for each matched Latin term.

    Matching is done on the lower-cased haystack with word-ish boundaries so a
    term like "otp" does not match inside "cryptops". Evidence is sliced from
    the ORIGINAL text at the same offset (NFKC lower preserves offsets for the
    ASCII-ish scam vocabulary we match; non-ASCII Latin is rare here).
    """
    hits: list[str] = []
    for term in terms:
        t = term.lower()
        # Word-ish boundary: term not flanked by [a-z0-9]. Allows spaces/punct
        # inside multi-word terms. Escape regex metacharacters in the term.
        pattern = re.compile(
            r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])"
        )
        for m in pattern.finditer(haystack_lower):
            start, end = m.start(), m.end()
            # Map back to original text (same offsets under NFKC-lower for our
            # vocabulary); fall back to the term if offsets drift.
            snippet = original[start:end]
            hits.append(snippet if snippet.strip() else term)
            if len(hits) >= _MAX_EVIDENCE_ITEMS:
                return hits
    return hits


def _find_unicode_terms(original: str, terms: list[str]) -> list[str]:
    """Return evidence substrings for Urdu terms matched as substrings."""
    hits: list[str] = []
    for term in terms:
        idx = original.find(term)
        if idx != -1:
            hits.append(term)
            if len(hits) >= _MAX_EVIDENCE_ITEMS:
                return hits
    return hits


def _has_negation(original: str, haystack_lower: str, cues: list[str], mode: str) -> bool:
    for cue in cues:
        if mode == "unicode":
            if cue in original:
                return True
        else:
            if cue.lower() in haystack_lower:
                return True
    return False


def detect_signals(text: str) -> list[SignalHit]:
    """Evaluate every signal against ``text`` and return the TRIGGERED ones.

    Deterministic and side-effect free. Evidence is always a real substring of
    the input. Negation-sensitive request signals are suppressed when a
    protective cue is present in the same message.
    """
    if not isinstance(text, str) or not text:
        return []

    haystack_lower = _normalize_latin(text)

    # Determine which negation modes are active anywhere in the message.
    negation_active = False
    for _lang, (_lex, cues, mode) in _LANG_LEXICONS.items():
        if _has_negation(text, haystack_lower, cues, mode):
            negation_active = True
            break

    acc: dict[str, _Accumulator] = {}

    for lang, (lexicon, _cues, mode) in _LANG_LEXICONS.items():
        for signal_id, terms in lexicon.items():
            if mode == "unicode":
                found = _find_unicode_terms(text, terms)
            else:
                found = _find_latin_terms(text, haystack_lower, terms)
            if not found:
                continue
            bucket = acc.setdefault(signal_id, _Accumulator())
            for ev in found:
                if ev not in bucket.evidence and len(bucket.evidence) < _MAX_EVIDENCE_ITEMS:
                    bucket.evidence.append(ev)
            bucket.languages.add(lang)

    hits: list[SignalHit] = []
    for signal_id in SIGNALS:  # stable, deterministic order
        bucket = acc.get(signal_id)
        if bucket is None or not bucket.evidence:
            continue
        # Negation-aware suppression for request-type signals.
        if signal_id in _NEGATION_SENSITIVE and negation_active:
            continue
        meta = SIGNALS[signal_id]
        hits.append(
            SignalHit(
                signal_id=signal_id,
                name=meta["name"],
                explanation=meta["explanation"],
                direction=meta["direction"],
                evidence=tuple(bucket.evidence),
                languages=tuple(sorted(bucket.languages)),
            )
        )
    return hits
