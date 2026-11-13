"""Bilingual (English + Urdu) plain-language explanation (Task 2.9, Req 5.6/4.5).

Explanations are TEMPLATED from the triggered signals -- no AI, no network.
Both English and Urdu are always produced (Req 5.6). When no signals are
detected, the explanation conveys the honest "no recognized indicators, not a
guarantee of safety" message (Req 5.11 / 7.5).

This module does not add detection; it describes what the rule engine found.
"""

from __future__ import annotations

from app.services.detection.classify import Classification
from app.services.detection.signals import SIGNALS

# Short Urdu label per signal id. Hand-written (not machine-translated) so the
# wording is natural. Partial by design; falls back to the English name.
_SIGNAL_UR: dict[str, str] = {
    "urgency_threat": "فوری یا دھمکی آمیز زبان",
    "account_suspension": "اکاؤنٹ بند/تصدیق کی دھمکی",
    "otp_request": "او ٹی پی/کوڈ مانگنا",
    "credential_request": "پاسورڈ/حساس معلومات مانگنا",
    "payment_demand": "مشکوک ادائیگی کا مطالبہ",
    "prize_lottery": "انعام/لاٹری کا دعویٰ",
    "authority_impersonation": "بینک/ادارے کی جعل سازی",
    "suspicious_link": "مشکوک لنک",
    "app_install": "ایپ/فائل انسٹال کرنے کا کہنا",
    "social_pressure": "نفسیاتی دباؤ",
}

_CLASS_EN = {
    "SAFE": "No strong scam indicators were found",
    "SUSPICIOUS": "This message shows some scam indicators and should be treated with caution",
    "HIGH RISK": "This message shows strong scam indicators and is very likely a scam",
}
_CLASS_UR = {
    "SAFE": "کوئی واضح دھوکہ دہی کے آثار نہیں ملے",
    "SUSPICIOUS": "اس پیغام میں کچھ مشکوک آثار ہیں، احتیاط کریں",
    "HIGH RISK": "اس پیغام میں دھوکہ دہی کے مضبوط آثار ہیں، یہ غالباً فراڈ ہے",
}

_NO_SIGNAL_EN = (
    "No recognized scam indicators were detected. This is not a guarantee that "
    "the message is safe -- stay cautious."
)
_NO_SIGNAL_UR = (
    "کوئی معروف دھوکہ دہی کے آثار نہیں ملے۔ یہ اس بات کی ضمانت نہیں کہ پیغام محفوظ "
    "ہے -- محتاط رہیں۔"
)


def build_explanation(
    triggered_signal_ids: list[str], classification: Classification
) -> tuple[str, str]:
    """Return ``(explanation_en, explanation_ur)`` for the result.

    Deterministic, templated from signals. Always returns both languages.
    """
    if not triggered_signal_ids:
        return _NO_SIGNAL_EN, _NO_SIGNAL_UR

    # Preserve the engine's stable signal order.
    ordered = [sid for sid in SIGNALS if sid in set(triggered_signal_ids)]

    names_en = [SIGNALS[sid]["name"] for sid in ordered]
    names_ur = [_SIGNAL_UR.get(sid, SIGNALS[sid]["name"]) for sid in ordered]

    en = (
        f"{_CLASS_EN.get(classification, classification)}. "
        f"Indicators found: {', '.join(names_en)}."
    )
    ur = (
        f"{_CLASS_UR.get(classification, classification)}۔ "
        f"نشاندہی شدہ آثار: {'، '.join(names_ur)}۔"
    )
    return en, ur
