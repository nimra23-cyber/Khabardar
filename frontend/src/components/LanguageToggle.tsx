/**
 * LanguageToggle: selects the active interface language via LanguageContext.
 *
 * A native <select> keeps this accessible and simple for Task 1.5. Labels come
 * from translation keys; the brand name is never translated. Uses semantic
 * token utilities only (no hardcoded colors), consistent with Task 1.4.
 */
import { useTranslation } from "react-i18next";

import { useLanguage } from "../context/LanguageContext";
import type { SupportedLanguage } from "../i18n";

export function LanguageToggle() {
  const { t } = useTranslation();
  const { language, setLanguage } = useLanguage();

  return (
    <label className="flex items-center gap-2 text-fg" data-testid="language-toggle">
      <span className="text-sm">{t("language.label")}</span>
      <select
        aria-label={t("language.label")}
        data-testid="language-select"
        value={language}
        onChange={(e) => setLanguage(e.target.value as SupportedLanguage)}
        className="rounded border border-metallic-silver/30 bg-surface px-2 py-1 text-fg"
      >
        <option value="en">{t("language.english")}</option>
        <option value="ur">{t("language.urdu")}</option>
        <option value="ur-Latn">{t("language.romanUrdu")}</option>
      </select>
    </label>
  );
}
