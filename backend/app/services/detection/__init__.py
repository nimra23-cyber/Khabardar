"""Rule-based scam detection engine (Task 2.6).

Deterministic, explainable, fully local detection: no external API keys, no
cloud LLMs, no network access at runtime. Validates Req 5.3 (0-100 score),
5.4 (classification bands), 5.11 (absence-of-safety), 7.1/7.2 (explainable
signal evaluation).

Public entry point: ``rule_engine.evaluate(text) -> RuleBasedResult``.
"""

from app.services.detection.rule_engine import (
    NO_SIGNAL_NOTICE,
    RULESET_VERSION,
    evaluate,
)

__all__ = ["evaluate", "RULESET_VERSION", "NO_SIGNAL_NOTICE"]
