/**
 * ThemeContext: dark-default theme with safe, persistent light/dark switching.
 *
 * Behaviors (Task 1.4 / Req 2.2, 2.3, 2.4):
 * - Dark is the default when no saved preference exists.
 * - The preference persists to localStorage and is restored after reload.
 * - Safe fallback to dark if localStorage is unavailable (e.g. disabled /
 *   throws) or contains an invalid value.
 * - The theme is applied at the document root (`<html data-theme="...">`), the
 *   same attribute the pre-hydration bootstrap in index.html sets, so there is
 *   no visible wrong-theme flash on load.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { ThemeName } from "../styles/palette";

export const THEME_STORAGE_KEY = "khabardar.theme";
export const DEFAULT_THEME: ThemeName = "dark";

interface ThemeContextValue {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function isValidTheme(value: unknown): value is ThemeName {
  return value === "dark" || value === "light";
}

/** Read the saved theme safely; fall back to the default on any problem. */
export function readStoredTheme(): ThemeName {
  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY);
    return isValidTheme(raw) ? raw : DEFAULT_THEME;
  } catch {
    // localStorage unavailable (disabled, privacy mode, SSR, etc.).
    return DEFAULT_THEME;
  }
}

/** Persist the theme safely; ignore storage failures (non-fatal). */
function writeStoredTheme(theme: ThemeName): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Non-fatal: persistence unavailable; in-memory theme still applies.
  }
}

/** Apply the theme at the document root. */
export function applyThemeToDocument(theme: ThemeName): void {
  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("data-theme", theme);
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeName>(() => readStoredTheme());

  // Keep the document root and storage in sync whenever the theme changes.
  useEffect(() => {
    applyThemeToDocument(theme);
    writeStoredTheme(theme);
  }, [theme]);

  const setTheme = useCallback((next: ThemeName) => {
    setThemeState(isValidTheme(next) ? next : DEFAULT_THEME);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const value = useMemo(
    () => ({ theme, setTheme, toggleTheme }),
    [theme, setTheme, toggleTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (ctx === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
}
