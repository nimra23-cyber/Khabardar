"""Scoring tests (Task 2.6, Req 5.3): bounds, determinism, anti-inflation,
overlap caps."""

from __future__ import annotations

from app.services.detection.scoring import (
    MAX_SCORE,
    MIN_SCORE,
    SIGNAL_WEIGHTS,
    score_signals,
)


def test_empty_signals_score_zero():
    assert score_signals([]) == 0
    assert score_signals(["unknown_signal"]) == 0


def test_score_is_bounded_0_100():
    # All signals triggered -> still within [0, 100].
    s = score_signals(list(SIGNAL_WEIGHTS))
    assert MIN_SCORE <= s <= MAX_SCORE


def test_scoring_is_deterministic_and_order_independent():
    a = score_signals(["otp_request", "urgency_threat"])
    b = score_signals(["urgency_threat", "otp_request"])
    c = score_signals(["otp_request", "urgency_threat"])
    assert a == b == c


def test_duplicate_ids_do_not_inflate_score():
    once = score_signals(["urgency_threat"])
    many = score_signals(["urgency_threat"] * 10)
    assert once == many


def test_adding_a_signal_never_lowers_score_monotonic():
    base = score_signals(["urgency_threat"])
    more = score_signals(["urgency_threat", "prize_lottery"])
    assert more >= base


def test_overlap_group_cap_prevents_double_counting():
    # otp_request (55) + credential_request (50) are capped at 65 as a group,
    # so their combined contribution is far below the naive sum.
    otp = score_signals(["otp_request"])
    both = score_signals(["otp_request", "credential_request"])
    # Both should exceed OTP alone (cap 65 > 55) but not reach the ~78 that an
    # uncapped 55+50 probabilistic-OR would give.
    assert both > otp
    # Uncapped combine of 55 and 50: 1-(0.45*0.50)=0.775 -> 78. Capped single
    # 65 -> 65. Assert we are at the capped value, not the inflated one.
    assert both == 65


def test_strong_single_signal_scores_high_enough_to_be_suspicious():
    # An OTP request alone should land at least in SUSPICIOUS territory.
    assert score_signals(["otp_request"]) >= 40


def test_many_weak_signals_accumulate_but_stay_bounded():
    weak = ["urgency_threat", "suspicious_link", "social_pressure"]
    s = score_signals(weak)
    assert 0 < s <= 100
