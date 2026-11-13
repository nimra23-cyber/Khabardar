"""Signal detection tests (Task 2.6, Req 7.1/7.2): per-signal, multilingual,
negation/protective context, evidence traceability, malformed input."""

from __future__ import annotations

import pytest

from app.services.detection.signals import SIGNALS, detect_signals


def _ids(text):
    return {h.signal_id for h in detect_signals(text)}


# --- individual signals (English) ------------------------------------------


def test_urgency_signal():
    assert "urgency_threat" in _ids("Please act now, this is urgent!")


def test_account_suspension_signal():
    assert "account_suspension" in _ids("Your account will be blocked today.")


def test_otp_request_signal():
    assert "otp_request" in _ids("Please share your OTP to continue.")


def test_credential_request_signal():
    assert "credential_request" in _ids("Enter your password and card number.")


def test_payment_demand_signal():
    assert "payment_demand" in _ids("Pay the processing fee via JazzCash.")


def test_prize_lottery_signal():
    assert "prize_lottery" in _ids("Congratulations, you have won a prize!")


def test_authority_impersonation_signal():
    assert "authority_impersonation" in _ids("This is a notice from State Bank.")


def test_suspicious_link_signal():
    assert "suspicious_link" in _ids("Click here to verify: http://x.example")


def test_app_install_signal():
    assert "app_install" in _ids("Please install AnyDesk to receive your refund.")


def test_social_pressure_signal():
    assert "social_pressure" in _ids("Do not tell anyone, only you are selected.")


# --- multilingual ----------------------------------------------------------


def test_roman_urdu_account_suspension():
    assert "account_suspension" in _ids("Apka account band ho jayega, verify karein.")


def test_urdu_account_suspension():
    assert "account_suspension" in _ids("آپ کا اکاؤنٹ بند ہو جائے گا، تصدیق کریں۔")


def test_mixed_language_message():
    ids = _ids("Apka account band hoga. فوراً verify karein.")
    assert "account_suspension" in ids
    assert "urgency_threat" in ids  # 'فوراً' (ur) or 'foran' etc.


# --- negation / protective context (the key requirement) -------------------


def test_otp_request_vs_protective_warning_differ():
    request = _ids("Apna OTP share kar dein.")
    warning = _ids("Apna OTP kisi ko na batayein, yeh fraud hai.")
    assert "otp_request" in request
    assert "otp_request" not in warning  # protective advice, not a request


def test_english_protective_otp_warning_not_flagged_as_request():
    assert "otp_request" not in _ids("Never share your OTP with anyone.")


def test_urdu_protective_otp_warning_not_flagged_as_request():
    # "اپنا او ٹی پی کسی کو نہ بتائیں" = do NOT tell your OTP to anyone.
    assert "otp_request" not in _ids("اپنا او ٹی پی کسی کو نہ بتائیں۔")


def test_credential_request_suppressed_by_negation():
    assert "credential_request" not in _ids(
        "Our bank will never ask you to share your password."
    )


# --- evidence traceability -------------------------------------------------


def test_evidence_is_substring_of_input():
    text = "Please share your OTP and pay the processing fee urgently."
    for hit in detect_signals(text):
        for ev in hit.evidence:
            # Evidence must be traceable: it appears in the original input
            # (case-insensitively for Latin matches).
            assert ev.lower() in text.lower() or ev in text


def test_no_signal_has_empty_evidence_when_triggered():
    for hit in detect_signals("You won a lottery, send fee via Easypaisa now."):
        assert len(hit.evidence) >= 1


def test_signal_metadata_is_complete():
    for hit in detect_signals("Share your OTP now."):
        assert hit.signal_id in SIGNALS
        assert hit.name and hit.explanation and hit.direction


# --- malformed / unicode / benign ------------------------------------------


def test_empty_and_none_input():
    assert detect_signals("") == []
    assert detect_signals(None) == []  # type: ignore[arg-type]


def test_benign_message_triggers_nothing():
    assert detect_signals("Are we meeting for lunch tomorrow?") == []


def test_control_chars_and_emoji_do_not_crash():
    hits = detect_signals("share your otp \x00\x01 now 🚨")
    assert "otp_request" in {h.signal_id for h in hits}


def test_keyword_not_matched_inside_larger_word():
    # 'otp' should not match inside an unrelated longer token.
    assert "otp_request" not in _ids("The cryptops library is unrelated.")
