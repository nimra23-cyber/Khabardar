import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeToggle } from "../components/ThemeToggle";
import {
  DEFAULT_THEME,
  THEME_STORAGE_KEY,
  ThemeProvider,
  readStoredTheme,
  useTheme,
} from "./ThemeContext";

function renderWithProvider() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>,
  );
}

describe("ThemeContext", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    vi.restoreAllMocks();
  });

  it("defaults to dark on first visit (no saved preference)", () => {
    expect(DEFAULT_THEME).toBe("dark");
    renderWithProvider();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(screen.getByTestId("theme-toggle")).toHaveTextContent("Theme: dark");
  });

  it("persists the selected theme to localStorage", () => {
    renderWithProvider();
    const toggle = screen.getByTestId("theme-toggle");
    act(() => {
      toggle.click();
    });
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("restores a saved dark preference after reload", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "dark");
    renderWithProvider();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(screen.getByTestId("theme-toggle")).toHaveTextContent("Theme: dark");
  });

  it("restores a saved light preference after reload", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "light");
    renderWithProvider();
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(screen.getByTestId("theme-toggle")).toHaveTextContent("Theme: light");
  });

  it("falls back to dark when the saved value is invalid", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "neon-purple");
    expect(readStoredTheme()).toBe("dark");
    renderWithProvider();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("falls back to dark when localStorage.getItem throws (unavailable)", () => {
    const spy = vi
      .spyOn(Storage.prototype, "getItem")
      .mockImplementation(() => {
        throw new Error("localStorage unavailable");
      });
    expect(readStoredTheme()).toBe("dark");
    renderWithProvider();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    spy.mockRestore();
  });

  it("does not crash when localStorage.setItem throws (persist failure is non-fatal)", () => {
    const spy = vi
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new Error("quota exceeded");
      });
    renderWithProvider();
    const toggle = screen.getByTestId("theme-toggle");
    // Toggling must still update the in-memory theme and the document root.
    act(() => {
      toggle.click();
    });
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    spy.mockRestore();
  });

  it("ThemeToggle switches dark <-> light on click", () => {
    renderWithProvider();
    const toggle = screen.getByTestId("theme-toggle");
    expect(toggle).toHaveTextContent("Theme: dark");
    act(() => toggle.click());
    expect(toggle).toHaveTextContent("Theme: light");
    act(() => toggle.click());
    expect(toggle).toHaveTextContent("Theme: dark");
  });

  it("useTheme throws outside a provider", () => {
    function Orphan() {
      useTheme();
      return null;
    }
    // Suppress React's error logging noise for this expected throw.
    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Orphan />)).toThrow(/useTheme must be used within a ThemeProvider/);
    errSpy.mockRestore();
  });
});
