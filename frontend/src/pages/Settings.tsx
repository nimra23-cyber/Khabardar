/**
 * Settings page (Task 1.7 shell).
 *
 * Theme and language controls are genuinely functional (delivered in Tasks
 * 1.4/1.5), so they are shown as working controls. Retention configuration is
 * NOT yet implemented (backend arrives in a later task); it is labeled honestly
 * and not presented as functional.
 */
import { useTranslation } from "react-i18next";

import { LanguageToggle } from "../components/LanguageToggle";
import { ThemeToggle } from "../components/ThemeToggle";

export default function Settings() {
  const { t } = useTranslation();
  return (
    <div data-testid="page-settings">
      <h1 className="mb-4 text-2xl font-semibold">{t("nav.settings")}</h1>

      <section className="mb-4 rounded-lg border border-metallic-silver/30 bg-surface p-4">
        <h2 className="mb-3 font-medium">{t("settings.appearance")}</h2>
        <div className="flex flex-wrap items-center gap-4">
          <ThemeToggle />
          <LanguageToggle />
        </div>
      </section>

      <section className="rounded-lg border border-metallic-silver/30 bg-surface p-4">
        <h2 className="mb-2 font-medium">{t("settings.retention")}</h2>
        {/* Honest: retention config is not implemented yet. */}
        <p data-testid="settings-retention-unavailable" className="text-sm text-fg/80">
          {t("unavailable.notImplemented")}
        </p>
      </section>
    </div>
  );
}
