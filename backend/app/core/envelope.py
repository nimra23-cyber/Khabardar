"""Standardized API response envelope (Req 22.7).

Every endpoint returns a consistent shape:

* success -> ``{ "ok": true, "data": {...} }``
* error   -> ``{ "ok": false, "error": { "code", "message", "operation" } }``

The ``operation`` field names the user operation that failed so the frontend
can point the user at exactly what went wrong while preserving their input
(Req 22.7). Error bodies NEVER contain stack traces, internal paths, secrets,
or raw exception detail (Req 22.7, security conditions).
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def success(data: Any) -> dict[str, Any]:
    """Build a success envelope body."""
    return {"ok": True, "data": data}


def error_body(code: str, message: str, operation: str) -> dict[str, Any]:
    """Build an error envelope body (no internal detail)."""
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "operation": operation,
        },
    }


def error_response(
    *, status_code: int, code: str, message: str, operation: str, extra: dict[str, Any] | None = None
) -> JSONResponse:
    """Build a JSONResponse carrying the error envelope.

    ``extra`` allows non-sensitive additive fields (e.g. ``blocked: true``,
    ``save_error: true``) that the design places alongside the envelope.
    """
    body = error_body(code, message, operation)
    if extra:
        # Additive, non-sensitive flags only. Never used for secrets/traces.
        body.update(extra)
    return JSONResponse(status_code=status_code, content=body)
