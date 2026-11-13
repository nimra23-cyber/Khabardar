"""Build a structured + Markdown report from a detection result.

Trust boundary (hardened): the client-supplied result is NOT trusted. The
caller's ``classification`` is RE-DERIVED from the score via the canonical
classifier so an inconsistent score/classification pair cannot produce a
misleading report. Every client-supplied string (category, signal names,
evidence, explanations, ruleset) is neutralized so it cannot inject Markdown
structure (headings, list items, tables), raw HTML, or fake report metadata
into the generated document.

Deterministic; no network, no persistence.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from app.services.detection.classify import classify
from app.services.sanitize import neutralize

_RECOMMENDATIONS = {
    "SAFE": [
        "No strong scam indicators were found, but stay cautious.",
        "Never share OTPs, passwords, or PINs with anyone.",
    ],
    "SUSPICIOUS": [
        "Treat this message with caution; do not act on it immediately.",
        "Do not click links or share any codes/credentials.",
        "Verify the sender through an official channel.",
    ],
    "HIGH RISK": [
        "Do not respond, click links, or share any information.",
        "Do not send money or OTPs/passwords.",
        "Report and delete the message; warn family members.",
    ],
}

# Markdown-structural characters that could let client text forge headings,
# list items, tables, blockquotes, or code fences in the generated document.
# Includes list markers (-, +) and digit-dot ordered-list starts are handled by
# collapsing newlines (so nothing starts a new structural line).
_MD_STRUCTURE = re.compile(r"[#>`*_|\[\]~\r\n+\-]+")


def recommendations_for(classification: str) -> list[str]:
    return _RECOMMENDATIONS.get(classification, _RECOMMENDATIONS["SUSPICIOUS"])


def _safe_text(value, *, max_len: int = 2000) -> str:
    """Neutralize client text for safe inclusion in a Markdown document.

    1. Coerce to str and cap length.
    2. Run the XSS/markup neutralizer (strips tags/scripts/schemes).
    3. Collapse Markdown-structural characters to spaces so the value cannot
       forge headings/list-items/tables/metadata lines.
    """
    if value is None:
        return ""
    s = str(value)[:max_len]
    s = neutralize(s)  # removes HTML/script/dangerous schemes, no angle brackets
    s = _MD_STRUCTURE.sub(" ", s)
    return re.sub(r"[ \t]{2,}", " ", s).strip()


def build_report(result: dict) -> dict:
    """Return ``{report, markdown, filename}`` from a (validated) result dict.

    ``result`` is expected to have passed ``GenerateReportRequest`` validation
    (score range, allowed classification, bounded signals). Here we additionally
    enforce SEMANTIC consistency and neutralize all free text.
    """
    score = int(result.get("risk_score", 0))
    score = max(0, min(100, score))
    # SEMANTIC CONSISTENCY: re-derive the classification from the score so a
    # client cannot claim e.g. score=0 + "HIGH RISK".
    classification = classify(score)

    category = _safe_text(result.get("category"), max_len=100)
    explanation_en = _safe_text(result.get("explanation_en"))
    explanation_ur = _safe_text(result.get("explanation_ur"))
    ruleset = _safe_text(result.get("ruleset_version"), max_len=100)

    raw_signals = result.get("signals", []) or []
    safe_signals = []
    for s in raw_signals[:50]:
        name = _safe_text(s.get("name"), max_len=200) if isinstance(s, dict) else ""
        ev_list = s.get("evidence", []) if isinstance(s, dict) else []
        evidence = [_safe_text(e, max_len=500) for e in (ev_list or [])[:10]]
        evidence = [e for e in evidence if e]
        if name:
            safe_signals.append({"name": name, "evidence": evidence})

    recs = recommendations_for(classification)
    generated_at = datetime.now(timezone.utc).isoformat()

    structured = {
        "title": "KHABARDAR Scam Analysis Report",
        "generated_at": generated_at,
        "risk_score": score,
        "classification": classification,
        "category": category or None,
        "signals": safe_signals,
        "explanation_en": explanation_en,
        "explanation_ur": explanation_ur,
        "recommendations": recs,
        "ruleset_version": ruleset or None,
        "disclaimer": (
            "This is an automated heuristic assessment, not a definitive "
            "verdict. KHABARDAR is a prototype; always verify independently."
        ),
    }

    lines = [
        "# KHABARDAR Scam Analysis Report",
        "",
        f"- Generated: {generated_at}",
        f"- Risk score: {score}/100",
        f"- Classification: {classification}",
        f"- Category: {category or 'n/a'}",
        "",
        "## Detected signals",
    ]
    if safe_signals:
        for s in safe_signals:
            ev = ", ".join(s["evidence"])
            lines.append(f"- {s['name']} (evidence: {ev})")
    else:
        lines.append("- No contributing signals were detected.")
    lines += [
        "",
        "## Explanation (English)",
        explanation_en or "n/a",
        "",
        "## Explanation (Urdu)",
        explanation_ur or "n/a",
        "",
        "## Recommended actions",
    ]
    lines += [f"- {r}" for r in recs]
    lines += ["", f"_{structured['disclaimer']}_"]

    return {
        "report": structured,
        "markdown": "\n".join(lines),
        "filename": f"khabardar-report-{classification.replace(' ', '_').lower()}.md",
    }
