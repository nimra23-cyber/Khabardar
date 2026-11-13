"""Roman Urdu lexicon for rule-based detection (Task 2.6).

INITIAL, PARTIAL heuristic set. Roman Urdu has NO standard spelling, so this
list captures common variants (e.g. "karein"/"karen", "foran"/"fauran") but
cannot cover every transliteration. Coverage is explicitly incomplete
(Req 23 honesty). Terms are lower-case; matched over normalized lower Latin
text with word-ish boundaries.

Signal ids match ``signals.SIGNALS``.
"""

from __future__ import annotations

LEXICON: dict[str, list[str]] = {
    "urgency_threat": [
        "foran",
        "fauran",
        "abhi",
        "jaldi",
        "turant",
        "akhri warning",
        "akhri mauka",
        "warna",
    ],
    "account_suspension": [
        "account band",
        "account block",
        "account mautal",
        "account band ho jayega",
        "verify karein",
        "verify karen",
        "tasdeeq karein",
        "tasdeeq karen",
        "dobara activate",
    ],
    "otp_request": [
        "otp share kar",
        "otp bhejein",
        "otp bhejo",
        "otp batao",
        "otp batayein",
        "code bhejein",
        "code batao",
        "pin batao",
        "pin bhejo",
    ],
    "credential_request": [
        "password batao",
        "password bhejo",
        "atm pin",
        "card number",
        "shanakhti card number",
        "cnic number",
        "account number",
    ],
    "payment_demand": [
        "paise bhejein",
        "paise bhejo",
        "raqam bhejein",
        "fees ada karein",
        "payment karein",
        "jazzcash",
        "easypaisa",
        "transfer karein",
    ],
    "prize_lottery": [
        "aap jeet gaye",
        "inaam",
        "lottery",
        "qura andazi",
        "mubarak ho",
        "free tohfa",
        "cash prize",
    ],
    "authority_impersonation": [
        "state bank",
        "nadra",
        "fbr",
        "customs",
        "police",
        "adalat",
        "court",
        "courier",
    ],
    "suspicious_link": [
        "link par click",
        "yahan click",
        "link kholein",
        "login karein",
        "bit.ly",
        "tinyurl",
    ],
    "app_install": [
        "app install",
        "app download",
        "apk download",
        "file download",
        "anydesk",
        "teamviewer",
    ],
    "social_pressure": [
        "kisi ko na batayein",
        "kisi ko mat batao",
        "raaz rakhein",
        "sirf aap",
        "jaldi karein warna",
        "trust karein",
    ],
}

# Protective / negation cues in Roman Urdu. Near an otp/credential cue these
# make it a WARNING (e.g. "apna OTP kisi ko na batayein") rather than a request.
NEGATION_CUES: list[str] = [
    "na batayein",
    "na batao",
    "mat batao",
    "mat batayein",
    "na dein",
    "mat dein",
    "share na karein",
    "kisi ko na",
    "khabardar",
    "hoshiyar",
    "mehfooz rakhein",
]
