/** Intelligence page tests (Phase 5+6): renders real stats + IOC extraction. */
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import Intelligence from "./Intelligence";

const STATS = {
  total_scans: 5,
  detected_scams: 3,
  risk_distribution: { SAFE: 2, SUSPICIOUS: 2, "HIGH RISK": 1 },
  category_breakdown: { otp_theft: 1 },
  trend_30d: [{ date: "2025-01-01", count: 5 }],
  empty: false,
  public_demo: false,
  environment: "prototype",
};

const IOCS = {
  count: 2,
  iocs: [
    { ioc_type: "url", display_value: "http://evil.xyz", note: "Link extracted." },
    { ioc_type: "email", display_value: "****e.com", note: "Email (masked)." },
  ],
  integration_states: { virustotal: "unavailable" },
  note: "Local extraction only.",
};

function mockFetch() {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/api/dashboard/stats")) {
      return Promise.resolve({ ok: true, json: async () => ({ ok: true, data: STATS }) } as Response);
    }
    if (url.includes("/api/iocs/extract")) {
      return Promise.resolve({ ok: true, json: async () => ({ ok: true, data: IOCS }) } as Response);
    }
    return Promise.reject(new Error("unexpected url " + url));
  });
}

describe("Intelligence page", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders real dashboard stats", async () => {
    mockFetch();
    render(<Intelligence />);
    await waitFor(() => screen.getByTestId("stat-total"));
    expect(screen.getByTestId("stat-total").textContent).toContain("5");
    expect(screen.getByTestId("stat-detected").textContent).toContain("3");
    expect(screen.getByTestId("prototype-label")).toBeInTheDocument();
  });

  it("extracts IOCs from submitted text", async () => {
    mockFetch();
    render(<Intelligence />);
    await waitFor(() => screen.getByTestId("stat-total"));
    fireEvent.change(screen.getByTestId("ioc-input"), {
      target: { value: "see http://evil.xyz and a@b.com" },
    });
    fireEvent.click(screen.getByTestId("ioc-submit"));
    await waitFor(() => screen.getByTestId("ioc-result"));
    const items = screen.getAllByTestId("ioc-item");
    expect(items.length).toBe(2);
  });

  it("shows honest empty state when no data", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.includes("/api/dashboard/stats")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ ok: true, data: { ...STATS, total_scans: 0, detected_scams: 0, empty: true, risk_distribution: { SAFE: 0, SUSPICIOUS: 0, "HIGH RISK": 0 } } }),
        } as Response);
      }
      return Promise.reject(new Error("x"));
    });
    render(<Intelligence />);
    await waitFor(() => screen.getByTestId("stats-empty"));
    expect(screen.getByTestId("stats-empty")).toBeInTheDocument();
  });
});
