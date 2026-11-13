"""Report generation (Phase 6 / Req 20 reports).

Builds a structured, human-readable report from a REAL detection result passed
by the client. Stateless and privacy-safe: it reformats data the user already
received; it does not read other users' records and respects public-demo mode
(no persistence). PDF export is optional and not required for the MVP; a
portable Markdown/text report is produced that the frontend offers as a
download.
"""

from app.services.reports.generate import build_report

__all__ = ["build_report"]
