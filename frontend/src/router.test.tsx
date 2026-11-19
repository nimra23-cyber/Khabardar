import { act, render, screen } from "@testing-library/react";
import {
  RouterProvider,
  createMemoryRouter,
} from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LOGO_SRC } from "./components/SplashLogo";
import { LanguageProvider } from "./context/LanguageContext";
import { ThemeProvider } from "./context/ThemeContext";
import { SPLASH_DURATION_MS } from "./pages/Splash";
import { routes } from "./router";

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  return {
    router,
    ...render(
      <LanguageProvider>
        <ThemeProvider>
          <RouterProvider router={router} />
        </ThemeProvider>
      </LanguageProvider>,
    ),
  };
}

const APP_ROUTES: { path: string; testId: string }[] = [
  { path: "/dashboard", testId: "page-dashboard" },
  { path: "/detector", testId: "page-detector" },
  { path: "/url", testId: "page-url" },
  { path: "/scanner", testId: "page-scanner" },
  { path: "/intelligence", testId: "page-intelligence" },
  { path: "/honeypot", testId: "page-honeypot" },
  { path: "/family", testId: "page-family" },
  { path: "/history", testId: "page-history" },
  { path: "/reports", testId: "page-reports" },
  { path: "/settings", testId: "page-settings" },
  { path: "/about", testId: "page-about" },
];

describe("Router: all routes render", () => {
  it.each(APP_ROUTES)("renders $path", ({ path, testId }) => {
    renderAt(path);
    expect(screen.getByTestId(testId)).toBeInTheDocument();
  });

  it("renders the splash at /", () => {
    vi.useFakeTimers();
    renderAt("/");
    expect(screen.getByTestId("splash-screen")).toBeInTheDocument();
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });
});

describe("Router: splash transitions to /dashboard after ~2s", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("navigates to the dashboard when the splash completes", async () => {
    const { router } = renderAt("/");
    expect(screen.getByTestId("splash-screen")).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(SPLASH_DURATION_MS);
    });

    expect(router.state.location.pathname).toBe("/dashboard");
    expect(screen.getByTestId("page-dashboard")).toBeInTheDocument();
  });
});

describe("Router: Scope B placeholders have genuinely disabled controls", () => {
  it.each([
    { path: "/honeypot", page: "page-honeypot" },
    { path: "/family", page: "page-family" },
  ])("$path shows a Scope B unavailable state with a disabled action", ({ path, page }) => {
    renderAt(path);
    expect(screen.getByTestId(page)).toBeInTheDocument();
    expect(screen.getByTestId("scope-b-unavailable")).toBeInTheDocument();
    const btn = screen.getByTestId("disabled-action") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
    expect(btn.getAttribute("aria-disabled")).toBe("true");
  });
});

describe("Router: not-implemented pages are honest (no fake functionality)", () => {
  // /detector, /history, /url, /intelligence, /reports, /scanner are now FUNCTIONAL
  // and excluded here. All previous placeholders have been replaced with real UIs.
  it("scanner page is now implemented and renders the upload form", () => {
    renderAt("/scanner");
    expect(screen.getByTestId("page-scanner")).toBeInTheDocument();
    expect(screen.getByTestId("scanner-file-input")).toBeInTheDocument();
  });
});

describe("NavBar: active-state styling and dashboard entry points", () => {
  it("marks the active destination distinctly", () => {
    renderAt("/detector");
    // Sidebar renders nav links in both mobile drawer and desktop sidebar.
    const activeLinks = screen.getAllByTestId("nav-detector");
    const active = activeLinks[0];
    expect(active.className).toContain("active-nav");
    // A non-active link does not carry the active marker.
    const aboutLinks = screen.getAllByTestId("nav-about");
    expect(aboutLinks[0].className).not.toContain("active-nav");
  });

  it("dashboard presents entry points to detector/url/scanner/intelligence", () => {
    renderAt("/dashboard");
    for (const id of ["entry-detector", "entry-url", "entry-scanner", "entry-intelligence"]) {
      expect(screen.getByTestId(id)).toBeInTheDocument();
    }
  });

  it("clicking a dashboard entry point navigates to its route", async () => {
    const { router } = renderAt("/dashboard");
    await act(async () => {
      screen.getByTestId("entry-detector").click();
    });
    expect(router.state.location.pathname).toBe("/detector");
    expect(screen.getByTestId("page-detector")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Regression lock (splash-not-appearing bug): the four required behaviors.
// ---------------------------------------------------------------------------
describe("Regression: splash entry behavior", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("/ displays the Splash first (logo + name + tagline)", () => {
    renderAt("/");
    expect(screen.getByTestId("splash-screen")).toBeInTheDocument();
    // Name and tagline present.
    expect(screen.getByText("KHABARDAR")).toBeInTheDocument();
    expect(screen.getByText("Think Before You Trust.")).toBeInTheDocument();
    // Dashboard content is NOT shown underneath the splash yet.
    expect(screen.queryByTestId("page-dashboard")).toBeNull();
  });

  it("Splash logo points to the correct official asset", () => {
    renderAt("/");
    const img = screen.getByTestId("splash-logo-img") as HTMLImageElement;
    expect(img.getAttribute("src")).toBe(LOGO_SRC);
    expect(LOGO_SRC).toBe("/assets/Khabardar_Logo.png");
  });

  it("Splash transitions to /dashboard after ~2s", async () => {
    const { router } = renderAt("/");
    await act(async () => {
      vi.advanceTimersByTime(SPLASH_DURATION_MS);
    });
    expect(router.state.location.pathname).toBe("/dashboard");
    expect(screen.getByTestId("page-dashboard")).toBeInTheDocument();
    expect(screen.queryByTestId("splash-screen")).toBeNull();
  });

  it("direct navigation to /dashboard does NOT display the Splash", () => {
    renderAt("/dashboard");
    expect(screen.getByTestId("page-dashboard")).toBeInTheDocument();
    expect(screen.queryByTestId("splash-screen")).toBeNull();
  });
});
