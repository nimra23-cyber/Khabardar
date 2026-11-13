"""Error-envelope exception handlers (Req 22.7).

Converts every error into the standard error envelope and guarantees that no
stack trace, internal path, secret, or raw exception detail reaches the client.

Handlers:
* ``AppError``            -> its safe code/message/operation + status.
* ``RequestValidationError`` (Pydantic/FastAPI) -> generic VALIDATION_ERROR.
  The raw validation detail is NOT returned verbatim because it can echo back
  submitted sensitive values; a field-name-only summary is provided instead.
* ``HTTPException``        -> mapped to the envelope with a safe message.
* ``Exception`` (catch-all) -> generic INTERNAL_ERROR. Full detail is logged
  server-side only; the client sees nothing internal.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.core.envelope import error_response
from app.core.errors import (
    INTERNAL_ERROR_CODE,
    INTERNAL_ERROR_MESSAGE,
    AppError,
)

logger = logging.getLogger("khabardar.error")


def _operation_for(request: Request) -> str:
    """Derive a coarse operation label from the matched route TEMPLATE.

    The raw URL path can contain sensitive path parameters, so we use the
    matched route's template (e.g. ``/api/history/{scan_id}``) when available
    and a non-sensitive marker otherwise -- never the raw path.
    """
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if isinstance(template, str) and template:
        return template
    return "<unmatched>"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError):
        # Expected, user-facing error with safe fields.
        return error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            operation=exc.operation or _operation_for(request),
            extra=exc.extra,
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(request: Request, exc: RequestValidationError):
        # Summarize by field LOCATION only -- never echo submitted values,
        # which may contain passwords/OTPs/tokens.
        fields = []
        for err in exc.errors():
            loc = err.get("loc", ())
            # Drop the leading "body"/"query" scope; keep field names only.
            parts = [str(p) for p in loc if p not in ("body", "query", "path")]
            if parts:
                fields.append(".".join(parts))
        detail = (
            f"Invalid request fields: {', '.join(sorted(set(fields)))}."
            if fields
            else "The request failed validation."
        )
        return error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message=detail,
            operation=_operation_for(request),
        )

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(request: Request, exc: HTTPException):
        # Use a safe, generic message rather than echoing arbitrary detail.
        safe_message = (
            exc.detail
            if isinstance(exc.detail, str) and exc.status_code < 500
            else "Request could not be completed."
        )
        return error_response(
            status_code=exc.status_code,
            code=f"HTTP_{exc.status_code}",
            message=safe_message,
            operation=_operation_for(request),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception):
        # SANITIZED logging only. We deliberately do NOT use logger.exception()
        # or include str(exc)/the traceback, because the exception message can
        # contain secrets, submitted values, OTPs, tokens, or filesystem paths.
        # We emit a structured, non-sensitive event: request id, exception
        # CLASS name (type only, never the message), path, and status.
        request_id = request.scope.get("khabardar_request_id") or getattr(
            request.state, "request_id", "n/a"
        )
        logger.error(
            "unhandled_error request_id=%s exception_class=%s route=%s status=%s",
            request_id,
            type(exc).__name__,
            _operation_for(request),
            500,
        )
        # Client sees a generic, detail-free envelope.
        return error_response(
            status_code=500,
            code=INTERNAL_ERROR_CODE,
            message=INTERNAL_ERROR_MESSAGE,
            operation=_operation_for(request),
        )
