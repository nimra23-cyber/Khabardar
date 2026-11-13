"""Unit tests for the response/error envelope helpers (Task 1.2)."""

from __future__ import annotations

from app.core.envelope import error_body, error_response, success


def test_success_shape():
    body = success({"x": 1})
    assert body == {"ok": True, "data": {"x": 1}}


def test_error_body_shape():
    body = error_body("VALIDATION_ERROR", "bad input", "scam_detect")
    assert body == {
        "ok": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "bad input",
            "operation": "scam_detect",
        },
    }


def test_error_response_includes_extra_flags():
    resp = error_response(
        status_code=200,
        code="SSRF_BLOCKED",
        message="blocked",
        operation="url_analyze",
        extra={"blocked": True},
    )
    assert resp.status_code == 200
    # JSONResponse stores the serialized body on .body; decode and check.
    import json

    payload = json.loads(resp.body)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "SSRF_BLOCKED"
    assert payload["blocked"] is True
