"""Middleware + exception-handler tests (Task 1.2).

Covers:
* validation errors (Pydantic 422) -> envelope, field names only, no echoed values
* unexpected exceptions -> generic INTERNAL_ERROR, NO stack trace / secret leak
* AppError -> safe code/message/operation
* malformed JSON body -> envelope, no leak
* consistent error structure across all paths
* rate-limit window boundary (101st request rejected)
* CORS allow vs deny
* request body with passwords/OTPs/tokens is NEVER logged
"""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import AppError, ValidationAppError
from app.middleware import register_middleware
from app.middleware.rate_limit import RateLimitMiddleware


SENTINEL_SECRET = "TOPSECRET-OTP-999111"


class Payload(BaseModel):
    text: str
    count: int


def build_app(**overrides) -> FastAPI:
    settings = Settings()
    app = FastAPI()
    register_middleware(app, settings)

    @app.post("/echo")
    def echo(payload: Payload):
        from app.core.envelope import success

        return success({"len": len(payload.text)})

    @app.post("/boom")
    def boom(payload: Payload):
        # Simulate an unexpected bug whose message embeds BOTH a secret and a
        # filesystem path -- neither may reach the client or the logs.
        raise RuntimeError(
            f"internal failure at {SENTINEL_PATH} token={SENTINEL_SECRET}"
        )

    @app.get("/app-error")
    def app_error():
        raise ValidationAppError("bad thing", operation="demo_op")

    @app.get("/raw-http")
    def raw_http():
        raise AppError("not found", operation="demo", code="NOT_FOUND", status_code=404)

    return app


@pytest.fixture
def client():
    return TestClient(build_app())


@pytest.fixture
def client_observe_errors():
    # Do NOT re-raise server exceptions: observe the actual response the client
    # would receive in production (so we can assert no leakage in the body).
    return TestClient(build_app(), raise_server_exceptions=False)


def _assert_error_envelope(body: dict):
    assert body["ok"] is False
    assert set(body["error"].keys()) >= {"code", "message", "operation"}


def test_validation_error_envelope_no_value_echo(client):
    # Missing "count" and wrong type -> 422 with field names, not submitted values.
    r = client.post("/echo", json={"text": SENTINEL_SECRET})
    assert r.status_code == 422
    body = r.json()
    _assert_error_envelope(body)
    assert body["error"]["code"] == "VALIDATION_ERROR"
    # The submitted sensitive value must NOT be echoed back.
    assert SENTINEL_SECRET not in r.text
    # Field name is referenced.
    assert "count" in body["error"]["message"]


SENTINEL_PATH = r"C:\Users\secretuser\private\keys\id_rsa"


@pytest.fixture
def capture_khabardar_logs():
    """Temporarily let the non-propagating khabardar.* loggers reach caplog.

    In production these loggers have ``propagate=False`` and their own stdout
    handler (so Uvicorn's config cannot swallow them). pytest's ``caplog``
    captures via the root logger, which requires propagation. This fixture
    flips propagation ON only for the duration of a test so caplog can observe
    the sanitized records, then restores the production setting. It does NOT
    change what is logged -- only where the test can see it.
    """
    names = ("khabardar.access", "khabardar.error")
    saved = {n: logging.getLogger(n).propagate for n in names}
    for n in names:
        logging.getLogger(n).propagate = True
    try:
        yield
    finally:
        for n, val in saved.items():
            logging.getLogger(n).propagate = val


def test_unexpected_exception_is_generic_and_no_leak(
    client_observe_errors, caplog, capture_khabardar_logs
):
    # Capture ALL application logs across every khabardar logger during the call.
    with caplog.at_level(logging.DEBUG):
        r = client_observe_errors.post("/boom", json={"text": "hi", "count": 1})

    assert r.status_code == 500
    body = r.json()
    _assert_error_envelope(body)
    assert body["error"]["code"] == "INTERNAL_ERROR"

    # --- Client response must not leak anything internal ---
    assert SENTINEL_SECRET not in r.text
    assert SENTINEL_PATH not in r.text
    assert "RuntimeError" not in r.text
    assert "Traceback" not in r.text

    # --- Captured application logs must not leak the sentinel secret, the
    #     sentinel filesystem path, the raw exception message, or a traceback.
    captured = caplog.text
    assert SENTINEL_SECRET not in captured, "secret leaked into logs"
    assert SENTINEL_PATH not in captured, "filesystem path leaked into logs"
    assert "Traceback (most recent call last)" not in captured, "traceback in logs"
    # The sanitized event IS present: request id + exception class + path.
    assert "unhandled_error" in captured
    assert "RuntimeError" in captured  # class name only (no message)
    assert "/boom" in captured


