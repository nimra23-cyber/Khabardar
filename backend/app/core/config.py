"""Environment-based configuration and secrets loader.

Consolidates the single source of truth for configuration and secrets
(Requirements 19.4, 8.7, 18.2). Design guarantees enforced here:

* Secrets are loaded ONLY from the backend environment / `.env` file --
  never hardcoded in source and never shipped to the frontend (Req 22.4).
* The application is fully functional with NO optional keys set: every
  optional provider/integration reports as "unavailable" rather than failing.
* Nothing in this module exposes a raw secret value. Secret values are held in
  a private closure (not instance attributes), so they do NOT appear in
  ``vars(settings)`` / ``settings.__dict__`` -- the most common accidental
  serialization path. Availability is reported via a map of
  "configured"/"unavailable" states only (``capabilities()``).
* The server binds to localhost by default (local-only until Req 18 auth).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Callable

from dotenv import load_dotenv

# Load backend/.env if present. Missing file is fine -- all keys are optional.
load_dotenv()


def _get(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or None


class Settings:
    """Runtime configuration.

    Non-secret values are plain public attributes. Secret values are captured
    in a private closure (``_secret``) assigned to a non-attribute slot, so
    they never appear in ``__dict__``. Availability is exposed only via
    ``capabilities()``.
    """

    # Logical names of the secret-bearing settings.
    _SECRET_NAMES = (
        "gemini_key",
        "groq_key",
        "ollama_base_url",
        "safe_browsing_key",
        "virustotal_key",
        "urlscan_key",
        "hash_salt",
    )

    def __init__(self) -> None:
        # --- Server (local-only) ---
        self.host: str = _get("KHABARDAR_HOST", "127.0.0.1") or "127.0.0.1"
        self.port: int = int(_get("KHABARDAR_PORT", "8000") or "8000")
        self.cors_origins: list[str] = [
            o.strip()
            for o in (
                _get(
                    "KHABARDAR_CORS_ORIGINS",
                    "http://127.0.0.1:5173,http://localhost:5173",
                )
                or ""
            ).split(",")
            if o.strip()
        ]

        # --- Database ---
        self.database_url: str = (
            _get("KHABARDAR_DATABASE_URL", "sqlite:///./khabardar.db")
            or "sqlite:///./khabardar.db"
        )

        # --- Privacy / retention (clamped to the allowed 1..3650 range) ---
        raw_retention = int(_get("KHABARDAR_RETENTION_DAYS", "90") or "90")
        self.retention_days: int = max(1, min(3650, raw_retention))

        # --- Media (non-secret path) ---
        self.tesseract_cmd: str | None = _get("TESSERACT_CMD")

        # --- Public demo mode (non-secret) ---
        # When true, the app runs as an UNAUTHENTICATED public demo: scan-history
        # PERSISTENCE and the /api/history endpoint are DISABLED so no shared
        # record store is exposed to anonymous visitors. Text detection still
        # works fully. Enabled via KHABARDAR_PUBLIC_DEMO in {1,true,yes,on}.
        _pd = (_get("KHABARDAR_PUBLIC_DEMO", "false") or "false").lower()
        self.public_demo: bool = _pd in {"1", "true", "yes", "on"}

        # --- Secrets: held in a private closure, NOT as instance attributes ---
        secret_values: dict[str, str | None] = {
            "gemini_key": _get("GEMINI_API_KEY"),
            "groq_key": _get("GROQ_API_KEY"),
            "ollama_base_url": _get("OLLAMA_BASE_URL"),
            "safe_browsing_key": _get("GOOGLE_SAFE_BROWSING_KEY"),
            "virustotal_key": _get("VIRUSTOTAL_KEY"),
            "urlscan_key": _get("URLSCAN_KEY"),
            # Per-install salt/pepper for one-way identifier hashing (Req 21.3).
            # Treated as a secret: held in the closure, never serialized or
            # reported via capabilities(). If unset, the privacy service derives
            # a stable per-install fallback (see services/privacy.py).
            "hash_salt": _get("KHABARDAR_HASH_SALT"),
        }

        def _reader(name: str) -> str | None:
            return secret_values.get(name)

        # A single callable is the only reference to the secret store. It is a
        # plain function object in __dict__; its closure cell holds the values,
        # so str(vars(self)) shows only "<function ...>", never the secrets.
        object.__setattr__(self, "_secret", _reader)

    def secret(self, name: str) -> str | None:
        """Backend-internal accessor for a named secret (never for responses)."""
        if name not in self._SECRET_NAMES:
            raise KeyError(f"Unknown secret: {name}")
        reader: Callable[[str], str | None] = object.__getattribute__(self, "_secret")
        return reader(name)

    def __repr__(self) -> str:
        """Explicit, secret-free representation.

        Shows only non-secret config and the availability map so that repr(),
        str(), f-strings, logging ("%r"/"%s"), and exception messages can never
        interpolate a raw secret value.
        """
        return (
            "Settings("
            f"host={self.host!r}, port={self.port}, "
            f"local_only={self.is_local_only}, "
            f"database_url={self.database_url!r}, "
            f"retention_days={self.retention_days}, "
            f"public_demo={self.public_demo}, "
            f"capabilities={self.capabilities()!r})"
        )

    __str__ = __repr__

    @property
    def is_local_only(self) -> bool:
        """True when bound to a loopback host (the required local-only mode)."""
        return self.host in {"127.0.0.1", "::1", "localhost"}

    def capabilities(self) -> dict[str, dict[str, str]]:
        """Report availability WITHOUT exposing any secret value (Req 22.6).

        Each provider/integration is reported as "configured" or "unavailable"
        based solely on whether its credential is present. No key value appears
        in the output.
        """

        def state(name: str) -> str:
            return "configured" if self.secret(name) else "unavailable"

        return {
            "ai_providers": {
                "gemini": state("gemini_key"),
                "groq": state("groq_key"),
                "ollama": state("ollama_base_url"),
            },
            "integrations": {
                "safe_browsing": state("safe_browsing_key"),
                "virustotal": state("virustotal_key"),
                "urlscan": state("urlscan_key"),
            },
        }


@lru_cache
def get_settings() -> Settings:
    """Return the cached singleton settings instance."""
    return Settings()
