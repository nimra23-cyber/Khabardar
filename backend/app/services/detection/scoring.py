"""Transparent risk scoring for the rule-based engine (Task 2.6, Req 5.3).

The Risk_Score is a deterministic, bounded 0-100 aggregate of TRIGGERED signal
weights. It is a HEURISTIC score, not a calibrated probability of fraud
(Req 23). All weights below are PROVISIONAL initial values chosen by judgement,
to be calibrated against the evaluation dataset (Task 2.15 / Req 24) -- they are
NOT empirically validated.

Anti-inflation / anti-double-count design:

* Each signal contributes its weight AT MOST ONCE, regardless of how many
  keywords or how many times a keyword repeats in the message. (The signal
  layer already de-duplicates evidence; the scorer never multiplies by match
  count.) So repeating "urgent urgent urgent" cannot inflate the score.
* Strongly-overlapping signals are grouped; each GROUP contributes at most its
  ``group_cap`` so two near-synonymous signals don't double-count. E.g.
  ``otp_request`` and ``credential_request`` both express "give me your
  secret" -- together they are capped.
* Aggregation uses diminishing returns (probabilistic-OR style combination) so
  many weak signals accumulate but cannot trivially saturate to 100; the final
  value is clamped to [0, 100].
"""

from __future__ import annotations

from collections.abc import Iterable

# --- Provisional signal weights (0..100 "points"), with rationale ----------
# Higher = stronger standalone indicator of a scam. These are initial heuristics
# (Req 23); do not present as validated accuracy.
SIGNAL_WEIGHTS: dict[str, int] = {
    # Direct secret exfiltration is the strongest single indicator.
    "otp_request": 55,          # asking for an OTP is almost always malicious
    "credential_request": 50,   # asking for password/card/CNIC is near-certain
    # Money movement under pressure is a very strong indicator.
    "payment_demand": 40,
    # Account-suspension threats are a classic phishing hook.
    "account_suspension": 35,
    # Impersonating a bank/govt/courier lends false authority.
    "authority_impersonation": 30,
    # Prize/lottery is a common lure but also appears in benign marketing.
    "prize_lottery": 30,
    # Install/download requests (esp. remote-access tools like AnyDesk/
    # TeamViewer) are a hallmark of refund/support scams; a standalone request
    # should by itself reach SUSPICIOUS (>=40), so weight it at 45.
    "app_install": 45,
    # A link/"click here" alone is weakly suspicious (many benign msgs have
    # links); it mainly amplifies other signals.
    "suspicious_link": 18,
    # Generic urgency is weak on its own (benign reminders are urgent too).
    "urgency_threat": 18,
    # Secrecy/pressure tactics are moderately suspicious.
    "social_pressure": 22,
}

# Overlapping-signal groups with a per-group cap. A group's combined
# contribution is capped at ``cap`` so near-synonymous signals don't
# double-count. Signals not in any group contribute independently.
OVERLAP_GROUPS: list[dict] = [
    {
        "name": "secret_request",
        "members": ("otp_request", "credential_request"),
        # Capped slightly above the strongest member so having BOTH adds a
        # little, but not the full sum (55 + 50 = 105 would be excessive).
        "cap": 65,
    },
    {
        "name": "pressure",
        "members": ("urgency_threat", "social_pressure", "account_suspension"),
        "cap": 55,
    },
]

MIN_SCORE = 0
MAX_SCORE = 100


def _group_adjusted_weights(triggered: set[str]) -> list[int]:
    """Return the list of weight contributions after applying group caps.

    For each overlap group, sum the triggered members' weights and cap at the
    group's ``cap``; members handled by a group are excluded from the
    independent-contribution list. Remaining triggered signals contribute their
    full weight.
    """
    handled: set[str] = set()
    contributions: list[int] = []

    for group in OVERLAP_GROUPS:
        members = [m for m in group["members"] if m in triggered]
        if not members:
            continue
        raw = sum(SIGNAL_WEIGHTS.get(m, 0) for m in members)
        contributions.append(min(raw, int(group["cap"])))
        handled.update(members)

    for sig in triggered:
        if sig in handled:
            continue
        contributions.append(SIGNAL_WEIGHTS.get(sig, 0))

    return contributions


def _combine_diminishing(contributions: Iterable[int]) -> int:
    """Combine point contributions with diminishing returns, then clamp.

    We treat each contribution ``w`` as a pseudo-probability ``w/100`` and
    combine via probabilistic OR: ``1 - prod(1 - w_i/100)``. This is monotonic
    (adding a signal never lowers the score), order-independent (deterministic),
    naturally bounded in [0, 100), and gives diminishing returns so stacking
    many weak signals can't trivially hit 100 while strong signals still push
    high. The result is rounded to an int and clamped to [0, 100].
    """
    remaining = 1.0
    for w in contributions:
        w = max(0, min(100, int(w)))
        remaining *= (1.0 - w / 100.0)
    score = round((1.0 - remaining) * 100)
    return max(MIN_SCORE, min(MAX_SCORE, int(score)))


def score_signals(triggered_signal_ids: Iterable[str]) -> int:
    """Compute the integer Risk_Score (0..100) for the triggered signal ids.

    Deterministic: identical input sets yield identical scores. Unknown ids are
    ignored (weight 0). No side effects.
    """
    triggered = {s for s in triggered_signal_ids if s in SIGNAL_WEIGHTS}
    if not triggered:
        return 0
    contributions = _group_adjusted_weights(triggered)
    return _combine_diminishing(contributions)
