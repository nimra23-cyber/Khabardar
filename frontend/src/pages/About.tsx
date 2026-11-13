/**
 * About page (Task 1.7). Static, genuinely functional informational content.
 */
import { useTranslation } from "react-i18next";

export default function About() {
  const { t } = useTranslation();
  return (
    <div data-testid="page-about">
      <h1 className="mb-2 text-2xl font-semibold">
        <bdi dir="ltr">{t("app.name")}</bdi>
      </h1>
      <p className="mb-4 text-sm text-fg/80">{t("app.tagline")}</p>
      <p className="max-w-prose text-sm">{t("about.body")}</p>
      {/* Honest prototype label (Req 15.8 / 22 spirit): this is a local
          prototype, not a live nationwide service. */}
      <p className="mt-4 text-xs text-fg/60">{t("about.prototypeNote")}</p>
    </div>
  );
}
