import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LanguageToggle } from "../components/LanguageToggle";
import i18n, {
  DEFAULT_LANGUAGE,
  LANGUAGE_STORAGE_KEY,
  readStoredLanguage,
} from "../i18n";
import { LanguageProvider, useLanguage } from "./LanguageContext";

function renderToggle() {
  return render(
    <LanguageProvider>
      <LanguageToggle />
    </LanguageProvider>,
  );
}

describe("LanguageContext / i18n", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("lang");
    document.documentElement.removeAttribute("dir");
    await i18n.changeLanguage("en");
    vi.restoreAllMocks();
  });

  it("defaults to English when no stored selection exists", () => {
    expect(DEFAULT_LANGUAGE).toBe("en");
    expect(readStoredLanguage()).toBe("en");
    renderToggle();
    expect(screen.getByTestId<HTMLSelectElement>("language-select").value).toBe("en");
  });

  it("falls back to English for an invalid stored value", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "fr");
    expect(readStoredLanguage()).toBe("en");
  });

  it("falls back to English when storage is unavailable (getItem throws)", () => {
    const spy = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("unavailable");
    });
    expect(readStoredLanguage()).toBe("en");
    spy.mockRestore();
  });

  it("persists the selected language under khabardar.lang", async () => {
    renderToggle();
    const select = screen.getByTestId<HTMLSelectElement>("language-select");
    await act(async () => {
      select.value = "ur-Latn";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("ur-Latn");
  });

  it("does not crash when setItem throws (persist failure is non-fatal)", async () => {
    const spy = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    renderToggle();
    const select = screen.getByTestId<HTMLSelectElement>("language-select");
    await act(async () => {
      select.value = "ur";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    // In-memory switch still applied.
    expect(i18n.resolvedLanguage).toBe("ur");
    spy.mockRestore();
  });

  it("sets document lang/dir correctly for each language", async () => {
    renderToggle();
    const select = screen.getByTestId<HTMLSelectElement>("language-select");

    // Urdu script -> rtl.
    await act(async () => {
      select.value = "ur";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(document.documentElement.getAttribute("lang")).toBe("ur");
    expect(document.documentElement.getAttribute("dir")).toBe("rtl");

    // Roman Urdu -> ltr.
    await act(async () => {
      select.value = "ur-Latn";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(document.documentElement.getAttribute("lang")).toBe("ur-Latn");
    expect(document.documentElement.getAttribute("dir")).toBe("ltr");

    // English -> ltr.
    await act(async () => {
      select.value = "en";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(document.documentElement.getAttribute("lang")).toBe("en");
    expect(document.documentElement.getAttribute("dir")).toBe("ltr");
  });

  it("LanguageToggle switches the rendered language", async () => {
    renderToggle();
    const select = screen.getByTestId<HTMLSelectElement>("language-select");
    // Default English label for the 'language.label' key.
    expect(screen.getByTestId("language-toggle")).toHaveTextContent("Language");

    await act(async () => {
      select.value = "ur";
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    // Urdu label for 'language.label'.
    expect(screen.getByTestId("language-toggle")).toHaveTextContent("زبان");
  });

  it("useLanguage throws outside a provider", () => {
    function Orphan() {
      useLanguage();
      return null;
    }
    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Orphan />)).toThrow(
      /useLanguage must be used within a LanguageProvider/,
    );
    errSpy.mockRestore();
  });
});
