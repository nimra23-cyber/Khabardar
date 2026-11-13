"""Scam detection pipeline: engine -> category -> explanation -> masked persist.

Orchestrates the in-scope MVP text path (Task 2.13) using the EXISTING rule
engine (Task 2.6), category/explanation assembly (Task 2.9), and the EXISTING
privacy+XSS persistence boundary (Task 2.4 ScanHistoryRepository). No AI keys,
no network, no raw-content logging.

Persistence failures do NOT fail the request: the computed result is still
returned with ``save_error=True`` (Req 20.4).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.detection import evaluate
from app.services.detection.categories import assign_category
from app.services.detection.explanation import build_explanation
from app.repositories.scan_history import ScanHistoryRepository


def _confidence_from_score(score: int) -> float:
    """Derive a 0.00-1.00 confidence as a transparent function of the score.

    This is a HEURISTIC readout of how far the score sits from the SAFE/HIGH
    bands, NOT a calibrated probability of fraud (Req 23 honesty). Deterministic.
    """
    # Distance from the nearest band centre, normalized. Simple, bounded,
    # monotone-ish: low/high scores -> higher confidence in the label.
    return round(min(1.0, abs(score - 50) / 50.0 + (score / 100.0) * 0.0 + 0.0), 2)


def run_detection(text: str, *, db: Session | None = None, user_id: str | None = None):
    """Run the full text-detection pipeline and return a result dict.

    If ``db`` and ``user_id`` are provided, the result is persisted via the
    masked repository boundary; on failure the result is still returned with
    ``save_error=True``. Returns a plain dict ready for ``DetectResult``.
    """
    engine_result = evaluate(text)
    triggered_ids = [s.signal_id for s in engine_result.signals]

    category = assign_category(triggered_ids, engine_result.classification)
    explanation_en, explanation_ur = build_explanation(
        triggered_ids, engine_result.classification
    )
    confidence = _confidence_from_score(engine_result.risk_score)
    timestamp = datetime.now(timezone.utc).isoformat()

    signals_payload = [
        {
            "signal_id": s.signal_id,
            "name": s.name,
            "explanation": s.explanation,
            "direction": s.direction,
            "evidence": list(s.evidence),
            "languages": list(s.languages),
        }
        for s in engine_result.signals
    ]

    scan_id: str | None = None
    save_error = False
    if db is not None and user_id is not None:
        try:
            repo = ScanHistoryRepository(db)
            record = repo.create_scan(
                user_id=user_id,
                scan_type="text",
                raw_content=text,  # masked+neutralized inside the repository
                risk_score=engine_result.risk_score,
                classification=engine_result.classification,
                category=category,
                signals=signals_payload,
                explanation_en=explanation_en,
                explanation_ur=explanation_ur,
                confidence=confidence,
                origin="verified",
            )
            scan_id = record.id
        except Exception:
            # Req 20.4: still return the computed result, flag the save failure.
            save_error = True

    return {
        "risk_score": engine_result.risk_score,
        "classification": engine_result.classification,
        "category": category,
        "signals": signals_payload,
        "explanation_en": explanation_en,
        "explanation_ur": explanation_ur,
        "confidence": confidence,
        "detected_languages": engine_result.detected_languages,
        "no_signals_detected": engine_result.no_signals_detected,
        "no_signal_notice": engine_result.no_signal_notice,
        "ruleset_version": engine_result.ruleset_version,
        "timestamp": timestamp,
        "scan_id": scan_id,
        "save_error": save_error,
    }
