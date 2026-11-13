/**
 * ThemeToggle: switches between dark and light themes via ThemeContext.
 *
 * Presentation-light on purpose for Task 1.4 (icons/branding arrive later).
 * Uses semantic token utilities only -- no hardcoded colors.
 */
import { useTranslation } from "react-i18next";

import { useTheme } from "../context/ThemeContext";

export function ThemeToggle() {
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const label =
    theme === "dark" ? t("theme.switchToLight") : t("theme.switchToDark");

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={label}
      data-testid="theme-toggle"
      className="rounded border border-metallic-silver/30 bg-surface px-3 py-2 text-fg"
    >
      {t("theme.label")}: {theme}
    </button>
  );
}
