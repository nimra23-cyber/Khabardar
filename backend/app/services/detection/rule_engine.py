"""Rule-based detection engine orchestrator (Task 2.6).

Composes the signal layer, the transparent scorer, and the pure classifier into
a single deterministic, local, explainable result. No network, no AI keys, no
persistence, no logging of the raw message.

Public API:
    evaluate(text) -> RuleBasedResult

The result is a validated Pydantic model carrying the integer Risk_Score, the
Classification band, the triggered signals with traceable evidence, a light
language hint, and the ruleset version. Category assignment, bilingual
explanations, confidence, and the persisted schema are OUT OF SCOPE for this
task (Task 2.9 / 2.13) and are intentionally not produced here.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from app.services.detection.classify import Classification, classify
from app.services.detection.scoring import score_signals
from app.services.detection.signals import SignalHit, detect_signals

# Bump when signal set / weights / matching change, so results are traceable to
# a ruleset. This is NOT a probability or accuracy claim.
RULESET_VERSION = "rules-2.6.0"

# Input bounds mirror Req 5.1/5.2 (1..10000 chars). The engine itself tolerates
# any string; the pipeline (Task 2.13) owns HTTP-level length rejection. We
# expose the constant so the pipeline can reuse it.
MAX_INPUT_CHARS = 10000

_URDU_RANGE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_LATIN_RANGE = re.compile(r"[A-Za-z]")


class TriggeredSignal(BaseModel):
    """One triggered signal in the result (validated)."""

    signal_id: str
    name: str
    explanation: str
    direction: str
    evidence: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    @field_validator("evidence")
    @classmethod
    def _non_empty_evidence(cls, v: list[str]) -> list[str]:
        # A triggered signal must carry at least one piece of evidence; this
        # enforces "never claim a signal without traceable evidence".
        if not v:
            raise ValueError("a triggered signal must include evidence")
        return v


# Stable, user-facing notice surfaced when the rule engine finds NO contributing
# signals. This makes the "no contributing signals detected" state EXPLICIT
# (Req 7.5) and ensures a SAFE band on an unrecognized message is accompanied by
# an honest statement that absence of evidence is NOT an assurance of safety
# (Req 5.11 -- "do not classify SAFE solely because no keyword was found").
NO_SIGNAL_NOTICE = (
    "No contributing scam signals were detected by the local rule engine. "
    "This reflects the absence of recognized indicators, not a guarantee that "
    "the message is safe."
)


class RuleBasedResult(BaseModel):
    """Deterministic rule-based detection result (Task 2.6 contract)."""

    risk_score: int = Field(ge=0, le=100)
    classification: Classification
    signals: list[TriggeredSignal] = Field(default_factory=list)
    detected_languages: list[str] = Field(default_factory=list)
    ruleset_version: str = RULESET_VERSION
    # Explicit no-signal state (Req 7.5 / 5.11). When True, no signal
    # contributed to the score; ``no_signal_notice`` carries the honest message
    # that this is absence-of-evidence, not an affirmative safety verdict.
    no_signals_detected: bool = False
    no_signal_notice: str | None = None

    @field_validator("classification")
    @classmethod
    def _classification_matches_score(cls, v, info):  # type: ignore[no-untyped-def]
        # Defensive invariant: classification must equal classify(score).
        score = info.data.get("risk_score")
        if score is not None and classify(int(score)) != v:
            raise ValueError("classification does not match risk_score band")
        return v

    @field_validator("no_signal_notice")
    @classmethod
    def _notice_matches_flag(cls, v, info):  # type: ignore[no-untyped-def]
        # Invariant: the notice is present IFF no_signals_detected is True, so
        # the explicit no-signal indication cannot drift from reality.
        flag = info.data.get("no_signals_detected")
        if flag and not v:
            raise ValueError("no_signal_notice required when no signals detected")
        if not flag and v:
            raise ValueError("no_signal_notice must be None when signals detected")
        return v


def _language_hint(text: str, hits: list[SignalHit]) -> list[str]:
    """Best-effort language hint (NOT the full detector in Task 2.9).

    Combines script detection (Urdu Unicode vs Latin) with the languages of the
    lexicons that actually matched. Returns a sorted, de-duplicated list; empty
    only for empty input.
    """
    langs: set[str] = set()
    if _URDU_RANGE.search(text):
        langs.add("ur")
    if _LATIN_RANGE.search(text):
        # Latin script could be English or Roman Urdu; refine using matched
        # lexicon languages when available.
        langs.add("en")
    for h in hits:
        langs.update(h.languages)
    # If Roman-Urdu lexicon matched, prefer to surface ur-Latn alongside en.
    return sorted(langs)


def evaluate(text: str) -> RuleBasedResult:
    """Run the rule-based engine on ``text`` and return a validated result.

    Deterministic and side-effect free: identical input yields an identical
    result. Safe on empty/malformed/Unicode input (returns a SAFE, zero-signal
    result for empty input rather than raising). Does NOT log the raw message,
    fetch URLs, or persist anything.
    """
    if not isinstance(text, str):
        text = "" if text is None else str(text)

    hits = detect_signals(text)
    triggered_ids = [h.signal_id for h in hits]
    score = score_signals(triggered_ids)
    classification = classify(score)

    signals = [
        TriggeredSignal(
            signal_id=h.signal_id,
            name=h.name,
            explanation=h.explanation,
            direction=h.direction,
            evidence=list(h.evidence),
            languages=list(h.languages),
        )
        for h in hits
    ]

    no_signals = not signals
    return RuleBasedResult(
        risk_score=score,
        classification=classification,
        signals=signals,
        detected_languages=_language_hint(text, hits),
        ruleset_version=RULESET_VERSION,
        no_signals_detected=no_signals,
        no_signal_notice=NO_SIGNAL_NOTICE if no_signals else None,
    )
