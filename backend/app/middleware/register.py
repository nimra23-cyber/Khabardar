"""Wire the middleware chain and exception handlers onto the app.

Starlette applies ``add_middleware`` in reverse order of registration (the
LAST added runs OUTERMOST). To achieve the design's outermost-first order:

    CORS (outermost) -> rate limit -> request-id/audit -> body-size validation

we register them in the reverse sequence below. Exception handlers are then
installed so every error leaves as the standard envelope.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.core.config import Settings
from app.middleware.cors import add_cors
from app.middleware.error_wrapper import register_exception_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.validation import BodySizeLimitMiddleware


def register_middleware(app: FastAPI, settings: Settings) -> None:
    # Registered innermost-first; Starlette runs last-added outermost.
    app.add_middleware(BodySizeLimitMiddleware)       # innermost
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RateLimitMiddleware)
    add_cors(app, settings)                           # outermost (CORS)

    register_exception_handlers(app)
