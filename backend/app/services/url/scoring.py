"""Transparent URL risk scoring (Req 9.7).

Combines triggered indicator weights into a bounded 0-100 score using the same
diminishing-returns (probabilistic-OR) combiner as the text engine, so many
weak indicators accumulate without trivially saturating, and the result is
always within [0, 100]. Deterministic. Weights are PROVISIONAL heuristics
(Req 23), not calibrated probabilities.
"""

from __future__ import annotations

from collections.abc import Iterable

MIN_SCORE = 0
MAX_SCORE = 100


def score_url_indicators(indicators: Iterable[dict]) -> int:
    remaining = 1.0
    for ind in indicators:
        w = max(0, min(100, int(ind.get("weight", 0))))
        remaining *= 1.0 - w / 100.0
    score = round((1.0 - remaining) * 100)
    return max(MIN_SCORE, min(MAX_SCORE, int(score)))
