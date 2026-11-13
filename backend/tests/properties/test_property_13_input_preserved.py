"""Contract-level property harness for Property 13 (input preserved on error).

Feature: khabardar-platform, Property 13: User input is preserved on operation
error.

Validates: Requirements 22.7

Design statement:
    For any user operation that fails, the platform returns a user-facing
    message identifying the failed operation, and the submitted input is
    preserved unchanged (no partial modification).

================================================================================
IMPORTANT -- WHAT THIS TEST DOES AND DOES NOT VERIFY
================================================================================

As of this task, KHABARDAR has **no production state-mutating component**: the
``app/`` tree contains only ``core/`` (config, envelope, errors, logging),
``middleware/``, and ``main.py``. There is no ``services/``, ``repositories/``,
``db/``, or ``models/`` layer yet -- persistence lands in Phase 2 (task 2.x).

Consequently this file is a **contract-level / property-harness test**. The
"safe" operation it exercises (compute on a local copy, commit only on success)
is implemented **inside the test fixture**, not in production code. Therefore:

* This test DOES verify the two things that production code already provides:
  the standard error envelope on failure (``ok:false`` + ``operation`` +
  non-empty ``message``, no leakage) -- that part runs through the REAL
  ``register_exception_handlers`` / ``AppError`` / envelope code (see call
  sites below).
* This test DOCUMENTS the intended input/state-preservation invariant and
  proves (via ``test_property_13_assertion_is_not_vacuous``) that the
  preservation check is non-vacuous -- it fails against a mutate-before-fail
  implementation.
* This test DOES **NOT** verify production operation atomicity. The
  preservation behavior shown here is the FIXTURE's behavior, because there is
  no production write operation to call.

TODO (Phase 2 persistence): when real write operations exist (e.g. ScanHistory
persistence), Property 13 MUST be extended to exercise the actual production
service/repository and assert server-side/persisted state is preserved on
failure, using a real DB transaction rollback or an equivalent state
comparison. See docs/DEPENDENCY_NOTES.md / the Property 13 follow-up note.

Production components actually imported/exercised by this harness:
    app.core.errors.AppError                -> raised to signal a failed op
    app.middleware.error_wrapper.register_exception_handlers
                                            -> produces the REAL error envelope
    app.core.envelope.success               -> REAL success envelope for /state
    app.middleware.{validation,request_id,rate_limit,cors}
                                            -> REAL middleware chain
No production persistence/service/repository/transaction helper is imported or
called, because none exists yet.
"""

from __future__ import annotations

import copy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel

from app.core.config import Settings
from app.core.envelope import success
from app.core.errors import AppError
from app.middleware.cors import add_cors
from app.middleware.error_wrapper import register_exception_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.validation import BodySizeLimitMiddleware

PROPERTY_TAG = "Feature: khabardar-platform, Property 13"
MIN_ITERATIONS = 100

# Fixed id of the server-side record the operations act on.
RECORD_ID = "rec-1"


class UpdatePayload(BaseModel):
    text: str
    count: int


def _build_app(*, unsafe: bool) -> FastAPI:
    """Build a HARNESS app whose failing operation acts on server-side state.

    NOTE: the operation bodies below are FIXTURE code, not production code.
    They model the contract Property 13 expects; they do not call any
    production service/repository/transaction helper (none exists yet).

    A single in-process record (``store[RECORD_ID]``) stands in for the
    server-side state. The ``/op/update`` operation always fails, with two
    fixture implementations:

    * safe (``unsafe=False``): models the INTENDED invariant -- compute on a
      LOCAL copy and commit to ``store`` only on success. Since it fails first,
      ``store`` is left unchanged.
    * unsafe (``unsafe=True``): models a BUGGY implementation that mutates
      ``store`` IN PLACE *before* raising. Used only to prove the preservation
      assertion is non-vacuous.

    The REAL production error-handling stack (exception handlers, AppError,
    envelope, middleware) wraps both. ``GET /state`` exposes the current record
    so the test observes it from outside the failed request.
    """
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)
    # Generous rate-limit cap so >=100 Hypothesis iterations aren't throttled.
    app.add_middleware(RateLimitMiddleware, max_requests=100_000, window_seconds=60)
    add_cors(app, Settings())
    register_exception_handlers(app)

    # The server-side state (the object Property 13 requires to be preserved).
    store: dict[str, dict[str, object]] = {
        RECORD_ID: {"text": "ORIGINAL", "count": 0, "revision": 0}
    }
    app.state.store = store

    @app.get("/state")
    def get_state():
        return success(store[RECORD_ID])

    @app.post("/op/update")
    def op_update(payload: UpdatePayload):
        record = store[RECORD_ID]
        if unsafe:
            # BUGGY: partially modify server-side state, THEN fail.
            record["text"] = payload.text
            record["count"] = payload.count
            record["revision"] = record["revision"] + 1  # type: ignore[operator]
            raise AppError(
                "Update failed after partial mutation.",
                operation="record_update",
                code="OPERATION_FAILED",
                status_code=400,
            )
        # SAFE: work on a local copy; commit only on success. We fail before
        # committing, so the server-side record is untouched.
        working = copy.deepcopy(record)
        working["text"] = payload.text
        working["count"] = payload.count
        working["revision"] = working["revision"] + 1  # type: ignore[operator]
        raise AppError(
            "Update failed before commit.",
            operation="record_update",
            code="OPERATION_FAILED",
            status_code=400,
        )
        # (Unreachable commit kept to document intent.)
        # store[RECORD_ID] = working  # noqa: ERA001

    return app


