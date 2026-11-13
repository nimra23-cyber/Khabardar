/** Detector page tests (Task 2.14): renders backend result, preserves input
 * on error, shows no-signal notice. fetch is mocked to return the standard
 * envelope -- this verifies UI behavior against the real client, not a fake
 * detection algorithm. */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import Detector from "./Detector";

function envelope(data: unknown) {
  return {
    ok: true,
    json: async () => ({ ok: true, data }),
  } as unknown as Response;
}

function errorEnvelope(status: number, code: string) {
  return {
    ok: false,
    json: async () => ({
      ok: false,
      error: { code, message: "Invalid input.", operation: "/api/scam/detect" },
    }),
  } as unknown as Response;
}

const SCAM_RESULT = {
  risk_score: 71,
  classification: "HIGH RISK",
  category: "otp_theft",
  signals: [
    {
      signal_id: "otp_request",
      name: "OTP / verification code request",
      explanation: "Asks to share an OTP.",
      direction: "increases",
      evidence: ["share your OTP"],
      languages: ["en"],
    },
  ],
  explanation_en: "Strong indicators.",
  explanation_ur: "مضبوط آثار۔",
  confidence: 0.42,
  detected_languages: ["en"],
  no_signals_detected: false,
  no_signal_notice: null,
  ruleset_version: "rules-2.6.0",
  timestamp: "2025-01-01T00:00:00Z",
  scan_id: "abc",
  save_error: false,
};

describe("Detector page", () => {
  afterEach(() => vi.restoreAllMocks());

  it("submits text and renders the backend result", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(envelope(SCAM_RESULT));
    render(<Detector />);
    fireEvent.change(screen.getByTestId("detector-input"), {
      target: { value: "share your OTP now" },
    });
    fireEvent.click(screen.getByTestId("detector-submit"));
    await waitFor(() => screen.getByTestId("detector-result"));
    expect(screen.getByTestId("risk-score").textContent).toBe("71");
    expect(screen.getByTestId("risk-class").textContent).toBe("HIGH RISK");
    expect(screen.getByTestId("signal-otp_request")).toBeInTheDocument();
    expect(screen.getByTestId("explanation-ur").textContent).toContain("آثار");
  });

  it("preserves input and shows an error on server failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      errorEnvelope(422, "VALIDATION_ERROR"),
    );
    render(<Detector />);
    const input = screen.getByTestId("detector-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "bad input" } });
    fireEvent.click(screen.getByTestId("detector-submit"));
    await waitFor(() => screen.getByTestId("detector-error"));
    // Input is preserved (not cleared) on error (Req 22.7).
    expect(input.value).toBe("bad input");
  });

  it("shows the no-signal notice when applicable", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope({
        ...SCAM_RESULT,
        risk_score: 0,
        classification: "SAFE",
        category: null,
        signals: [],
        no_signals_detected: true,
        no_signal_notice: "No recognized indicators; not a guarantee of safety.",
      }),
    );
    render(<Detector />);
    fireEvent.change(screen.getByTestId("detector-input"), {
      target: { value: "asdkfj qweoiru" },
    });
    fireEvent.click(screen.getByTestId("detector-submit"));
    await waitFor(() => screen.getByTestId("no-signal-notice"));
    expect(screen.getByTestId("no-signal-notice").textContent).toContain(
      "not a guarantee",
    );
  });
});
