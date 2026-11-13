"""Classification: a pure function of the Risk_Score (Task 2.6, Req 5.4).

Bands (inclusive):
    0-39   -> SAFE
    40-69  -> SUSPICIOUS
    70-100 -> HIGH RISK

``classify`` is a pure function: it depends ONLY on the integer score and no
other state, so identical scores always map to identical classifications
(Property 2). The score is validated to be within 0..100.
"""

from __future__ import annotations

from typing import Literal

Classification = Literal["SAFE", "SUSPICIOUS", "HIGH RISK"]

SAFE_MAX = 39
SUSPICIOUS_MAX = 69
SCORE_MIN = 0
SCORE_MAX = 100


def classify(score: int) -> Classification:
    """Map an integer Risk_Score (0..100) to its Classification band.

    Raises ``ValueError`` if the score is out of range -- the engine clamps
    scores to 0..100 before calling this, so an out-of-range value indicates a
    programming error, not user input.
    """
    if not isinstance(score, int) or isinstance(score, bool):
        raise ValueError(f"score must be an int, got {type(score).__name__}")
    if score < SCORE_MIN or score > SCORE_MAX:
        raise ValueError(f"score out of range 0..100: {score}")
    if score <= SAFE_MAX:
        return "SAFE"
    if score <= SUSPICIOUS_MAX:
        return "SUSPICIOUS"
    return "HIGH RISK"
