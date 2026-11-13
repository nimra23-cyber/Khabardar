"""No-signal / absence-of-evidence behavior (Task 2.6, Req 5.11 & 7.5).

Req 7.5: when no detection signals are found, the result must present an
EXPLICIT indication that no contributing signals were detected.

Req 5.11 (MVP-AC-4): a message must NOT be treated as SAFE *solely* because no
keyword matched. The engine keeps SAFE as the honest score band but attaches an
explicit ``no_signals_detected`` flag + ``no_signal_notice`` so a caller (and
the user) can distinguish LOW DETECTED RISK from INSUFFICIENT DETECTION
EVIDENCE. The classification remains a pure function of the score (no fourth
class is introduced, which the spec does not permit).
"""

from __future__ import annotations

import pytest

from app.services.detection import NO_SIGNAL_NOTICE, evaluate


NO_SIGNAL_INPUTS = [
    ("", "empty string"),
    ("   ", "whitespace only"),
    ("\t\n  \r", "mixed whitespace"),
    ("Hi, are we meeting for lunch tomorrow?", "benign familiar message"),
    ("The quarterly report is attached for review.", "benign work message"),
    ("asdkfj qweoiru zxcmnv lkjhgf", "unfamiliar/unrecognized gibberish"),
    ("語 لا 123 %%% ***", "unrecognized mixed unicode/symbols"),
]


@pytest.mark.parametrize("text,reason", NO_SIGNAL_INPUTS)
def test_no_signal_state_is_explicit(text, reason):
    r = evaluate(text)
    # No signals triggered.
    assert r.signals == [], reason
    # The no-signal state is EXPLICIT (Req 7.5), not merely an empty list.
    assert r.no_signals_detected is True, reason
    assert r.no_signal_notice == NO_SIGNAL_NOTICE, reason


@pytest.mark.parametrize("text,reason", NO_SIGNAL_INPUTS)
def test_no_signal_notice_states_absence_not_safety(text, reason):
    r = evaluate(text)
    notice = r.no_signal_notice or ""
    # The notice must convey "absence of evidence, not a guarantee of safety"
    # so a SAFE band is not read as an affirmative safety verdict (Req 5.11).
    assert "not a guarantee" in notice.lower()
    assert "absence" in notice.lower()


def test_no_signal_score_band_is_still_safe_but_flagged():
    # SAFE remains the honest band for score 0 (classification is a pure
    # function of score), but the explicit flag prevents false assurance.
    r = evaluate("Hello there, hope you are well.")
    assert r.risk_score == 0
    assert r.classification == "SAFE"
    assert r.no_signals_detected is True


def test_triggered_signal_clears_no_signal_state():
    r = evaluate("Share your OTP now to verify your blocked account.")
    assert r.signals  # at least one signal
    assert r.no_signals_detected is False
    assert r.no_signal_notice is None


def test_low_risk_with_signal_is_not_no_signal_state():
    # A single weak signal yields a low (SAFE-band) score but is NOT the
    # no-signal state: detected low risk != insufficient evidence.
    r = evaluate("urgent")  # urgency_threat weight 18 -> score 18, SAFE band
    assert r.classification == "SAFE"
    assert r.signals  # urgency_threat triggered
    assert r.no_signals_detected is False
    assert r.no_signal_notice is None


def test_result_model_rejects_inconsistent_no_signal_fields():
    # The model invariant: notice present IFF no_signals_detected True.
    from app.services.detection.rule_engine import RuleBasedResult

    with pytest.raises(Exception):
        RuleBasedResult(
            risk_score=0,
            classification="SAFE",
            signals=[],
            no_signals_detected=True,
            no_signal_notice=None,  # missing notice -> invalid
        )
    with pytest.raises(Exception):
        RuleBasedResult(
            risk_score=0,
            classification="SAFE",
            signals=[],
            no_signals_detected=False,
            no_signal_notice="should not be here",  # notice without flag
        )
