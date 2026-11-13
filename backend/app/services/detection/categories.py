"""Scam category assignment from triggered signals (Task 2.9, Req 5.5/6).

Maps the dominant triggered signal(s) to a scam category. Non-SAFE results with
no specific category are labeled ``"uncategorized"`` (Req 6.7). A SAFE result
with no signals has category ``None`` (the no-signal state is surfaced
separately by the engine).

Category assignment is deterministic and local; it does not add new detection,
it only labels what the signal layer already found.
"""

from __future__ import annotations

from app.services.detection.classify import Classification

# Priority-ordered mapping: the FIRST signal (by this order) present in the
# triggered set determines the category. Ordering reflects how diagnostic each
# signal is of a specific scam category.
_SIGNAL_TO_CATEGORY: list[tuple[str, str]] = [
    ("otp_request", "otp_theft"),
    ("credential_request", "phishing"),
    ("prize_lottery", "prize_or_lottery"),
    ("payment_demand", "advance_fee_or_payment"),
    ("app_install", "remote_access_or_malware"),
    ("account_suspension", "account_takeover"),
    ("authority_impersonation", "identity_impersonation"),
    ("suspicious_link", "phishing"),
    ("social_pressure", "social_engineering"),
    ("urgency_threat", "social_engineering"),
]

UNCATEGORIZED = "uncategorized"


def assign_category(
    triggered_signal_ids: list[str], classification: Classification
) -> str | None:
    """Return a scam category for the result.

    * SAFE with no signals -> ``None`` (no category to assign).
    * Non-SAFE (SUSPICIOUS/HIGH RISK) with recognizable signals -> mapped
      category; if none maps, ``"uncategorized"`` (Req 6.7).
    * SAFE but with a weak signal present -> best-effort mapped category so the
      user still sees why it was flagged at all.
    """
    triggered = set(triggered_signal_ids)
    for signal_id, category in _SIGNAL_TO_CATEGORY:
        if signal_id in triggered:
            return category
    if classification != "SAFE":
        # Non-SAFE but no mappable signal: never omit the category (Req 6.7).
        return UNCATEGORIZED
    return None
