"""Schemas for the SOC dashboard stats endpoint (Phase 6)."""

from __future__ import annotations

from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: str
    count: int


class DashboardStats(BaseModel):
    total_scans: int
    detected_scams: int
    risk_distribution: dict[str, int]
    category_breakdown: dict[str, int]
    trend_30d: list[TrendPoint]
    empty: bool
    public_demo: bool
    environment: str
