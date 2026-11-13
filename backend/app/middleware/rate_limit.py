"""In-process rate limiting (Req 19.2).

Rejects a client that exceeds 100 requests within a rolling 60-second window
with a 429 RATE_LIMITED envelope. Keyed by client host. This is a simple,
local, single-process limiter appropriate for the local MVP (no distributed
store). It never inspects or logs the request body.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.envelope import error_response

RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _client_key(self, request: Request) -> str:
        client = request.client
        return client.host if client else "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        key = self._client_key(request)
        now = time.monotonic()
        window_start = now - self.window_seconds

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < window_start:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return error_response(
                    status_code=429,
                    code="RATE_LIMITED",
                    message="Too many requests. Please try again shortly.",
                    operation="rate_limit",
                )
            hits.append(now)

        return await call_next(request)
