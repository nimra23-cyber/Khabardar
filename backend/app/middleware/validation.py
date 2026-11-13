"""Request body-size enforcement middleware (Req 19.1).

Enforces the maximum body size against the ACTUAL bytes received, not the
``Content-Length`` header. The header is advisory only: it can be missing,
understated, or absent entirely under chunked / streamed transfer encoding.

This is implemented as a pure ASGI middleware (not ``BaseHTTPMiddleware``) so
it can observe the request body stream as it arrives:

* It wraps the ASGI ``receive`` callable and accumulates the length of each
  ``http.request`` body chunk.
* The moment the running total exceeds ``max_body_bytes`` it short-circuits
  with the standard error envelope and HTTP 413, WITHOUT reading further and
  WITHOUT passing the request to downstream handlers.
* For requests within the limit it re-emits exactly the messages it read, so
  downstream FastAPI handlers consume the body normally and unchanged.

A fast-path rejection is also applied when ``Content-Length`` is present and
already declares an oversize body, so obviously-too-large requests are refused
before any body is read.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.envelope import error_body

# 15 MB coarse cap. The media upload path applies its own stricter 10 MB image
# cap (task 4.1); text endpoints apply a 10,000-char cap via Pydantic.
MAX_BODY_BYTES = 15 * 1024 * 1024


class BodySizeLimitMiddleware:
    """Pure-ASGI body size limiter (byte-accurate, chunked-safe)."""

    def __init__(self, app: ASGIApp, max_body_bytes: int = MAX_BODY_BYTES) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Fast path: if Content-Length is present AND already too large, reject
        # up front without reading the body. (We do NOT trust it to be correct
        # when it is small -- the streaming counter below is the real guard.)
        declared = self._declared_length(scope)
        if declared is not None and declared > self.max_body_bytes:
            await self._reject(send)
            return

        received_total = 0
        over_limit = False

        async def limited_receive() -> Message:
            nonlocal received_total, over_limit
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"") or b""
                received_total += len(body)
                if received_total > self.max_body_bytes:
                    over_limit = True
            return message

        # We must still send a response ourselves if the limit is tripped while
        # the app is reading. To keep the stream correct for well-behaved apps,
        # we pre-scan the body here, enforcing the cap, then replay it.
        body_chunks: list[bytes] = []
        more_body = True
        while more_body:
            message = await limited_receive()
            if message["type"] == "http.disconnect":
                # Client went away; let the app handle the disconnect.
                await self.app(scope, self._replay(body_chunks, disconnected=True), send)
                return
            if message["type"] == "http.request":
                if over_limit:
                    await self._reject(send)
                    return
                body_chunks.append(message.get("body", b"") or b"")
                more_body = message.get("more_body", False)
            else:  # pragma: no cover - defensive
                more_body = False

        await self.app(scope, self._replay(body_chunks), send)

    @staticmethod
    def _declared_length(scope: Scope) -> int | None:
        for key, value in scope.get("headers", []):
            if key == b"content-length":
                try:
                    return int(value.decode("latin-1"))
                except ValueError:
                    return None
        return None

    @staticmethod
    def _replay(body_chunks: list[bytes], *, disconnected: bool = False) -> Receive:
        """Build a receive() that replays the already-read body to the app."""
        combined = b"".join(body_chunks)
        sent = False
        disconnect_after = disconnected

        async def replay() -> Message:
            nonlocal sent, disconnect_after
            if not sent:
                sent = True
                return {
                    "type": "http.request",
                    "body": combined,
                    "more_body": False,
                }
            if disconnect_after:
                disconnect_after = False
                return {"type": "http.disconnect"}
            # After the single body message, block on disconnect semantics.
            return {"type": "http.disconnect"}

        return replay

    async def _reject(self, send: Send) -> None:
        import json

        body = error_body(
            "PAYLOAD_TOO_LARGE",
            "Request body exceeds the maximum allowed size.",
            "request_validation",
        )
        payload = json.dumps(body).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(payload)).encode("latin-1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": payload})
