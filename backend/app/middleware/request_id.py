"""Request-ID and sanitized access-logging middleware.

Assigns each request a unique, SERVER-GENERATED id (surfaced as the
``X-Request-ID`` response header) and logs ONE sanitized line per request.

Security properties:

* **Server-generated request IDs.** The id is always a fresh server-side
  ``uuid4``. Any client-supplied ``X-Request-ID`` header is IGNORED (not
  trusted, not reflected), so a client cannot inject log-forging or malicious
  content via the id. For optional inbound correlation, a client value is only
  accepted if it already matches a strict UUID format, and even then it is
  recorded under a separate ``client_corr`` field -- never used as the
  authoritative id.
* **Route template, not raw path.** The access log records the matched route
  TEMPLATE (e.g. ``/api/history/{scan_id}``), never the raw URL path, because
  path parameters can carry sensitive values. Query strings and bodies are
  never logged.
* **No body access.** The request body is never read, buffered, or logged.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("khabardar.access")


def _safe_route(request: Request) -> str:
    """Matched route template if available, else a non-sensitive marker."""
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if isinstance(template, str) and template:
        return template
    return "<unmatched>"


def _valid_uuid(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        return None


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Always server-generated; never derived from client input.
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        # Also expose on scope so the outer safety boundary can read it.
        request.scope["khabardar_request_id"] = request_id

        # Optional inbound correlation id: accepted ONLY if a strict UUID; it is
        # never used as the authoritative id and never echoed to the client.
        client_corr = _valid_uuid(request.headers.get("x-request-id"))

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000.0

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request id=%s method=%s route=%s status=%s duration_ms=%.1f client_corr=%s",
            request_id,
            request.method,
            _safe_route(request),
            response.status_code,
            round(duration_ms, 1),
            client_corr or "-",
        )
        return response
