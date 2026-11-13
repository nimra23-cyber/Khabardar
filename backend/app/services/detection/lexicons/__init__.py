"""Language-specific lexicons for the rule-based detection engine (Task 2.6).

Each lexicon module exposes keyword/phrase lists grouped by SIGNAL ID. Lists are
hand-authored and documented; they are an INITIAL heuristic set, NOT an
exhaustive or empirically-validated corpus (Req 23 honesty). Coverage for Urdu
and Roman Urdu is partial and documented as such in the module docstrings.

Matching semantics (see ``signals.py``):
* English / Roman Urdu terms match on word-ish boundaries over normalized
  lower-cased Latin text.
* Urdu terms match as substrings over the original Unicode text (Urdu has no
  ASCII word boundaries).
"""

from app.services.detection.lexicons import en, ur, ur_latn

# Registry consumed by signals.py. Order is irrelevant; matching is set-based.
LEXICONS = {
    "en": en.LEXICON,
    "ur": ur.LEXICON,
    "ur-Latn": ur_latn.LEXICON,
}

__all__ = ["LEXICONS", "en", "ur", "ur_latn"]
