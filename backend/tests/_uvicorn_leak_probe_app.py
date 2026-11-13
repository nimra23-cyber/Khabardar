"""Throwaway app used ONLY by the real-Uvicorn log-leakage integration test.

It mounts the real middleware chain and adds a single crash route whose
exception message embeds unique sentinels (a fake secret, a filesystem path,
and a fake access token). The integration test runs this under a real Uvicorn
process, makes a real HTTP request, and scans the captured stderr/stdout to
prove those sentinels never reach production logs.

This module is not imported by the production app (app.main); it lives under
tests/ and is referenced only by the integration test.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.envelope import success
from app.core.logging_config import configure_application_logging
from app.middleware import register_middleware
from app.middleware.safety_boundary import SafetyBoundaryMiddleware

# Mirror production: disable Uvicorn's raw access logger and attach the
# sanitized application loggers, regardless of how this is launched.
configure_application_logging()

# Unique sentinels the test will grep for in the server logs.
SENTINEL_SECRET = "UVICORN-LEAK-SECRET-7f3a91"
SENTINEL_PATH = r"C:\Users\victim\private\keys\id_rsa_LEAKPROBE"
SENTINEL_TOKEN = "Bearer-LEAKPROBE-tok-abc123def456"

fastapi_app = FastAPI()
register_middleware(fastapi_app, get_settings())


@fastapi_app.get("/api/health")
def health() -> dict[str, object]:
    return success({"service": "khabardar", "local_only": True})


@fastapi_app.get("/_probe/boom")
def boom() -> dict[str, object]:
    raise RuntimeError(
        f"unexpected failure secret={SENTINEL_SECRET} "
        f"path={SENTINEL_PATH} token={SENTINEL_TOKEN}"
    )


# Sentinels used by the access-log (non-exception) leak test. These are placed
# in a path parameter and a query parameter by the test, and must not appear in
# any captured Uvicorn output.
SENTINEL_PATHPARAM = "PATHPARAM-LEAKPROBE-7a1b2c3d"
SENTINEL_QUERY = "QUERYVAL-LEAKPROBE-9e8f7a6b"


@fastapi_app.get("/_probe/item/{item_id}")
def item(item_id: str) -> dict[str, object]:
    # Succeeds normally. The raw path parameter (item_id) and any query string
    # must never reach the logs; only the route TEMPLATE should be recorded.
    return success({"ok": True})


# Mirror production wrapping: outermost ASGI safety boundary.
app = SafetyBoundaryMiddleware(fastapi_app)