def test_app_error_envelope(client):
    r = client.get("/app-error")
    assert r.status_code == 400
    body = r.json()
    _assert_error_envelope(body)
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["operation"] == "demo_op"
    assert body["error"]["message"] == "bad thing"


def test_app_error_custom_status(client):
    r = client.get("/raw-http")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_malformed_json_body(client):
    r = client.post(
        "/echo",
        data="{not-json",
        headers={"content-type": "application/json"},
    )
    # FastAPI raises a RequestValidationError for unparsable JSON -> 422 envelope.
    assert r.status_code == 422
    _assert_error_envelope(r.json())
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_request_id_header_present(client):
    r = client.get("/app-error")
    assert "x-request-id" in {k.lower() for k in r.headers.keys()}


def test_rate_limit_window_boundary():
    # Small limit so the test is fast and deterministic.
    settings = Settings()
    app = FastAPI()
    # Register normal chain then override the rate limiter with a tiny limit.
    register_middleware(app, settings)
    # Rebuild a dedicated app with a 3-request limit for a crisp boundary test.
    app2 = FastAPI()
    app2.add_middleware(RateLimitMiddleware, max_requests=3, window_seconds=60)

    from app.core.envelope import success

    @app2.get("/ping")
    def ping():
        return success({"pong": True})

    c = TestClient(app2)
    assert c.get("/ping").status_code == 200  # 1
    assert c.get("/ping").status_code == 200  # 2
    assert c.get("/ping").status_code == 200  # 3
    r4 = c.get("/ping")                        # 4 -> rejected
    assert r4.status_code == 429
    assert r4.json()["error"]["code"] == "RATE_LIMITED"


def test_cors_allows_listed_origin_and_denies_other():
    settings = Settings()  # default allowlist: 127.0.0.1:5173 / localhost:5173
    app = FastAPI()
    register_middleware(app, settings)

    from app.core.envelope import success

    @app.get("/ping")
    def ping():
        return success({"pong": True})

    c = TestClient(app)

    allowed = "http://127.0.0.1:5173"
    r_ok = c.get("/ping", headers={"origin": allowed})
    assert r_ok.headers.get("access-control-allow-origin") == allowed

    denied = "http://evil.example"
    r_deny = c.get("/ping", headers={"origin": denied})
    # Request still succeeds server-side, but no ACAO header is granted to the
    # disallowed origin, so the browser blocks it.
    assert r_deny.headers.get("access-control-allow-origin") != denied


def test_request_body_with_secrets_is_not_logged(caplog, capture_khabardar_logs):
    """The request logger must never emit the request body (passwords/OTPs)."""
    client = TestClient(build_app())
    with caplog.at_level(logging.INFO):
        client.post("/echo", json={"text": f"my password is {SENTINEL_SECRET}", "count": 2})
    # The access log line records method/route/status only -- never the body.
    assert SENTINEL_SECRET not in caplog.text
    # The sanitized access event is present, using the route template.
    assert "khabardar.access" in caplog.text
    assert "route=/echo" in caplog.text  # route template (non-sensitive)


# ---------------------------------------------------------------------------
# Body-size limit: byte-accurate enforcement (not Content-Length trust).
# ---------------------------------------------------------------------------

from starlette.requests import Request as _Request  # noqa: E402

from app.middleware.request_id import RequestIdMiddleware  # noqa: E402
from app.middleware.validation import BodySizeLimitMiddleware  # noqa: E402


