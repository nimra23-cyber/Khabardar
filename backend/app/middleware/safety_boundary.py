"""Outermost ASGI safety boundary (final guard against log leakage).

Starlette's ``ServerErrorMiddleware`` always re-raises the original exception
after a custom 500 handler runs (verified in Starlette 0.36.3 source:
``errors.py`` ends every handled path with ``raise exc``). That re-raised
exception propagates to Uvicorn, which logs the FULL traceback -- including the
raw exception message, which may contain secrets, OTPs, tokens, or filesystem
paths.

To prevent that, this middleware wraps the ENTIRE application at the ASGI level,
outside Starlette's ``ServerErrorMiddleware``. If any exception escapes the
inner stack (i.e. the inner ServerErrorMiddleware re-raised it), this boundary:

* ensures a clean, generic 500 envelope is sent to the client if no response
  has started yet,
* logs ONLY a sanitized event (request id, exception class name, route template
  or sanitized path, status) -- never ``str(exc)`` and never a traceback,
* and does NOT re-raise, so the exception never reaches Uvicorn's logger.

In the normal path the inner custom handler already sent the clean envelope and
marked the response started; this boundary then simply swallows the re-raised
exception (still logging nothing sensitive) so it cannot reach production logs.
"""

from __future__ import annotations

import json
import logging

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.envelope import error_body
from app.core.errors import INTERNAL_ERROR_CODE, INTERNAL_ERROR_MESSAGE

logger = logging.getLogger("khabardar.error")


def _safe_route(scope: Scope) -> str:
    """Return the route TEMPLATE (no path params) when available.

    Raw URL paths can embed sensitive path parameters; the matched route's
    template (e.g. ``/api/history/{scan_id}``) is safe to log. Falls back to a
    coarse label if no route matched.
    """
    route = scope.get("route")
    template = getattr(route, "path", None)
    if isinstance(template, str) and template:
        return template
    # No matched route (e.g. 404 path or error before routing): log method only
    # plus a generic marker, NEVER the raw (possibly sensitive) path.
    return "<unmatched>"


class SafetyBoundaryMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def _send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, _send)
        except Exception as exc:  # noqa: BLE001 - this is the final guard
            request_id = scope.get("khabardar_request_id") or "n/a"
            # If the inner error handler already produced the clean envelope
            # (normal path), it also logged the sanitized event -- we stay
            # silent to avoid a duplicate log line, and simply swallow the
            # re-raised exception so it cannot reach Uvicorn's logger.
            # Only when NO response has started (the inner handler did not run,
            # e.g. an error raised outside the routing layer) do we emit the
            # generic envelope AND log the sanitized event ourselves.
            if not response_started:
                logger.error(
                    "unhandled_error request_id=%s exception_class=%s route=%s status=%s",
                    request_id,
                    type(exc).__name__,
                    _safe_route(scope),
                    500,
                )
                payload = json.dumps(
                    error_body(
                        INTERNAL_ERROR_CODE,
                        INTERNAL_ERROR_MESSAGE,
                        _safe_route(scope),
                    )
                ).encode("utf-8")
                await send(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(payload)).encode("latin-1")),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": payload})
            # CRITICAL: do NOT re-raise. The exception stops here and can never
            # reach Uvicorn's traceback logger.
