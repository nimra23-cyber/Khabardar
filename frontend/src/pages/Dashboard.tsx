/**
 * Dashboard: the Main Dashboard shell (Req 3.6).
 *
 * Presents a distinct, selectable entry point for each of the Scam Detector,
 * URL Analyzer, Media Scanner, and SOC (Threat Intelligence). Each entry point
 * navigates to its route. This is the real dashboard shell; the per-feature
 * functionality is delivered by later tasks and the target pages state that
 * honestly.
 */
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

const ENTRY_POINTS: { to: string; titleKey: string; testId: string }[] = [
  { to: "/detector", titleKey: "nav.detector", testId: "entry-detector" },
  { to: "/url", titleKey: "nav.url", testId: "entry-url" },
  { to: "/scanner", titleKey: "nav.scanner", testId: "entry-scanner" },
  { to: "/intelligence", titleKey: "nav.intelligence", testId: "entry-intelligence" },
];

export default function Dashboard() {
  const { t } = useTranslation();

  return (
    <div data-testid="page-dashboard">
      <h1 className="mb-1 text-2xl font-semibold">{t("dashboard.title")}</h1>
      <p className="mb-6 text-sm text-fg/80">{t("dashboard.subtitle")}</p>

      <div className="grid grid-cols-1 gap-4 tablet:grid-cols-2 desktop:grid-cols-4">
        {ENTRY_POINTS.map((e) => (
          <Link
            key={e.to}
            to={e.to}
            data-testid={e.testId}
            className="block rounded-lg border border-metallic-silver/30 bg-surface p-4 hover:border-accent"
          >
            <span className="font-medium">{t(e.titleKey)}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
