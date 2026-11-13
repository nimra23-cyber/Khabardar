"""IOC extraction router: POST /api/iocs/extract (Phase 5).

Extracts and normalizes indicators from submitted text (local, keyless). Sensitive
IOC values (phone/email/wallet/bank) are MASKED before returning (Req 21). No
network calls; external threat-intel enrichment is reported 'unavailable' because
live sources require credentials (Req 10.3/10.5) and are never fabricated.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.envelope import success
from app.core.errors import ValidationAppError
from app.schemas.iocs import ExtractIOCRequest, IOCExtractResult, IOCOut
from app.services.intel import extract_iocs
from app.services.privacy import mask_value

router = APIRouter(prefix="/api/iocs", tags=["iocs"])

# IOC types whose values are sensitive and must be masked before display.
_SENSITIVE_TYPES = {"phone", "email", "wallet", "bank"}

# External reputation sources require credentials -> always unavailable in MVP.
_INTEGRATIONS = ("safe_browsing", "virustotal", "urlscan", "abuseipdb")

_TYPE_NOTE = {
    "url": "Link extracted. Analyze it in the URL Analyzer; not auto-fetched.",
    "domain": "Domain extracted. Reputation lookup requires an external source (unavailable).",
    "ip": "IP address extracted. Reputation lookup requires an external source (unavailable).",
    "email": "Email contact extracted (masked).",
    "phone": "Phone contact extracted (masked).",
    "wallet": "Crypto wallet address extracted (masked).",
    "bank": "Bank/payment reference extracted (masked).",
}


@router.post("/extract")
def extract(payload: ExtractIOCRequest) -> dict:
    """Extract, normalize, and mask IOCs from submitted text."""
    text = payload.text
    if not text or len(text) > 10000:
        raise ValidationAppError(
            "Submitted text must be between 1 and 10000 characters.",
            operation="/api/iocs/extract",
            code="INVALID_LENGTH",
        )

    iocs = extract_iocs(text)
    out: list[IOCOut] = []
    for ioc in iocs:
        if ioc.ioc_type in _SENSITIVE_TYPES:
            display = mask_value(ioc.normalized_value)
        else:
            display = ioc.normalized_value
        out.append(
            IOCOut(
                ioc_type=ioc.ioc_type,
                display_value=display,
                note=_TYPE_NOTE.get(ioc.ioc_type, "Indicator extracted."),
            )
        )

    result = IOCExtractResult(
        count=len(out),
        iocs=out,
        integration_states={name: "unavailable" for name in _INTEGRATIONS},
        note=(
            "Indicators were extracted and normalized locally. No claim of "
            "maliciousness is made; external reputation sources are unavailable "
            "without credentials."
        ),
    )
    return success(result.model_dump())
