"""Urdu (Unicode) lexicon for rule-based detection (Task 2.6).

INITIAL, PARTIAL heuristic set. Urdu coverage is deliberately limited to common
scam phrasings and is NOT exhaustive (Req 23 honesty). Terms are matched as
SUBSTRINGS over the original Urdu Unicode text (Urdu script has no ASCII word
boundaries). We intentionally do not strip Urdu diacritics so evidence stays
traceable to the input.

Signal ids match ``signals.SIGNALS``.
"""

from __future__ import annotations

LEXICON: dict[str, list[str]] = {
    "urgency_threat": [
        "فوراً",
        "فورا",
        "ابھی",
        "جلدی",
        "آخری وارننگ",
        "آخری موقع",
        "فوری",
    ],
    "account_suspension": [
        "اکاؤنٹ بند",
        "اکاؤنٹ بلاک",
        "اکاؤنٹ معطل",
        "تصدیق کریں",
        "تصدیق کرائیں",
        "دوبارہ فعال",
    ],
    "otp_request": [
        "او ٹی پی بھیجیں",
        "او ٹی پی بتائیں",
        "کوڈ بھیجیں",
        "کوڈ بتائیں",
        "پن بتائیں",
        "پن بھیجیں",
    ],
    "credential_request": [
        "پاسورڈ بتائیں",
        "پاسورڈ بھیجیں",
        "اے ٹی ایم پن",
        "کارڈ نمبر",
        "شناختی کارڈ نمبر",
        "اکاؤنٹ نمبر",
    ],
    "payment_demand": [
        "پیسے بھیجیں",
        "رقم بھیجیں",
        "فیس ادا کریں",
        "ادائیگی کریں",
        "جاز کیش",
        "ایزی پیسہ",
    ],
    "prize_lottery": [
        "آپ جیت گئے",
        "انعام",
        "لاٹری",
        "قرعہ اندازی",
        "مبارک ہو",
        "مفت تحفہ",
    ],
    "authority_impersonation": [
        "اسٹیٹ بینک",
        "نادرا",
        "ایف بی آر",
        "کسٹمز",
        "پولیس",
        "عدالت",
    ],
    "suspicious_link": [
        "لنک پر کلک",
        "یہاں کلک کریں",
        "لنک کھولیں",
        "لاگ ان کریں",
    ],
    "app_install": [
        "ایپ انسٹال",
        "ایپ ڈاؤن لوڈ",
        "فائل ڈاؤن لوڈ",
    ],
    "social_pressure": [
        "کسی کو نہ بتائیں",
        "راز رکھیں",
        "صرف آپ",
        "جلدی کریں ورنہ",
    ],
}

# Protective / negation cues in Urdu. When present near an otp/credential cue,
# the cue is a WARNING (e.g. "اپنا او ٹی پی کسی کو نہ بتائیں" = do NOT tell your
# OTP to anyone), not a request.
NEGATION_CUES: list[str] = [
    "نہ بتائیں",
    "نہ دیں",
    "مت بتائیں",
    "مت دیں",
    "شیئر نہ کریں",
    "کسی کو نہ",
    "خبردار",
    "ہوشیار",
    "محفوظ رکھیں",
]
