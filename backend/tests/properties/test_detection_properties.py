"""Property-based tests for the rule-based engine (Task 2.6).

Covers (min 100 iterations each):
* Risk_Score is always an int in 0..100 for ANY input  (Property 1, Req 5.3).
* Classification is a pure function of the score         (Property 2, Req 5.4).
* The engine is deterministic for identical input.
* Duplicate-keyword repetition never inflates the score.

These exercise the REAL engine over randomized inputs, not mocks.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.detection import evaluate
from app.services.detection.classify import classify
from app.services.detection.scoring import SIGNAL_WEIGHTS, score_signals

PROPERTY_TAG = "Feature: khabardar-platform, Property 1/2 (rule engine)"
MIN_ITERATIONS = 100

# A text strategy mixing arbitrary unicode with real scam vocabulary so the
# engine's matching paths are actually exercised (not just random noise).
_VOCAB = [
    "otp",
    "share your otp",
    "password",
    "account band",
    "verify karein",
    "فوراً",
    "تصدیق کریں",
    "lottery",
    "jazzcash",
    "click here",
    "install anydesk",
    "never share",
    "hello",
    "lunch",
]

_text = st.one_of(
    st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=0, max_size=300),
    st.lists(st.sampled_from(_VOCAB), min_size=0, max_size=12).map(lambda xs: " ".join(xs)),
)


@settings(max_examples=MIN_ITERATIONS)
@given(text=_text)
def test_property_risk_score_bounds(text):
    r = evaluate(text)
    assert isinstance(r.risk_score, int)
    assert 0 <= r.risk_score <= 100


@settings(max_examples=MIN_ITERATIONS)
@given(text=_text)
def test_property_classification_is_pure_function_of_score(text):
    r = evaluate(text)
    # Classification must equal the pure classifier applied to the score.
    assert r.classification == classify(r.risk_score)


@settings(max_examples=MIN_ITERATIONS)
@given(text=_text)
def test_property_engine_is_deterministic(text):
    a = evaluate(text).model_dump()
    b = evaluate(text).model_dump()
    assert a == b


@settings(max_examples=MIN_ITERATIONS)
@given(
    ids=st.lists(st.sampled_from(sorted(SIGNAL_WEIGHTS)), min_size=0, max_size=10),
    reps=st.integers(min_value=1, max_value=8),
)
def test_property_duplicates_do_not_inflate(ids, reps):
    once = score_signals(ids)
    many = score_signals(ids * reps)
    assert once == many
    assert 0 <= once <= 100


@settings(max_examples=MIN_ITERATIONS)
@given(ids=st.lists(st.sampled_from(sorted(SIGNAL_WEIGHTS)), min_size=0, max_size=10))
def test_property_score_order_independent(ids):
    import random

    shuffled = list(ids)
    random.Random(12345).shuffle(shuffled)
    assert score_signals(ids) == score_signals(shuffled)
