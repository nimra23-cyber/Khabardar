"""CORS allowlist configuration (Req 19.3).

Allows requests only from the explicitly configured origin allowlist
(local dev origin by default). No wildcard origin is used while credentials
are allowed, which would be insecure.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings


def add_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # explicit allowlist, no "*"
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
