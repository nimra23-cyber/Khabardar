"""HTTP middleware chain for KHABARDAR.

Ordered (outermost first) per design:
    CORS allowlist -> rate limit -> request-id/audit -> error-envelope wrapper

Input validation is enforced by Pydantic at the router boundary plus a body
size cap in the request-id/validation layer. The error-envelope wrapper is the
innermost app-level handler so every error leaves as the standard envelope.
"""

from app.middleware.register import register_middleware

__all__ = ["register_middleware"]
