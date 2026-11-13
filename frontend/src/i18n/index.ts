/**
 * i18next initialization -- the SINGLE SOURCE OF TRUTH for the active language.
 *
 * - Three separately-authored bundles: `en`, `ur` (Urdu script), `ur-Latn`
 *   (Roman Urdu). Roman Urdu is authored, NOT auto-transliterated.
 * - Default language: English (Req 4.3).
 * - Fallback language: English for any missing key (Req 4.4).
 * - Initial language resolved from localStorage key `khabardar.lang`, falling
 *   back to English when absent, invalid, or storage is unavailable (Req 4.2).
 *
 * LanguageContext reads/writes the active language through i18next; it does not
 * keep a duplicate copy of the language state.
 */
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./en.json";
import ur from "./ur.json";
import urLatn from "./ur-Latn.json";

export const LANGUAGE_STORAGE_KEY = "khabardar.lang";
export const DEFAULT_LANGUAGE = "en";
export const SUPPORTED_LANGUAGES = ["en", "ur", "ur-Latn"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

/** Languages that use right-to-left script. Only Urdu script is RTL. */
const RTL_LANGUAGES: ReadonlySet<string> = new Set(["ur"]);

export function isSupportedLanguage(value: unknown): value is SupportedLanguage {
  return (
    typeof value === "string" &&
    (SUPPORTED_LANGUAGES as readonly string[]).includes(value)
  );
}

/** Direction for a language: rtl only for Urdu script, ltr otherwise. */
export function directionFor(language: string): "rtl" | "ltr" {
  return RTL_LANGUAGES.has(language) ? "rtl" : "ltr";
}

/** Read the stored language safely; default to English on any problem. */
export function readStoredLanguage(): SupportedLanguage {
  try {
    const raw = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return isSupportedLanguage(raw) ? raw : DEFAULT_LANGUAGE;
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

/** Persist the language safely; ignore storage failures (non-fatal). */
export function writeStoredLanguage(language: SupportedLanguage): void {
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch {
    // Non-fatal: persistence unavailable; in-memory language still applies.
  }
}

/** Apply lang + dir to the document root for the given language. */
export function applyDocumentLanguage(language: string): void {
  if (typeof document !== "undefined") {
    const root = document.documentElement;
    root.setAttribute("lang", language);
    root.setAttribute("dir", directionFor(language));
  }
}

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ur: { translation: ur },
    "ur-Latn": { translation: urLatn },
  },
  lng: readStoredLanguage(),
  fallbackLng: DEFAULT_LANGUAGE,
  supportedLngs: SUPPORTED_LANGUAGES as unknown as string[],
  // A missing key in the active language falls back to English (Req 4.4).
  returnEmptyString: false,
  interpolation: { escapeValue: false },
});

export default i18n;
