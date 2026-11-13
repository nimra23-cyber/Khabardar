/**
 * Threat Intelligence (SOC) page (Phase 5 + 6).
 *
 * Two real, backend-driven sections:
 *  1. SOC stats from GET /api/dashboard/stats — real counts, honest empty
 *     state (all zeros) when nothing is persisted (e.g. public-demo mode).
 *  2. IOC extraction via POST /api/iocs/extract — extracts + masks indicators
 *     from submitted text; external reputation sources shown "unavailable".
 *
 * Labeled a prototype environment (Req 15.8). No fabricated statistics.
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useDashboardStats } from "../hooks/useDashboardStats";
import { useIocExtract } from "../hooks/useIocExtract";

function StatCard({ label, value, testId }: { label: string; value: number; testId: string }) {
  return (
    <div
      data-testid={testId}
      className="rounded-lg border border-metallic-silver/30 bg-surface p-4"
    >
      <div className="text-3xl font-bold tabular-nums">{value}</div>
      <div className="text-xs text-fg/70">{label}</div>
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
        <h1 className="mb-1 text-2xl font-semibold">{t("nav.intelligence")}</h1>
        <p className="text-xs text-warning" data-testid="prototype-label">
          {t("intel.prototype")}
        </p>
      </div>

      {/* SOC stats */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">{t("intel.overview")}</h2>
        {loading && <p className="text-sm text-fg/60">…</p>}
        {error && (
          <div role="alert" className="text-sm text-danger" data-testid="stats-error">
            {error.message}
          </div>
        )}
        {stats && (
          <>
            <div className="grid grid-cols-2 gap-3 tablet:grid-cols-4">
              <StatCard label={t("intel.totalScans")} value={stats.total_scans} testId="stat-total" />
              <StatCard label={t("intel.detectedScams")} value={stats.detected_scams} testId="stat-detected" />
              <StatCard label="SAFE" value={stats.risk_distribution.SAFE ?? 0} testId="stat-safe" />
              <StatCard
                label="HIGH RISK"
                value={stats.risk_distribution["HIGH RISK"] ?? 0}
                testId="stat-high"
              />
            </div>
            {stats.empty && (
              <p className="mt-3 text-sm text-fg/70" data-testid="stats-empty">
                {t("intel.emptyState")}
              </p>
            )}
          </>
        )}
      </section>

      {/* IOC extraction */}
      <section>
        <h2 className="mb-2 text-lg font-semibold">{t("intel.iocTitle")}</h2>
        <p className="mb-3 text-sm text-fg/80">{t("intel.iocSubtitle")}</p>
        <textarea
          data-testid="ioc-input"
          value={iocText}
          onChange={(e) => setIocText(e.target.value)}
          rows={4}
          dir="auto"
          className="w-full rounded-lg border border-metallic-silver/30 bg-surface p-3 text-fg focus:border-accent focus:outline-none"
          placeholder={t("intel.iocPlaceholder")}
        />
        <div className="mt-2 flex justify-end">
          <button
            type="button"
            data-testid="ioc-submit"
            disabled={iocText.trim().length < 1 || ioc.loading}
            onClick={() => ioc.extract(iocText)}
            className="rounded-lg bg-accent px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {ioc.loading ? t("intel.extracting") : t("intel.extract")}
          </button>
        </div>

        {ioc.error && (
          <div role="alert" className="mt-3 text-sm text-danger" data-testid="ioc-error">
            {ioc.error.message}
          </div>
        )}

        {ioc.result && (
          <div data-testid="ioc-result" className="mt-4 space-y-3">
            {ioc.result.count === 0 ? (
              <p className="text-sm text-fg/70" data-testid="ioc-none">
                {t("intel.iocNone")}
              </p>
            ) : (
              <ul className="space-y-2">
                {ioc.result.iocs.map((it, i) => (
                  <li
                    key={i}
                    data-testid="ioc-item"
                    className="rounded-lg border border-metallic-silver/30 bg-surface p-3 text-sm"
                  >
                    <span className="rounded bg-bg/60 px-2 py-0.5 text-xs font-semibold uppercase">
                      {it.ioc_type}
                    </span>
                    <code className="ml-2">{it.display_value}</code>
                    <p className="mt-1 text-xs text-fg/70">{it.note}</p>
                  </li>
                ))}
              </ul>
            )}
            <p className="text-xs text-fg/60">{ioc.result.note}</p>
          </div>
        )}
      </section>
    </div>
  );
}
