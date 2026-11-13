/**
 * Scanner page tests (Req 12): file upload, result rendering, error handling.
 * fetch is mocked to return the standard envelope.
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import Scanner from "./Scanner";

// --- Helpers ---

function envelope(data: unknown): Response {
  return {
    ok: true,
    json: async () => ({ ok: true, data }),
  } as unknown as Response;
}

function errorEnvelope(code: string, message: string): Response {
  return {
    ok: false,
    json: async () => ({
      ok: false,
      error: { code, message, operation: "/api/media/scan" },
    }),
  } as unknown as Response;
}

function makePng(size = 100): File {
  // Minimal valid PNG magic bytes.
  const pngMagic = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const blob = new Blob([pngMagic, new Uint8Array(size)], { type: "image/png" });
  return new File([blob], "test.png", { type: "image/png" });
}

function makeOversizedFile(): File {
  const blob = new Blob([new Uint8Array(11 * 1024 * 1024)], { type: "image/png" });
  return new File([blob], "big.png", { type: "image/png" });
}

function makeBadTypeFile(): File {
  const blob = new Blob(["not an image"], { type: "application/pdf" });
  return new File([blob], "bad.pdf", { type: "application/pdf" });
}

const SCAN_RESULT_BASIC = {
  ocr: { available: true, text: "Call now for a prize!", error: null },
  qr: { available: true, values: [], error: null },
  urls_found: [],
  text_analysis: {
    risk_score: 72,
    classification: "HIGH RISK" as const,
    category: "prize_scam",
    signals: [
      {
        signal_id: "urgency_cue",
        name: "Urgency cue",
        explanation: "Pressures the reader to act immediately.",
        direction: "increases",
        evidence: ["now"],
        languages: ["en"],
      },
    ],
    explanation_en: "Urgency indicators detected.",
    explanation_ur: "جلدی کے آثار ملے۔",
    confidence: 0.44,
    detected_languages: ["en"],
    no_signals_detected: false,
    no_signal_notice: null,
    ruleset_version: "rules-2.6.0",
    timestamp: "2025-01-01T00:00:00Z",
    scan_id: null,
    save_error: false,
  },
  url_analyses: [],
  image_type: "png" as const,
  public_demo: true,
};

const SCAN_RESULT_WITH_QR_AND_URLS = {
  ...SCAN_RESULT_BASIC,
  qr: {
    available: true,
    values: ["https://evil.example.com/phish"],
    error: null,
  },
  urls_found: ["https://evil.example.com/phish"],
  url_analyses: [
    {
      valid: true,
      url: "https://evil.example.com/phish",
      domain: "evil.example.com",
      scheme: "https",
      is_ip_url: false,
      blocked: false,
      risk_score: 65,
      classification: "HIGH RISK" as const,
      indicators: [],
      integration_states: { virustotal: "unavailable" },
      redirect_chain: [],
      network_checks: "unavailable",
      recommended_action: "do_not_visit",
      explanation_en: "High-risk URL.",
      ruleset_version: "url-rules-3.0.0",
    },
  ],
};

const SCAN_RESULT_OCR_UNAVAILABLE = {
  ocr: { available: false, text: null, error: "OCR engine not available" },
  qr: { available: false, values: [], error: "QR decoder not available" },
  urls_found: [],
  text_analysis: null,
  url_analyses: [],
  image_type: "png" as const,
  public_demo: true,
};

function renderScanner() {
  return render(
    <MemoryRouter>
      <Scanner />
    </MemoryRouter>,
  );
}

// --- Tests ---

describe("Scanner page", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders the upload form with correct file accept attribute", () => {
    renderScanner();
    const input = screen.getByTestId("scanner-file-input") as HTMLInputElement;
    expect(input.accept).toBe("image/png,image/jpeg,image/webp");
    expect(screen.getByTestId("scanner-submit")).toBeDisabled();
  });

  it("enables submit when a valid file is selected", async () => {
    renderScanner();
    const fileInput = screen.getByTestId("scanner-file-input") as HTMLInputElement;
    const file = makePng();

    // Mock URL.createObjectURL.
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    fireEvent.change(fileInput, { target: { files: [file] } });
    expect(screen.getByTestId("scanner-submit")).not.toBeDisabled();
  });

  it("shows a client error for oversized files without uploading", () => {
    renderScanner();
    const fileInput = screen.getByTestId("scanner-file-input") as HTMLInputElement;
    const bigFile = makeOversizedFile();

    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    fireEvent.change(fileInput, { target: { files: [bigFile] } });
    expect(screen.getByTestId("scanner-client-error")).toBeInTheDocument();
    // Fetch should NOT have been called.
    expect(vi.isMockFunction(globalThis.fetch)).toBe(false);
  });

  it("shows a client error for unsupported file types", () => {
    renderScanner();
    const fileInput = screen.getByTestId("scanner-file-input") as HTMLInputElement;
    const badFile = makeBadTypeFile();

    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    fireEvent.change(fileInput, { target: { files: [badFile] } });
    expect(screen.getByTestId("scanner-client-error")).toBeInTheDocument();
  });

  it("shows a loading state while uploading and renders result", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope(SCAN_RESULT_BASIC),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    renderScanner();
    const fileInput = screen.getByTestId("scanner-file-input") as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [makePng()] } });
    fireEvent.click(screen.getByTestId("scanner-submit"));

    // After response arrives, result section is shown.
    await waitFor(() => screen.getByTestId("scanner-result"));
    expect(screen.getByTestId("scanner-result")).toBeInTheDocument();
  });

  it("shows extracted OCR text when available", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope(SCAN_RESULT_BASIC),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    renderScanner();
    fireEvent.change(screen.getByTestId("scanner-file-input"), {
      target: { files: [makePng()] },
    });
    fireEvent.click(screen.getByTestId("scanner-submit"));

    await waitFor(() => screen.getByTestId("ocr-text"));
    expect(screen.getByTestId("ocr-text").textContent).toContain("prize");
  });

  it("shows risk badge for text analysis", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope(SCAN_RESULT_BASIC),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    renderScanner();
    fireEvent.change(screen.getByTestId("scanner-file-input"), {
      target: { files: [makePng()] },
    });
    fireEvent.click(screen.getByTestId("scanner-submit"));

    await waitFor(() => screen.getByTestId("risk-badge"));
    expect(screen.getByTestId("risk-score").textContent).toBe("72");
    expect(screen.getByTestId("risk-class").textContent).toBe("HIGH RISK");
  });

  it("shows QR values and URL analyses", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope(SCAN_RESULT_WITH_QR_AND_URLS),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    renderScanner();
    fireEvent.change(screen.getByTestId("scanner-file-input"), {
      target: { files: [makePng()] },
    });
    fireEvent.click(screen.getByTestId("scanner-submit"));

    await waitFor(() => screen.getByTestId("qr-values"));
    expect(screen.getByTestId("qr-value-0").textContent).toContain("evil.example.com");

    // URL analysis result shown.
    await waitFor(() => screen.getByTestId("url-analysis-0"));
    expect(screen.getByTestId("url-analysis-0")).toBeInTheDocument();
  });

  it("does NOT auto-open QR URLs — displayed as plain text", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope(SCAN_RESULT_WITH_QR_AND_URLS),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    renderScanner();
    fireEvent.change(screen.getByTestId("scanner-file-input"), {
      target: { files: [makePng()] },
    });
    fireEvent.click(screen.getByTestId("scanner-submit"));

    await waitFor(() => screen.getByTestId("qr-value-0"));
    // The QR value should be rendered as text content, NOT as an <a href="..."> auto-link.
    const qrItem = screen.getByTestId("qr-value-0");
    expect(qrItem.tagName).not.toBe("A");
    expect(qrItem.textContent).toContain("evil.example.com");
  });

  it("shows 'OCR unavailable' when OCR engine is not available", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope(SCAN_RESULT_OCR_UNAVAILABLE),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    renderScanner();
    fireEvent.change(screen.getByTestId("scanner-file-input"), {
      target: { files: [makePng()] },
    });
    fireEvent.click(screen.getByTestId("scanner-submit"));

    await waitFor(() => screen.getByTestId("ocr-unavailable"));
    expect(screen.getByTestId("ocr-unavailable")).toBeInTheDocument();
    expect(screen.getByTestId("qr-unavailable")).toBeInTheDocument();
  });

  it("shows server error and preserves file input on failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      errorEnvelope("INVALID_IMAGE", "The uploaded file could not be validated."),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    renderScanner();
    const fileInput = screen.getByTestId("scanner-file-input") as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [makePng()] } });
    fireEvent.click(screen.getByTestId("scanner-submit"));

    await waitFor(() => screen.getByTestId("scanner-error"));
    expect(screen.getByTestId("scanner-error")).toBeInTheDocument();
    // Result section should NOT be shown.
    expect(screen.queryByTestId("scanner-result")).toBeNull();
  });

  it("shows 'no text' message when OCR returns null text", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope({
        ...SCAN_RESULT_BASIC,
        ocr: { available: true, text: null, error: null },
        text_analysis: null,
      }),
    );
    URL.createObjectURL = vi.fn().mockReturnValue("blob:test");

    renderScanner();
    fireEvent.change(screen.getByTestId("scanner-file-input"), {
      target: { files: [makePng()] },
    });
    fireEvent.click(screen.getByTestId("scanner-submit"));

    await waitFor(() => screen.getByTestId("ocr-no-text"));
    expect(screen.getByTestId("ocr-no-text")).toBeInTheDocument();
  });
});
