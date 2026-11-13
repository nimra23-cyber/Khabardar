"""Threat-intelligence services (Phase 5): local, keyless IOC extraction,
normalization, and deduplication. No external calls; live enrichment is
Scope B and reported 'unavailable' when keys are absent.
"""

from app.services.intel.extract import extract_iocs, IOC
from app.services.intel.normalize import normalize_ioc

__all__ = ["extract_iocs", "normalize_ioc", "IOC"]
