/**
 * Settings: premium appearance + retention sections.
 * Preserves all testids.
 */
import { useTranslation } from "react-i18next";

import { LanguageToggle } from "../components/LanguageToggle";
import { ThemeToggle } from "../components/ThemeToggle";

export default function Settings() {
  const { t } = useTranslation();
  return (
    <div data-testid="page-settings" className="mx-auto max-w-lg space-y-4">
      <div className="mb-2">
        <h1 className="text-2xl font-bold tracking-tight">{t("nav.settings")}</h1>
      </div>

      <section className="rounded-lg border border-border-subtle bg-surface p-5 shadow-card">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("settings.appearance")}</h2>
        <div className="flex flex-wrap items-center gap-4">
          <ThemeToggle />
          <LanguageToggle />
        </div>
      </section>

      <section className="rounded-lg border border-border-subtle bg-surface p-5 shadow-card">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("settings.retention")}</h2>
        <p data-testid="settings-retention-unavailable" className="text-sm text-fg/50">{t("unavailable.notImplemented")}</p>
      </section>
    </div>
  );
}
