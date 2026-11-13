/** UrlAnalyzer page tests (Phase 3): renders backend result, shows blocked
 * state, preserves input on error. fetch mocked to the standard envelope. */
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import UrlAnalyzer from "./UrlAnalyzer";

function ok(data: unknown) {
  return { ok: true, json: async () => ({ ok: true, data }) } as unknown as Response;
}
function err(code: string) {
  return {
    ok: false,
    json: async () => ({
      ok: false,
      error: { code, message: "Invalid URL.", operation: "/api/url/analyze" },
    }),
  } as unknown as Response;
}

const RESULT = {
  url: "http://jazzcash.secure-login.xyz",
  domain: "jazzcash.secure-login.xyz",
  scheme: "http",
  is_ip_url: false,
  blocked: false,
  risk_score: 52,
  classification: "SUSPICIOUS",
  indicators: [
    { id: "brand_in_subdomain", name: "Brand in subdomain", evidence: "jazzcash", weight: 30 },
  ],
  integration_states: { virustotal: "unavailable", whois: "unavailable" },
  redirect_chain: [],
  network_checks: "unavailable",
  recommended_action: "do_not_enter_credentials",
  explanation_en: "Analyzed locally.",
  ruleset_version: "url-rules-3.0.0",
};

describe("UrlAnalyzer page", () => {
  afterEach(() => vi.restoreAllMocks());

  it("analyzes a URL and renders the backend result", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(ok(RESULT));
    render(<UrlAnalyzer />);
    fireEvent.change(screen.getByTestId("url-input"), {
      target: { value: "http://jazzcash.secure-login.xyz" },
    });
    fireEvent.click(screen.getByTestId("url-submit"));
    await waitFor(() => screen.getByTestId("url-result"));
    expect(screen.getByTestId("risk-score").textContent).toBe("52");
    expect(screen.getByTestId("url-domain").textContent).toBe("jazzcash.secure-login.xyz");
    expect(screen.getByTestId("url-ind-brand_in_subdomain")).toBeInTheDocument();
    expect(screen.getByTestId("url-integrations").textContent).toContain("unavailable");
  });

  it("shows the security-blocked state", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      ok({ ...RESULT, blocked: true, classification: "HIGH RISK", risk_score: 78 }),
    );
    render(<UrlAnalyzer />);
    fireEvent.change(screen.getByTestId("url-input"), {
      target: { value: "http://127.0.0.1/" },
    });
    fireEvent.click(screen.getByTestId("url-submit"));
    await waitFor(() => screen.getByTestId("url-blocked"));
    expect(screen.getByTestId("url-blocked")).toBeInTheDocument();
  });

  it("preserves input and shows an error on failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(err("INVALID_URL"));
    render(<UrlAnalyzer />);
    const input = screen.getByTestId("url-input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "ftp://bad" } });
    fireEvent.click(screen.getByTestId("url-submit"));
    await waitFor(() => screen.getByTestId("url-error"));
    expect(input.value).toBe("ftp://bad");
  });
});
