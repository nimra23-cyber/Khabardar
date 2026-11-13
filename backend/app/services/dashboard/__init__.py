"""SOC dashboard services (Phase 6): real stat aggregation from persisted
scans. Zero/empty metrics render as 0 (never fabricated)."""

from app.services.dashboard.stats import compute_stats

__all__ = ["compute_stats"]
