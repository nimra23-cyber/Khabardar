/**
 * About: premium info page with icon.
 * Preserves testid.
 */
import { useTranslation } from "react-i18next";

export default function About() {
  const { t } = useTranslation();
  return (
    <div data-testid="page-about" className="mx-auto max-w-lg">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">
          <bdi dir="ltr">{t("app.name")}</bdi>
        </h1>
        <p className="mt-1 text-sm text-fg/60">{t("app.tagline")}</p>
      </div>

      <div className="rounded-lg border border-border-subtle bg-surface p-6 shadow-card">
        <div className="mb-4 inline-flex rounded-lg bg-accent/10 p-3 text-accent">
          <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 5.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <p className="mb-4 text-sm text-fg/70">{t("about.body")}</p>
        <div className="rounded-lg border border-warning/20 bg-warning/5 p-3">
          <p className="text-xs text-warning/80">{t("about.prototypeNote")}</p>
        </div>
      </div>
    </div>
  );
}
