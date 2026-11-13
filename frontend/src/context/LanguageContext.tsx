/**
 * LanguageContext: thin provider over i18next (the single source of truth).
 *
 * It does NOT hold a duplicate language value; `language` is read from
 * i18next and kept in sync via i18next's `languageChanged` event. `setLanguage`
 * delegates to `i18n.changeLanguage`, then persists and applies lang/dir.
 *
 * Behaviors:
 * - Default English when no valid stored selection (handled by i18n init).
 * - Persist selection under `khabardar.lang`.
 * - Apply `lang` + `dir` on <html> (Urdu script => rtl; en / ur-Latn => ltr).
 * - Safe fallback to English on invalid input.
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

import i18n, {
  DEFAULT_LANGUAGE,
  applyDocumentLanguage,
  isSupportedLanguage,
  writeStoredLanguage,
  type SupportedLanguage,
} from "../i18n";

interface LanguageContextValue {
  language: SupportedLanguage;
  setLanguage: (language: SupportedLanguage) => void;
  dir: "rtl" | "ltr";
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

function currentI18nLanguage(): SupportedLanguage {
  const lng = i18n.resolvedLanguage ?? i18n.language;
  return isSupportedLanguage(lng) ? lng : DEFAULT_LANGUAGE;
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  // Mirror of i18next's language for render purposes ONLY; i18next remains the
  // source of truth. Kept in sync via the languageChanged subscription below.
  const [language, setLanguageMirror] = useState<SupportedLanguage>(
    () => currentI18nLanguage(),
  );

  // Ensure the document reflects the initial language on mount.
  useEffect(() => {
    applyDocumentLanguage(language);
  }, [language]);

  // Subscribe to i18next so any language change (from anywhere) updates us.
  useEffect(() => {
    const onChanged = () => {
      const next = currentI18nLanguage();
      setLanguageMirror(next);
      applyDocumentLanguage(next);
    };
    i18n.on("languageChanged", onChanged);
    return () => {
      i18n.off("languageChanged", onChanged);
    };
  }, []);

  const setLanguage = useCallback((next: SupportedLanguage) => {
    const target = isSupportedLanguage(next) ? next : DEFAULT_LANGUAGE;
    // i18next is the source of truth; changing it triggers languageChanged,
    // which updates the mirror and the document. Persist the selection too.
    void i18n.changeLanguage(target);
    writeStoredLanguage(target);
  }, []);

  const value = useMemo<LanguageContextValue>(
    () => ({
      language,
      setLanguage,
      dir: language === "ur" ? "rtl" : "ltr",
    }),
    [language, setLanguage],
  );

  return (
    <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (ctx === undefined) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return ctx;
}