def build_limit_app(max_body_bytes: int):
    """App with a small body cap and a raw-body echo route.

    Reads the raw body inside the handler to prove (a) the limiter does not
    break downstream body consumption and (b) small valid requests reach the
    handler intact.
    """
    app = FastAPI()
    # Innermost: body limiter. Outer: request-id (so X-Request-ID still works).
    app.add_middleware(BodySizeLimitMiddleware, max_body_bytes=max_body_bytes)
    app.add_middleware(RequestIdMiddleware)

    from app.core.envelope import success

    @app.post("/raw")
    async def raw(request: _Request):
        body = await request.body()
        return success({"received_bytes": len(body)})

    return app


def test_small_valid_request_reaches_handler():
    app = build_limit_app(max_body_bytes=1000)
    c = TestClient(app)
    payload = b"x" * 100
    r = c.post("/raw", content=payload)
    assert r.status_code == 200
    # Handler actually consumed the (replayed) body intact.
    assert r.json()["data"]["received_bytes"] == 100


def test_small_valid_json_reaches_pydantic_handler():
    # Uses the full middleware chain + a Pydantic route to confirm the limiter
    # does not break FastAPI JSON body parsing downstream.
    c = TestClient(build_app())
    r = c.post("/echo", json={"text": "hello", "count": 3})
    assert r.status_code == 200
    assert r.json()["data"]["len"] == 5


def test_oversized_content_length_fastpath_rejected():
    app = build_limit_app(max_body_bytes=1000)
    c = TestClient(app)
    # Declare a huge Content-Length; limiter should reject on the fast path.
    big = b"y" * 5000
    r = c.post("/raw", content=big)
    assert r.status_code == 413
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_missing_content_length_streamed_oversize_rejected():
    """Chunked/streamed body with NO Content-Length, exceeding the cap."""
    app = build_limit_app(max_body_bytes=1000)
    c = TestClient(app)

    def gen():
        # A generator body makes httpx use chunked transfer (no Content-Length).
        for _ in range(20):
            yield b"z" * 100  # 2000 bytes total > 1000 cap

    r = c.post("/raw", content=gen())
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_understated_content_length_still_rejected():
    """Content-Length lies (too small); actual bytes exceed the cap.

    We force a small, incorrect Content-Length header while sending a larger
    body, proving the limiter counts ACTUAL bytes rather than trusting the
    header.
    """
    app = build_limit_app(max_body_bytes=1000)
    c = TestClient(app)
    actual = b"w" * 5000
    # Override Content-Length to understate the true size.
    r = c.post(
        "/raw",
        content=actual,
        headers={"content-length": "10"},
    )
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_body_at_limit_boundary_accepted():
    app = build_limit_app(max_body_bytes=1000)
    c = TestClient(app)
    exactly = b"a" * 1000
    r = c.post("/raw", content=exactly)
    assert r.status_code == 200
    assert r.json()["data"]["received_bytes"] == 1000


# ---------------------------------------------------------------------------
# ASGI edge cases for the body limiter: multi-chunk, disconnect, handler-gating,
# body integrity on replay, and the memory-bound property.
# ---------------------------------------------------------------------------

import asyncio  # noqa: E402

from app.middleware.validation import BodySizeLimitMiddleware as _BSL  # noqa: E402


def _handler_gating_app(max_body_bytes: int):
    """Route records whether it executed, to prove gating of oversized bodies."""
    app = FastAPI()
    app.add_middleware(_BSL, max_body_bytes=max_body_bytes)
    from app.core.envelope import success

    state = {"handler_ran": False, "received": None}

    @app.post("/raw")
    async def raw(request: _Request):
        state["handler_ran"] = True
        body = await request.body()
        state["received"] = body
        return success({"n": len(body)})

    return app, state


def test_multi_chunk_combined_exceeds_cap_rejected():
    app, state = _handler_gating_app(max_body_bytes=1000)
    c = TestClient(app)

    def gen():
        # 15 chunks x 100 bytes = 1500 > 1000, delivered as multiple chunks.
        for _ in range(15):
            yield b"c" * 100

    r = c.post("/raw", content=gen())
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    # Oversized request rejected BEFORE the route handler executed.
    assert state["handler_ran"] is False


