"""Classification boundary tests (Task 2.6, Req 5.4)."""

from __future__ import annotations

import pytest

from app.services.detection.classify import classify


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "SAFE"),
        (1, "SAFE"),
        (39, "SAFE"),       # upper edge of SAFE
        (40, "SUSPICIOUS"),  # lower edge of SUSPICIOUS
        (69, "SUSPICIOUS"),  # upper edge of SUSPICIOUS
        (70, "HIGH RISK"),   # lower edge of HIGH RISK
        (100, "HIGH RISK"),
    ],
)
def test_classification_boundaries(score, expected):
    assert classify(score) == expected


def test_classify_is_pure_function_of_score():
    # Same score -> same class every time, independent of anything else.
    for s in range(0, 101):
        assert classify(s) == classify(s)


def test_classify_rejects_out_of_range():
    with pytest.raises(ValueError):
        classify(-1)
    with pytest.raises(ValueError):
        classify(101)


def test_classify_rejects_non_int():
    with pytest.raises(ValueError):
        classify(50.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        classify(True)  # bool is not an acceptable score
