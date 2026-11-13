"""Real-Uvicorn integration tests: sensitive data must not reach server logs.

Two leakage surfaces are covered with an ACTUAL Uvicorn process and REAL HTTP
requests:

1. Exception messages (via Starlette's ``raise exc`` re-raise reaching Uvicorn).
   The outermost ``SafetyBoundaryMiddleware`` must swallow it so no traceback /
   raw message reaches logs.
2. Uvicorn's own access logger, which records the RAW request target
   (``scope["path"]`` + ``query_string``). It must be DISABLED (the documented
   run command uses ``--no-access-log``), and the application's sanitized
   access log (route template only) used instead.

The probe server is launched with the SAME safe flag used in the documented
startup command (``--no-access-log``), not a test-only override, so the test
reflects production behavior. Bound to 127.0.0.1 only.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from tests._uvicorn_leak_probe_app import (
    SENTINEL_PATH,
    SENTINEL_PATHPARAM,
    SENTINEL_QUERY,
    SENTINEL_SECRET,
    SENTINEL_TOKEN,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_ready(port: int, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/api/health"
    while time.monotonic() < deadline:
        try:
            if httpx.get(url, timeout=1.0).status_code == 200:
                return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("Uvicorn did not become ready in time")


def _start_probe_server(port: int) -> subprocess.Popen:
    # Launch with the SAME safe flag as the documented production command.
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "tests._uvicorn_leak_probe_app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-access-log",
        ],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def _stop_and_capture(proc: subprocess.Popen) -> str:
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
    return out or ""


@pytest.mark.integration
def test_real_uvicorn_does_not_log_sensitive_exception_data():
    port = _free_port()
    proc = _start_probe_server(port)
    try:
        _wait_until_ready(port)
        assert httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=2.0).status_code == 200

        resp = httpx.get(f"http://127.0.0.1:{port}/_probe/boom", timeout=5.0)
        assert resp.status_code == 500
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert SENTINEL_SECRET not in resp.text
        assert SENTINEL_PATH not in resp.text
        assert SENTINEL_TOKEN not in resp.text

        time.sleep(1.0)
    finally:
        out = _stop_and_capture(proc)

    # Captured server logs must contain NO sensitive exception data.
    assert SENTINEL_SECRET not in out, "secret leaked into logs"
    assert SENTINEL_PATH not in out, "filesystem path leaked into logs"
    assert SENTINEL_TOKEN not in out, "access token leaked into logs"
    assert "Traceback (most recent call last)" not in out, "traceback in logs"
    assert "unexpected failure secret=" not in out, "raw exception message in logs"

    # Sanitized correlation event IS present.
    assert "unhandled_error" in out
    assert "exception_class=RuntimeError" in out
    assert "route=/_probe/boom" in out
    assert "request_id=" in out


@pytest.mark.integration
def test_real_uvicorn_does_not_log_raw_path_or_query():
    port = _free_port()
    proc = _start_probe_server(port)
    try:
        _wait_until_ready(port)

        # Sentinels in BOTH a path parameter and a query parameter.
        url = (
            f"http://127.0.0.1:{port}/_probe/item/{SENTINEL_PATHPARAM}"
            f"?token={SENTINEL_QUERY}"
        )
        r = httpx.get(url, timeout=5.0)
        assert r.status_code == 200
        # Server-generated request id is present for correlation.
        assert r.headers.get("x-request-id")

        time.sleep(1.0)
    finally:
        out = _stop_and_capture(proc)

    # The raw path parameter and query value must NOT appear anywhere in logs.
    assert SENTINEL_PATHPARAM not in out, "raw path parameter leaked into logs"
    assert SENTINEL_QUERY not in out, "query value leaked into logs"

    # The sanitized application access event uses the route TEMPLATE instead.
    assert "khabardar.access" in out or "route=/_probe/item/{item_id}" in out
    # Specifically, the templated route (not the raw value) is what's recorded.
    assert "route=/_probe/item/{item_id}" in out