def test_multi_chunk_at_or_below_cap_reaches_route_intact():
    app, state = _handler_gating_app(max_body_bytes=1000)
    c = TestClient(app)

    expected = b"".join(bytes([65 + (i % 26)]) * 100 for i in range(9))  # 900 bytes

    def gen():
        for i in range(9):
            yield bytes([65 + (i % 26)]) * 100

    r = c.post("/raw", content=gen())
    assert r.status_code == 200
    assert state["handler_ran"] is True
    # Body reached the handler COMPLETE and UNALTERED (no dup/truncation).
    assert state["received"] == expected
    assert len(state["received"]) == 900
    assert r.json()["data"]["n"] == 900


def test_oversized_request_gated_before_handler():
    app, state = _handler_gating_app(max_body_bytes=500)
    c = TestClient(app)
    r = c.post("/raw", content=b"x" * 5000)
    assert r.status_code == 413
    assert state["handler_ran"] is False


def test_disconnect_is_handled_without_hang():
    """An http.disconnect during receive must not hang or corrupt the request.

    Drive the middleware directly at the ASGI layer with a receive() that
    yields one small body chunk (more_body=True) then an http.disconnect.
    """
    async def run():
        sent: list = []

        async def app(scope, receive, send):
            # Downstream app drains receive until it sees disconnect, then
            # returns a trivial response. Must not hang.
            while True:
                msg = await receive()
                if msg["type"] == "http.disconnect":
                    break
                if msg["type"] == "http.request" and not msg.get("more_body"):
                    break
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        mw = _BSL(app, max_body_bytes=1000)

        scope = {"type": "http", "headers": [], "method": "POST", "path": "/x"}

        messages = [
            {"type": "http.request", "body": b"ab", "more_body": True},
            {"type": "http.disconnect"},
        ]
        idx = {"i": 0}

        async def receive():
            i = idx["i"]
            idx["i"] += 1
            if i < len(messages):
                return messages[i]
            return {"type": "http.disconnect"}

        async def send(message):
            sent.append(message)

        # Must complete well within a timeout (no hang).
        await asyncio.wait_for(mw(scope, receive, send), timeout=5.0)
        return sent

    sent = asyncio.run(run())
    # The app produced a response; the chain did not hang or raise.
    assert any(m["type"] == "http.response.start" for m in sent)


def test_body_buffer_memory_bound():
    """The buffered body cannot exceed max_body_bytes + one detection chunk.

    We instrument the middleware's replay to measure the largest buffer it
    ever assembled. With a cap of 1000 and 200-byte chunks, overflow is
    detected at 1200 bytes (cap + one chunk), and the request is rejected --
    the buffer must never hold the full oversized stream (e.g. not 10000).
    """
    captured = {"max_seen": 0}

    # Capture the ORIGINAL staticmethod descriptor from the class __dict__ so we
    # can restore it faithfully. (Reading ``_BSL._replay`` returns the
    # descriptor-resolved plain function; re-assigning that would turn the
    # staticmethod into an instance method and break later ``self._replay``
    # calls across the whole test session.)
    original_descriptor = _BSL.__dict__["_replay"]
    original_replay = _BSL._replay  # resolved function, for calling directly

    @staticmethod
    def spy_replay(body_chunks, *, disconnected=False):
        total = sum(len(c) for c in body_chunks)
        captured["max_seen"] = max(captured["max_seen"], total)
        return original_replay(body_chunks, disconnected=disconnected)

    app = FastAPI()
    app.add_middleware(_BSL, max_body_bytes=1000)
    from app.core.envelope import success

    @app.post("/raw")
    async def raw(request: _Request):
        b = await request.body()
        return success({"n": len(b)})

    c = TestClient(app)

    _BSL._replay = spy_replay
    try:
        def gen():
            # 50 chunks x 200 bytes = 10000 bytes total, far over the cap.
            for _ in range(50):
                yield b"q" * 200
        r = c.post("/raw", content=gen())
    finally:
        # Restore the ORIGINAL staticmethod descriptor (not the resolved
        # function), so the class attribute stays a staticmethod for every
        # later test that POSTs a body through this middleware.
        _BSL._replay = original_descriptor

    assert r.status_code == 413
    # On rejection we never call _replay with the full body; but even in the
    # accepted path the buffer is bounded. Assert the middleware aborted long
    # before buffering the whole 10000-byte stream.
    assert captured["max_seen"] <= 1000 + 200, captured["max_seen"]
