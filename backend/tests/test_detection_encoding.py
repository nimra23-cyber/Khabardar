"""Urdu encoding integrity tests (Task 2.6 acceptance review, Issue 2).

These verify DATA correctness independent of any terminal display codepage:
* lexicon source files are UTF-8,
* Urdu lexicon strings load with the correct Unicode codepoints,
* correctly-encoded Urdu input triggers the intended signals,
* returned evidence is exactly a substring of the original input,
* Urdu negation does not trigger an OTP request (while a request does).

All assertions compare Python ``str`` objects / codepoints, so they pass or
fail based on real data, not on how a console renders the characters.
"""

from __future__ import annotations

import pathlib

from app.services.detection import evaluate
from app.services.detection.lexicons import ur
from app.services.detection.signals import detect_signals

_LEX_DIR = pathlib.Path(__file__).resolve().parent.parent / "app" / "services" / "detection" / "lexicons"


def test_lexicon_files_are_utf8():
    for name in ("ur.py", "en.py", "ur_latn.py"):
        raw = (_LEX_DIR / name).read_bytes()
        # Must decode as UTF-8 without error.
        raw.decode("utf-8")


def test_urdu_lexicon_term_has_expected_codepoints():
    # "اکاؤنٹ بند" (account blocked) -- assert exact Unicode scalar values so a
    # mojibake/re-encoding regression would be caught regardless of display.
    term = "اکاؤنٹ بند"
    assert term in ur.LEXICON["account_suspension"]
    expected_codepoints = [
        0x627, 0x6A9, 0x627, 0x624, 0x646, 0x679, 0x20, 0x628, 0x646, 0x62F
    ]
    assert [ord(ch) for ch in term] == expected_codepoints
    # Every character is in an Arabic/Urdu Unicode block (no cp1252 artefacts).
    for ch in term.replace(" ", ""):
        assert 0x0600 <= ord(ch) <= 0x06FF or 0xFB50 <= ord(ch) <= 0xFDFF


def test_urdu_scam_input_triggers_expected_signals():
    text = "آپ کا اکاؤنٹ بند ہو جائے گا، فوراً تصدیق کریں۔"
    ids = {h.signal_id for h in detect_signals(text)}
    assert "account_suspension" in ids
    assert "urgency_threat" in ids


def test_urdu_evidence_is_exact_substring_of_input():
    text = "آپ کا اکاؤنٹ بند ہو جائے گا، فوراً تصدیق کریں۔"
    hits = detect_signals(text)
    assert hits
    for h in hits:
        for ev in h.evidence:
            # Byte-for-byte: evidence must be a real substring of the input.
            assert ev in text
            assert text.find(ev) != -1


def test_urdu_negation_does_not_trigger_otp_request():
    warn = "اپنا او ٹی پی کسی کو نہ بتائیں۔"  # do NOT tell your OTP to anyone
    ids = {h.signal_id for h in detect_signals(warn)}
    assert "otp_request" not in ids


def test_urdu_request_does_trigger_otp_request():
    req = "اپنا او ٹی پی بھیجیں فوراً"  # send your OTP now
    ids = {h.signal_id for h in detect_signals(req)}
    assert "otp_request" in ids


def test_urdu_roundtrip_through_result_model_preserves_evidence():
    text = "آپ کا اکاؤنٹ بند ہو جائے گا، فوراً تصدیق کریں۔"
    r = evaluate(text)
    for s in r.signals:
        for ev in s.evidence:
            assert ev in text