# App under test uses the SAFE (correct) implementation.
_app = _build_app(unsafe=False)
client = TestClient(_app)


_text_strategy = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=0,
    max_size=200,
)


def _server_state() -> dict:
    return client.get("/state").json()["data"]


@settings(max_examples=MIN_ITERATIONS)
@given(text=_text_strategy, count=st.integers(min_value=-(10**6), max_value=10**6))
def test_property_13_contract_failed_operation_preserves_state(text: str, count: int):
    """Contract harness: the REAL error envelope is returned on failure, and
    the (fixture-modeled) server-side state is unchanged.

    The error-envelope half runs through production code
    (register_exception_handlers + AppError + envelope). The state-preservation
    half asserts the INTENDED invariant against the fixture operation; it is a
    contract-level check, not production-atomicity verification (see module
    docstring and the Phase 2 TODO).
    """
    before = copy.deepcopy(_server_state())

    resp = client.post("/op/update", json={"text": text, "count": count})

    # --- Error contract (retained) ---
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    err = body["error"]
    assert err["operation"] == "record_update"
    assert isinstance(err["message"], str) and err["message"].strip()
    assert set(err.keys()) == {"code", "message", "operation"}
    assert "Traceback" not in resp.text
    assert "data" not in body

    # --- Server-side state preservation (the real, non-vacuous check) ---
    after = _server_state()
    assert after == before, (
        "server-side state was modified by a failed operation: "
        f"{before!r} -> {after!r}"
    )
    # The original sentinel values specifically are intact.
    assert after["text"] == "ORIGINAL"
    assert after["count"] == 0
    assert after["revision"] == 0


def test_property_13_assertion_is_not_vacuous():
    """Prove the preservation assertion catches a mutate-before-fail bug.

    Run the SAME failed operation against the UNSAFE implementation and show
    that the server-side state changes -- i.e. the assertion used above would
    fail for a buggy implementation. This guards against a vacuous property.
    """
    unsafe_app = _build_app(unsafe=True)
    unsafe_client = TestClient(unsafe_app)

    before = copy.deepcopy(unsafe_client.get("/state").json()["data"])
    resp = unsafe_client.post("/op/update", json={"text": "NEWVALUE", "count": 99})
    assert resp.status_code == 400  # still returns the error envelope
    after = unsafe_client.get("/state").json()["data"]

    # The buggy implementation DID partially modify server-side state...
    assert after != before
    assert after["text"] == "NEWVALUE"
    assert after["revision"] == before["revision"] + 1
    # ...which is exactly what the preservation assertion in the property test
    # would reject. This demonstrates the property is meaningful, not vacuous.


# A distinctive, attacker-controlled sentinel the validation handler must NEVER
# reflect back. It is deliberately unusual so it cannot collide with any token
# in the static field-name-only message (e.g. "Invalid request fields: count.").
_SECRET_SENTINEL = "SENTINEL_OTP_918273_pw!"


# The error-envelope validation handler summarizes by FIELD NAME only; it never
# echoes submitted values. The only field in UpdatePayload whose value we force
# invalid below is `count`, so this is the exact message the handler produces.
_EXPECTED_VALIDATION_MESSAGE = "Invalid request fields: count."


@settings(max_examples=MIN_ITERATIONS, deadline=None)
@given(text=_text_strategy, count=st.integers(min_value=-(10**6), max_value=10**6))
def test_property_13_validation_error_envelope(text: str, count: int):
    """Validation failure returns the envelope, identifies the operation, and
    does not echo submitted values; server-side state remains untouched.

    We embed an attacker-controlled sentinel into the submitted ``text`` and
    assert the sentinel is NEVER reflected in the response. We also assert the
    handler returns its field-name-only summary verbatim, proving it does not
    leak any submitted value. ``deadline=None`` only disables Hypothesis's
    per-example timing flakiness (TestClient round-trips vary); the iteration
    count (``max_examples=100``) is unchanged, so coverage is preserved.
    """
    before = copy.deepcopy(_server_state())

    # Carry a secret-looking sentinel inside the generated text. If the handler
    # ever echoed submitted values, the sentinel would appear in the response.
    payload_text = f"{text}{_SECRET_SENTINEL}"

    # Wrong type for `count` forces a 422 before the route handler runs.
    resp = client.post(
        "/op/update", json={"text": payload_text, "count": "not-an-int"}
    )

    assert resp.status_code == 422
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["operation"]

    # 1) The attacker-controlled sentinel is NOT reflected anywhere in the
    #    response body (no submitted value leaks), regardless of its content.
    assert _SECRET_SENTINEL not in resp.text

    # 2) The message is exactly the field-name-only summary -- it identifies the
    #    offending field by NAME, never by submitted VALUE.
    assert body["error"]["message"] == _EXPECTED_VALIDATION_MESSAGE

    # 3) Envelope shape and no raw exception detail.
    assert set(body["error"].keys()) == {"code", "message", "operation"}
    assert "Traceback" not in resp.text
    assert "data" not in body

    # Server-side state is unchanged (the route handler never ran).
    assert _server_state() == before
