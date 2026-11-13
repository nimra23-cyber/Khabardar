"""Rule-based engine integration tests (Task 2.6).

Covers the result contract, determinism, multilingual handling, evidence
traceability, the no-signal explicit state, privacy behavior, and a labeled
DEVELOPMENT evaluation fixture with a confusion-matrix summary.

NOTE on the fixture (honesty / Req 23): the inline ``DEV_FIXTURE`` below is a
small, hand-written DEVELOPMENT set used to sanity-check behavior while the
rules were authored. It is NOT the formal >=100-example evaluation dataset
(that is Task 2.15) and its metrics are NOT independent validation -- the rules
were written with these shapes in mind. We report the confusion matrix only to
make current behavior transparent, never as an accuracy claim.
"""

from __future__ import annotations

import pytest

from app.services.detection import RULESET_VERSION, evaluate
from app.services.detection.rule_engine import RuleBasedResult


def test_result_contract_shape():
    r = evaluate("Share your OTP to verify your blocked account immediately.")
    assert isinstance(r, RuleBasedResult)
    assert 0 <= r.risk_score <= 100
    assert r.classification in ("SAFE", "SUSPICIOUS", "HIGH RISK")
    assert r.ruleset_version == RULESET_VERSION
    assert all(s.evidence for s in r.signals)  # every signal carries evidence


def test_known_scam_returns_signal_and_nonzero_score():
    r = evaluate(
        "Congratulations! You won a lottery. Pay the clearance fee via JazzCash "
        "now or your prize expires today."
    )
    assert r.risk_score > 0
    assert len(r.signals) >= 1
    ids = {s.signal_id for s in r.signals}
    assert "prize_lottery" in ids and "payment_demand" in ids


def test_benign_message_has_no_signals_and_is_safe():
    r = evaluate("Hi, can we reschedule our meeting to 3pm tomorrow?")
    assert r.signals == []
    assert r.classification == "SAFE"
    assert r.risk_score == 0


def test_determinism_same_input_same_result():
    text = "Apka account band ho jayega, foran verify karein. Click link."
    a = evaluate(text).model_dump()
    b = evaluate(text).model_dump()
    assert a == b


def test_classification_matches_score_invariant():
    # The model validator enforces classify(score) == classification.
    for text in [
        "",
        "urgent",
        "share your otp now",
        "you won a prize, pay fee via jazzcash, share your otp and password now",
    ]:
        r = evaluate(text)
        from app.services.detection.classify import classify

        assert r.classification == classify(r.risk_score)


def test_multilingual_results():
    en = evaluate("Your account will be blocked. Verify immediately.")
    roman = evaluate("Apka account band ho jayega, foran verify karein.")
    urdu = evaluate("آپ کا اکاؤنٹ بند ہو جائے گا، فوراً تصدیق کریں۔")
    for r in (en, roman, urdu):
        assert r.classification in ("SUSPICIOUS", "HIGH RISK")
        assert any(s.signal_id == "account_suspension" for s in r.signals)


def test_otp_request_vs_protective_warning_scores_differ():
    request = evaluate("Apna OTP share kar dein abhi.")
    warning = evaluate("اپنا او ٹی پی کسی کو نہ بتائیں۔")
    assert any(s.signal_id == "otp_request" for s in request.signals)
    assert not any(s.signal_id == "otp_request" for s in warning.signals)
    assert request.risk_score > warning.risk_score


def test_privacy_engine_does_not_log_raw_message(caplog):
    import logging

    secret = "my-OTP-is-918273-password-topsecret"
    with caplog.at_level(logging.DEBUG):
        evaluate(f"Please share {secret} now")
    # The engine must not emit the raw message to logs.
    assert secret not in caplog.text
    assert "918273" not in caplog.text


def test_evidence_is_bounded():
    # Flooding one signal's keyword does not produce unbounded evidence.
    r = evaluate("urgent " * 50)
    for s in r.signals:
        assert len(s.evidence) <= 5


# --- labeled DEVELOPMENT fixture + confusion matrix (not formal eval) -------

# label is binary scam/benign for metric purposes. Mapping (documented): SAFE
# -> predicted benign; SUSPICIOUS or HIGH RISK -> predicted scam.
DEV_FIXTURE = [
    # (text, expected_label, reason)
    ("Hi, lunch tomorrow at 1pm?", "benign", "ordinary plan, no indicators"),
    ("Please find attached the quarterly report.", "benign", "normal work msg"),
    ("Your parcel is out for delivery today.", "benign", "benign delivery note"),
    ("Never share your OTP with anyone.", "benign", "protective advice"),
    ("اپنا او ٹی پی کسی کو نہ بتائیں۔", "benign", "Urdu protective OTP warning"),
    ("Meeting notes are in the shared drive.", "benign", "benign"),
    ("Happy birthday! See you at the party.", "benign", "benign"),
    ("The cryptops library build passed.", "benign", "keyword-in-word false-positive bait"),
    ("Share your OTP to verify your account now.", "scam", "OTP request + urgency"),
    ("Apka account band ho jayega, foran verify karein.", "scam", "Roman Urdu suspension"),
    ("آپ کا اکاؤنٹ بند ہو جائے گا، فوراً تصدیق کریں۔", "scam", "Urdu suspension threat"),
    ("You won a lottery! Pay the fee via JazzCash to claim.", "scam", "prize + payment"),
    ("Enter your password and ATM PIN to reactivate.", "scam", "credential request"),
    ("Install AnyDesk so we can process your refund.", "scam", "remote-access install"),
    ("Final notice: transfer the clearance fee immediately.", "scam", "urgency + payment"),
    ("State Bank: your account is suspended, click the link to verify.", "scam", "impersonation + link"),
]


def _predict_label(text: str) -> str:
    r = evaluate(text)
    return "benign" if r.classification == "SAFE" else "scam"


def test_dev_fixture_confusion_matrix(capsys):
    tp = tn = fp = fn = 0
    mistakes = []
    for text, expected, _reason in DEV_FIXTURE:
        pred = _predict_label(text)
        if expected == "scam" and pred == "scam":
            tp += 1
        elif expected == "benign" and pred == "benign":
            tn += 1
        elif expected == "benign" and pred == "scam":
            fp += 1
            mistakes.append(("FP", text))
        else:
            fn += 1
            mistakes.append(("FN", text))

    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    # Emit the summary so it appears with `pytest -s`.
    print(
        f"\n[DEV FIXTURE -- not formal eval] n={total} "
        f"TP={tp} TN={tn} FP={fp} FN={fn} "
        f"precision={precision:.2f} recall={recall:.2f} f1={f1:.2f} "
        f"mistakes={mistakes}"
    )

    # Behavior assertions: on this development fixture the engine must make no
    # mistakes (it was authored against these shapes). This guards regressions,
    # not real-world accuracy.
    assert fp == 0, f"false positives: {mistakes}"
    assert fn == 0, f"false negatives: {mistakes}"
