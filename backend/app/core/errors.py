"""Application error types and safe error codes (Req 22.7).

``AppError`` is the base for all expected, user-facing errors. It carries a
safe ``code``, a safe ``message``, an ``operation`` label, and an HTTP status.
The message is intended to be shown to the user and MUST NOT contain stack
traces, internal paths, secrets, or raw exception detail.

Unexpected (non-``AppError``) exceptions are caught by the error-wrapper
middleware and converted to a generic ``INTERNAL_ERROR`` envelope so that no
internal detail ever reaches the client.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for expected, user-facing errors."""

    status_code: int = 400
    code: str = "ERROR"

    def __init__(
        self,
        message: str,
        *,
        operation: str = "unknown",
        code: str | None = None,
        status_code: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.operation = operation
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.extra = extra or None


class ValidationAppError(AppError):
    """Input failed validation (Req 19.1). HTTP 400."""

    status_code = 400
    code = "VALIDATION_ERROR"


class RateLimitError(AppError):
    """Client exceeded the rate limit (Req 19.2). HTTP 429."""

    status_code = 429
    code = "RATE_LIMITED"


class NotFoundError(AppError):
    """Requested resource does not exist. HTTP 404."""

    status_code = 404
    code = "NOT_FOUND"


# Safe, generic message for any unexpected server-side failure. Deliberately
# free of detail so nothing internal leaks (Req 22.7).
INTERNAL_ERROR_CODE = "INTERNAL_ERROR"
INTERNAL_ERROR_MESSAGE = "An internal error occurred while processing the request."
