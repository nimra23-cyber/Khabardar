"""KHABARDAR FastAPI application entrypoint.

Local-only by default: the development runner binds to the configured host,
which defaults to 127.0.0.1. The application must not be exposed on a public
or shared network until authentication/access controls (Req 18) exist.

Routers and middleware are added in later tasks (1.2 onward). This task (1.1)
establishes the bootable skeleton and a health endpoint only.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.core.config import get_settings
from app.core.envelope import success
from app.core.logging_config import (
    UVICORN_LOG_CONFIG,
    configure_application_logging,
)
from app.middleware import register_middleware
from app.middleware.safety_boundary import SafetyBoundaryMiddleware

settings = get_settings()

# Disable Uvicorn's RAW access logger at import time so that no matter how the
# app is launched (dev runner, documented CLI, reload workers), the raw path +
# query string is never logged. Sanitized access logging is provided by the
# application's `khabardar.access` logger instead.
configure_application_logging()

_startup_logger = logging.getLogger("khabardar.error")


def _is_missing_schema_error(exc: Exception) -> bool:
    """True only when the DB error means the schema/tables aren't created yet.

    We match this narrowly so that a not-yet-migrated database is tolerated
    (seed skipped with a clear hint) while every OTHER database error -- bad
    credentials, unreachable host, corrupt file, constraint failures, etc. --
    is re-raised and surfaces loudly instead of masquerading as a successful
    seed. Matches both SQLite ("no such table") and PostgreSQL
    ("undefined_table" / "does not exist") phrasings via the DBAPI message.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError

    if not isinstance(exc, (OperationalError, ProgrammingError)):
        return False
    text = str(getattr(exc, "orig", exc)).lower()
    return (
        "no such table" in text  # SQLite
        or "undefined_table" in text  # PostgreSQL (pgcode name)
        or "does not exist" in text  # PostgreSQL message phrasing
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: ensure the single local user exists (idempotent seed).

    The schema is owned by Alembic migrations (run `alembic upgrade head`
    before starting). ONLY the "schema not created yet" case is tolerated: the
    seed is skipped with a sanitized, actionable warning. Any other database
    error is RE-RAISED so it cannot silently masquerade as a successful seed.
    No sensitive value is ever logged (we log the exception class / a fixed
    hint, never the message).
    """
    try:
        from app.db.seed import seed_local_user

        seed_local_user()
    except Exception as exc:
        if _is_missing_schema_error(exc):
            # Migrations not applied yet: skip seeding with a clear hint.
            _startup_logger.warning(
                "local_user_seed_skipped: schema missing; "
                "run 'alembic upgrade head' first",
            )
        else:
            # A genuine DB/seed error. Log the CLASS only (no message/secret),
            # then re-raise so startup fails loudly instead of silently.
            _startup_logger.error(
                "local_user_seed_failed exception_class=%s",
                type(exc).__name__,
            )
            raise
    yield


fastapi_app = FastAPI(
    title="KHABARDAR",
    description="Think Before You Trust - local scam & fraud protection platform.",
    version=__version__,
    lifespan=lifespan,
)

# Wire the ordered middleware chain and the error-envelope exception handlers.
register_middleware(fastapi_app, settings)

# Feature routers (Task 2.13 / 6.5): scam detection + scan history.
from app.routers.scam import router as scam_router  # noqa: E402
from app.routers.history import router as history_router  # noqa: E402
from app.routers.url import router as url_router  # noqa: E402
from app.routers.iocs import router as iocs_router  # noqa: E402
from app.routers.dashboard import router as dashboard_router  # noqa: E402
from app.routers.reports import router as reports_router  # noqa: E402
from app.routers.media import router as media_router  # noqa: E402

fastapi_app.include_router(scam_router)
fastapi_app.include_router(history_router)
fastapi_app.include_router(url_router)
fastapi_app.include_router(iocs_router)
fastapi_app.include_router(dashboard_router)
fastapi_app.include_router(reports_router)
fastapi_app.include_router(media_router)

# Keep a reference to the FastAPI instance for route registration below.
app = fastapi_app


def _health_payload() -> dict[str, object]:
    """Shared health body (no secrets)."""
    return success(
        {
            "service": "khabardar",
            "version": __version__,
            "local_only": settings.is_local_only,
        }
    )


@app.get("/")
def root() -> dict[str, object]:
    """Service root. Friendly, secret-free service identity."""
    return success(
        {
            "service": "khabardar",
            "tagline": "Think Before You Trust.",
            "version": __version__,
            "docs": "/docs",
            "health": "/api/health",
        }
    )


@app.get("/api/health")
def health() -> dict[str, object]:
    """Liveness probe. Reports version and local-only status (no secrets)."""
    return _health_payload()


@app.get("/health")
def health_alias() -> dict[str, object]:
    """Convenience alias for the canonical /api/health probe."""
    return _health_payload()


@app.get("/api/capabilities")
def capabilities() -> dict[str, object]:
    """Report provider/integration availability without exposing any secret.

    Full capabilities (OCR/QR, Scope B flags) are added in later tasks; this
    task exposes only the credential-availability map from settings (Req 22.6).
    """
    return success(settings.capabilities())


# Wrap the fully-configured FastAPI app in the outermost ASGI safety boundary.
# This sits OUTSIDE Starlette's ServerErrorMiddleware, so any exception that
# Starlette re-raises after handling (it always does: `raise exc`) is caught
# here and NEVER reaches Uvicorn's traceback logger. Routes were registered on
# `fastapi_app` (via the `app` alias) during module load above; reassigning the
# exported `app` only changes the ASGI callable Uvicorn imports.
app = SafetyBoundaryMiddleware(fastapi_app)


def run() -> None:
    """Run the development server bound to the configured (local) host.

    Uses ``access_log=False`` and our ``UVICORN_LOG_CONFIG`` so Uvicorn's raw
    access logger (which would record raw paths + query strings) is disabled;
    sanitized access logging comes from the application's ``khabardar.access``
    logger instead.
    """
    import uvicorn

    # Reload disabled here because the exported `app` is a wrapped ASGI callable
    # (import-string reload would re-wrap). The dev convenience runner passes the
    # app object directly; the documented command uses the import string form.
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        access_log=False,
        log_config=UVICORN_LOG_CONFIG,
    )


if __name__ == "__main__":
    run()
