"""Dashboard stat aggregation from REAL persisted scans (Req 15.1, 15.2, 15.8).

All numbers come from the ScanHistory table via parameterized ORM queries.
Zero/empty metrics render as numeric 0 (Req 15.2) -- never omitted, never
fabricated. In public-demo mode nothing is persisted, so every metric is 0 and
the dashboard shows an honest empty state.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.scan_history import ScanHistory

# Classifications we bucket risk distribution into.
_CLASSES = ("SAFE", "SUSPICIOUS", "HIGH RISK")


def compute_stats(db: Session, *, public_demo: bool) -> dict:
    """Compute dashboard metrics from persisted scans. Deterministic per data.

    If the schema is not yet initialized (migrations not run) or any DB error
    occurs, returns the honest empty state (all zeros) rather than crashing.
    """
    empty_result = {
        "total_scans": 0,
        "detected_scams": 0,
        "risk_distribution": {c: 0 for c in _CLASSES},
        "category_breakdown": {},
        "trend_30d": [],
        "empty": True,
        "public_demo": public_demo,
        "environment": "prototype",
    }

    try:
        total = int(db.scalar(select(func.count()).select_from(ScanHistory)) or 0)

        # Risk distribution (counts per classification; 0 when none).
        risk_distribution = {c: 0 for c in _CLASSES}
        for cls, cnt in db.execute(
            select(ScanHistory.classification, func.count())
            .group_by(ScanHistory.classification)
        ).all():
            if cls in risk_distribution:
                risk_distribution[cls] = int(cnt)

        # Category breakdown (exclude NULL categories).
        category_breakdown: dict[str, int] = {}
        for cat, cnt in db.execute(
            select(ScanHistory.category, func.count())
            .where(ScanHistory.category.is_not(None))
            .group_by(ScanHistory.category)
        ).all():
            if cat:
                category_breakdown[cat] = int(cnt)

        # 30-day trend: scans per day (date -> count). Only days with data appear;
        # the frontend fills gaps with 0.
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        trend_counter: Counter[str] = Counter()
        rows = db.execute(
            select(ScanHistory.created_at).where(ScanHistory.created_at >= cutoff)
        ).all()
        for (created,) in rows:
            if created is not None:
                trend_counter[created.date().isoformat()] += 1
        trend = [{"date": d, "count": trend_counter[d]} for d in sorted(trend_counter)]

        detected_scams = risk_distribution["SUSPICIOUS"] + risk_distribution["HIGH RISK"]

        return {
            "total_scans": total,
            "detected_scams": detected_scams,
            "risk_distribution": risk_distribution,
            "category_breakdown": category_breakdown,
            "trend_30d": trend,
            "empty": total == 0,
            "public_demo": public_demo,
            "environment": "prototype",
        }
    except Exception:
        # Schema not initialized or DB unavailable -> honest empty state.
        return empty_result
