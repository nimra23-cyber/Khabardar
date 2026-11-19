/**
 * LanguageToggle: compact language selector.
 */
import { useTranslation } from "react-i18next";

import { useLanguage } from "../context/LanguageContext";
import type { SupportedLanguage } from "../i18n";

export function LanguageToggle() {
  const { t } = useTranslation();
  const { language, setLanguage } = useLanguage();

  return (
    <label className="flex items-center gap-1.5 text-fg" data-testid="language-toggle">
      <span className="hidden desktop:inline text-xs">{t("language.label")}</span>
      <select
        aria-label={t("language.label")}
        data-testid="language-select"
        value={language}
        onChange={(e) => setLanguage(e.target.value as SupportedLanguage)}
        className="rounded-md border border-border-default bg-surface px-2 py-1.5 text-xs text-fg/70 transition-base hover:bg-surface-hover hover:text-fg"
      >
        <option value="en">{t("language.english")}</option>
        <option value="ur">{t("language.urdu")}</option>
        <option value="ur-Latn">{t("language.romanUrdu")}</option>
      </select>
    </label>
  );
}
