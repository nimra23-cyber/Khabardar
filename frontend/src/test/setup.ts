// Vitest setup: register jest-dom matchers and reset DOM/storage between tests.
import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach } from "vitest";

// Initialize i18next once for all tests so components using useTranslation()
// resolve real strings (default English). Importing the module runs init().
import i18n from "../i18n";

beforeEach(async () => {
  // Start each test from a clean slate.
  try {
    window.localStorage.clear();
  } catch {
    // ignore if unavailable
  }
  document.documentElement.removeAttribute("data-theme");
  document.documentElement.removeAttribute("lang");
  document.documentElement.removeAttribute("dir");
  // Reset i18next to the default language so tests are independent.
  // Awaited for deterministic isolation (changeLanguage is async).
  await i18n.changeLanguage("en");
});

afterEach(async () => {
  document.documentElement.removeAttribute("data-theme");
  document.documentElement.removeAttribute("lang");
  document.documentElement.removeAttribute("dir");
  await i18n.changeLanguage("en");
});
