"""ORM models package.

Importing this package registers all 11 models on ``Base.metadata`` so Alembic
and ``create_all`` see the full schema.
"""

from app.db.base import Base
from app.models.audit_log import AuditLog
from app.models.family import FamilyGroup, FamilyMember
from app.models.honeypot_session import HoneypotSession
from app.models.notification import Notification
from app.models.scam_campaign import ScamCampaign
from app.models.scam_report import ScamReport
from app.models.scan_history import ScanHistory
from app.models.threat_indicator import ThreatIndicator
from app.models.url_analysis import URLAnalysis
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "ScanHistory",
    "ScamReport",
    "URLAnalysis",
    "ThreatIndicator",
    "ScamCampaign",
    "FamilyGroup",
    "FamilyMember",
    "Notification",
    "AuditLog",
    "HoneypotSession",
]
