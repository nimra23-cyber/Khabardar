/**
 * Scan History: premium table + empty state.
 * Preserves all testids and API integration.
 */
import { useTranslation } from "react-i18next";

import { useHistory } from "../hooks/useHistory";

export default function History() {
  const { t } = useTranslation();
  const { data, loading, error } = useHistory();

  return (
    <div data-testid="page-history" className="mx-auto max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">{t("history.title")}</h1>
        <p className="mt-1 text-sm text-fg/60">{t("history.subtitle")}</p>
      </div>

      {loading && (
        <div className="space-y-2">
          {[0, 1, 2].map(i => <div key={i} className="h-12 skeleton" />)}
        </div>
      )}

      {error && (
        <div role="alert" data-testid="history-error"
          className="flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {error.message}
        </div>
      )}

      {!loading && !error && data && data.count === 0 && (
        <div data-testid="history-empty"
          className="rounded-lg border border-border-subtle bg-surface p-8 text-center shadow-card">
          <svg className="mx-auto mb-3 h-10 w-10 text-fg/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-sm text-fg/50">{t("history.empty")}</p>
        </div>
      )}

      {!loading && !error && data && data.count > 0 && (
        <div className="overflow-x-auto rounded-lg border border-border-subtle shadow-card">
          <table className="w-full text-left text-sm">
            <thead className="bg-surface">
              <tr className="border-b border-border-subtle">
                <th className="p-3 text-xs font-semibold uppercase tracking-wider text-fg/50">{t("history.colContent")}</th>
                <th className="p-3 text-xs font-semibold uppercase tracking-wider text-fg/50">{t("history.colScore")}</th>
                <th className="p-3 text-xs font-semibold uppercase tracking-wider text-fg/50">{t("history.colClass")}</th>
                <th className="p-3 text-xs font-semibold uppercase tracking-wider text-fg/50">{t("history.colWhen")}</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((it) => (
                <tr key={it.id} data-testid="history-row" className="border-b border-border-subtle transition-base hover:bg-surface-hover">
                  <td className="max-w-xs truncate p-3 text-fg/70" title={it.masked_content ?? ""}>{it.masked_content ?? ""}</td>
                  <td className="p-3 tabular-nums text-fg/80">{it.risk_score ?? "-"}</td>
                  <td className="p-3">{it.classification ?? "-"}</td>
                  <td className="p-3 text-xs text-fg/40">{it.created_at ? new Date(it.created_at).toLocaleString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
