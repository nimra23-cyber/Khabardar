"""Logging configuration that disables Uvicorn's raw access log.

Uvicorn's built-in access logger (``uvicorn.access``) records the RAW request
target via ``get_path_with_query_string(scope)`` -- i.e. ``scope["path"]`` plus
the full ``scope["query_string"]`` (verified in Uvicorn 0.29.0 source). That
raw target can contain sensitive path parameters (e.g. ``/api/history/<secret>``)
and query values (e.g. ``?token=...``). Uvicorn's access logger is INDEPENDENT
of the application middleware, so disabling/replacing it must be done at the
Uvicorn logging layer.

Strategy: keep Uvicorn's error/startup logs, but **silence the raw access
logger** (``uvicorn.access``) and rely on KHABARDAR's own sanitized access
logger (``khabardar.access``, in ``RequestIdMiddleware``) which logs only the
method, matched route TEMPLATE, status, duration, and the server-generated
request id -- never raw paths, query strings, bodies, or credentials.

``UVICORN_LOG_CONFIG`` is passed to ``uvicorn.run(log_config=...)`` by the dev
runner, and the documented CLI command adds ``--no-access-log`` for the same
effect. Both paths disable the raw access log; this is not a test-only setting.
"""

from __future__ import annotations

import logging
import sys

# Dict-config consumed by uvicorn.run(log_config=...). It configures the
# application's sanitized access logger to emit, and disables Uvicorn's raw
# access logger by routing it nowhere and turning off propagation.
UVICORN_LOG_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(levelname)s: %(message)s",
        },
        "khabardar": {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stderr",
        },
        "khabardar": {
            "class": "logging.StreamHandler",
            "formatter": "khabardar",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # Uvicorn's own error/startup logging stays on.
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        # RAW access logger: DISABLED. No handlers, no propagation. This is the
        # logger that would otherwise emit the raw path + query string.
        "uvicorn.access": {"handlers": [], "level": "CRITICAL", "propagate": False},
        # KHABARDAR's sanitized loggers.
        "khabardar.access": {
            "handlers": ["khabardar"],
            "level": "INFO",
            "propagate": False,
        },
        "khabardar.error": {
            "handlers": ["khabardar"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


_KHABARDAR_HANDLER_TAG = "_khabardar_stdout_handler"


def configure_application_logging() -> None:
    """Disable Uvicorn's raw access logger and attach the sanitized app logger.

    Applied at import/startup so the configuration holds no matter how Uvicorn
    is launched -- the dev runner (``uvicorn.run(log_config=...)``), the
    documented CLI command (``uvicorn ... --no-access-log``, which otherwise
    uses Uvicorn's default config and would not know about our loggers), or
    reload workers. Specifically:

    * ``uvicorn.access`` (the RAW path + query-string logger) is fully disabled.
    * ``khabardar.access`` / ``khabardar.error`` get a dedicated stdout handler
      (idempotently) so the sanitized events are always emitted, independent of
      Uvicorn's own logging config.
    """
    # 1) Hard-disable Uvicorn's raw access logger.
    access = logging.getLogger("uvicorn.access")
    access.handlers.clear()
    access.disabled = True
    access.propagate = False

    # 2) Ensure the sanitized application loggers emit regardless of launcher.
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    for name in ("khabardar.access", "khabardar.error"):
        lg = logging.getLogger(name)
        lg.setLevel(logging.INFO)
        lg.propagate = False
        # Idempotent: don't attach a second handler on re-import.
        if not any(getattr(h, _KHABARDAR_HANDLER_TAG, False) for h in lg.handlers):
            handler = logging.StreamHandler(stream=sys.stdout)
            handler.setFormatter(formatter)
            setattr(handler, _KHABARDAR_HANDLER_TAG, True)
            lg.addHandler(handler)


# Backwards-compatible alias (earlier name used by main.py import).
def silence_uvicorn_access_logger() -> None:
    configure_application_logging()
