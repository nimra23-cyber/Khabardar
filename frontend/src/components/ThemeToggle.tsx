/**
 * ThemeToggle: compact icon-based theme switcher.
 */
import { useTranslation } from "react-i18next";

import { useTheme } from "../context/ThemeContext";

export function ThemeToggle() {
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const label = theme === "dark" ? t("theme.switchToLight") : t("theme.switchToDark");

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={label}
      title={label}
      data-testid="theme-toggle"
      className="rounded-md border border-border-default bg-surface px-2 py-1.5 text-xs text-fg/70 transition-base hover:bg-surface-hover hover:text-fg"
    >
      <span className="hidden desktop:inline">{t("theme.label")}</span>: {theme}
    </button>
  );
}
