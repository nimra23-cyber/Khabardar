/**
 * Dashboard: premium SOC overview with real stats + quick-access tools.
 * Fetches actual metrics from GET /api/dashboard/stats. Empty state is honest
 * (no fabricated data). Quick-access cards link to working tools.
 */
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useDashboardStats } from "../hooks/useDashboardStats";

const TOOLS: { to: string; titleKey: string; descKey: string; testId: string; icon: string }[] = [
  { to: "/detector", titleKey: "nav.detector", descKey: "dashboard.toolDetect", testId: "entry-detector", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
  { to: "/url", titleKey: "nav.url", descKey: "dashboard.toolUrl", testId: "entry-url", icon: "M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" },
  { to: "/scanner", titleKey: "nav.scanner", descKey: "dashboard.toolScan", testId: "entry-scanner", icon: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M8 8h.01M21 12V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-5" },
  { to: "/intelligence", titleKey: "nav.intelligence", descKey: "dashboard.toolIntel", testId: "entry-intelligence", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
];

function StatCard({ label, value, testId, accent }: { label: string; value: number; testId: string; accent?: string }) {
  return (
    <div
      data-testid={testId}
      className="rounded-lg border border-border-subtle bg-surface p-4 shadow-card card-hover"
    >
      <div className={`text-3xl font-bold tabular-nums ${accent || "text-fg"}`}>{value}</div>
      <div className="mt-1 text-xs font-medium uppercase tracking-wider text-fg/50">{label}</div>
    </div>
  );
}

export default function Dashboard() {
  const { t } = useTranslation();
  const { data: stats, loading, error } = useDashboardStats();

  return (
    <div data-testid="page-dashboard" className="mx-auto max-w-5xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("dashboard.title")}</h1>
        <p className="mt-1 text-sm text-fg/60">{t("dashboard.subtitle")}</p>
      </div>

      {/* Stats overview */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("dashboard.overview")}</h2>
        {loading && (
          <div className="grid grid-cols-2 gap-4 tablet:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-24 skeleton" />
            ))}
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger/10 p-4 text-sm text-danger" role="alert">
            {error.message}
          </div>
        )}
        {stats && (
          <>
            <div className="grid grid-cols-2 gap-4 tablet:grid-cols-4">
              <StatCard label={t("dashboard.totalScans")} value={stats.total_scans} testId="stat-total" />
              <StatCard label={t("dashboard.detectedScams")} value={stats.detected_scams} testId="stat-detected" accent="text-warning" />
              <StatCard label="SAFE" value={stats.risk_distribution.SAFE ?? 0} testId="stat-safe" accent="text-safe" />
              <StatCard label="HIGH RISK" value={stats.risk_distribution["HIGH RISK"] ?? 0} testId="stat-high" accent="text-danger" />
            </div>
            {stats.empty && (
              <div className="mt-4 rounded-lg border border-border-subtle bg-surface p-6 text-center" data-testid="stats-empty">
                <svg className="mx-auto mb-3 h-10 w-10 text-fg/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-sm text-fg/60">{t("dashboard.emptyState")}</p>
              </div>
            )}
          </>
        )}
      </section>

      {/* Quick access tools */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("dashboard.quickAccess")}</h2>
        <div className="grid grid-cols-1 gap-4 tablet:grid-cols-2 desktop:grid-cols-4">
          {TOOLS.map((tool) => (
            <Link
              key={tool.to}
              to={tool.to}
              data-testid={tool.testId}
              className="card-hover group rounded-lg border border-border-subtle bg-surface p-5 shadow-card hover:border-border-accent"
            >
              <div className="mb-3 inline-flex rounded-lg bg-accent/10 p-2.5 text-accent">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={tool.icon} />
                </svg>
              </div>
              <h3 className="font-medium text-fg">{t(tool.titleKey)}</h3>
              <p className="mt-0.5 text-xs text-fg/50">{t(tool.descKey)}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
