/**
 * Threat Intelligence (SOC): premium stat cards + IOC extraction.
 * Preserves all testids and API integration.
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useDashboardStats } from "../hooks/useDashboardStats";
import { useIocExtract } from "../hooks/useIocExtract";

function StatCard({ label, value, testId, accent }: { label: string; value: number; testId: string; accent?: string }) {
  return (
    <div data-testid={testId} className="rounded-lg border border-border-subtle bg-surface p-4 shadow-card card-hover">
      <div className={`text-3xl font-bold tabular-nums ${accent || "text-fg"}`}>{value}</div>
      <div className="mt-1 text-xs font-medium uppercase tracking-wider text-fg/50">{label}</div>
    </div>
  );
}

export default function Intelligence() {
  const { t } = useTranslation();
  const { data: stats, loading, error } = useDashboardStats();
  const [iocText, setIocText] = useState("");
  const ioc = useIocExtract();

  return (
    <div data-testid="page-intelligence" className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("nav.intelligence")}</h1>
        <p className="mt-1 text-xs text-warning" data-testid="prototype-label">{t("intel.prototype")}</p>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("intel.overview")}</h2>
        {loading && <div className="grid grid-cols-2 gap-3 tablet:grid-cols-4">{[0,1,2,3].map(i => <div key={i} className="h-24 skeleton" />)}</div>}
        {error && <div role="alert" className="rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger" data-testid="stats-error">{error.message}</div>}
        {stats && (
          <>
            <div className="grid grid-cols-2 gap-3 tablet:grid-cols-4">
              <StatCard label={t("intel.totalScans")} value={stats.total_scans} testId="stat-total" />
              <StatCard label={t("intel.detectedScams")} value={stats.detected_scams} testId="stat-detected" accent="text-warning" />
              <StatCard label="SAFE" value={stats.risk_distribution.SAFE ?? 0} testId="stat-safe" accent="text-safe" />
              <StatCard label="HIGH RISK" value={stats.risk_distribution["HIGH RISK"] ?? 0} testId="stat-high" accent="text-danger" />
            </div>
            {stats.empty && (
              <div className="mt-4 rounded-lg border border-border-subtle bg-surface p-6 text-center" data-testid="stats-empty">
                <svg className="mx-auto mb-3 h-10 w-10 text-fg/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-sm text-fg/50">{t("intel.emptyState")}</p>
              </div>
            )}
          </>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("intel.iocTitle")}</h2>
        <p className="mb-3 text-sm text-fg/60">{t("intel.iocSubtitle")}</p>
        <textarea
          data-testid="ioc-input"
          value={iocText}
          onChange={(e) => setIocText(e.target.value)}
          rows={4}
          dir="auto"
          className="w-full rounded-lg border border-border-default bg-surface p-4 text-fg shadow-card transition-base placeholder:text-fg/30 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          placeholder={t("intel.iocPlaceholder")}
        />
        <div className="mt-2 flex justify-end">
          <button type="button" data-testid="ioc-submit" disabled={iocText.trim().length < 1 || ioc.loading} onClick={() => ioc.extract(iocText)}
            className="rounded-lg bg-accent px-6 py-2.5 font-medium text-white shadow-card transition-base hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40">
            {ioc.loading ? (
              <span className="flex items-center gap-2">
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.25" /><path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
                {t("intel.extracting")}
              </span>
            ) : t("intel.extract")}
          </button>
        </div>

        {ioc.error && <div role="alert" className="mt-3 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger" data-testid="ioc-error">{ioc.error.message}</div>}
        {ioc.result && (
          <div data-testid="ioc-result" className="mt-4 space-y-3">
            {ioc.result.count === 0 ? (
              <p className="text-sm text-fg/50" data-testid="ioc-none">{t("intel.iocNone")}</p>
            ) : (
              <ul className="space-y-2">
                {ioc.result.iocs.map((it, i) => (
                  <li key={i} data-testid="ioc-item" className="card-hover flex items-center gap-3 rounded-lg border border-border-subtle bg-surface p-3 shadow-card">
                    <span className="rounded-md border border-border-subtle bg-bg/40 px-2 py-0.5 text-xs font-semibold uppercase text-accent">{it.ioc_type}</span>
                    <code className="font-mono text-sm text-fg/80">{it.display_value}</code>
                    <span className="ml-auto text-xs text-fg/40">{it.note}</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="text-xs text-fg/40">{ioc.result.note}</p>
          </div>
        )}
      </section>
    </div>
  );
}
