/**
 * Scan History page (Task 6.7): lists the local user's recent analyses with
 * MASKED content only (sensitive values never shown raw). Empty account shows
 * an honest empty-state, not an error (Req 20.6). Content rendered as text.
 */
import { useTranslation } from "react-i18next";

import { useHistory } from "../hooks/useHistory";

export default function History() {
  const { t } = useTranslation();
  const { data, loading, error } = useHistory();

  return (
    <div data-testid="page-history" className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-2xl font-semibold">{t("history.title")}</h1>
      <p className="mb-4 text-sm text-fg/80">{t("history.subtitle")}</p>

      {loading && <p className="text-sm text-fg/60">…</p>}

      {error && (
        <div
          role="alert"
          data-testid="history-error"
          className="rounded-lg border border-danger/40 bg-danger/10 p-3 text-sm text-danger"
        >
          {error.message}
        </div>
      )}

      {!loading && !error && data && data.count === 0 && (
        <div
          data-testid="history-empty"
          className="rounded-lg border border-metallic-silver/30 bg-surface p-6 text-sm text-fg/70"
        >
          {t("history.empty")}
        </div>
      )}

      {!loading && !error && data && data.count > 0 && (
        <div className="overflow-x-auto rounded-lg border border-metallic-silver/30">
          <table className="w-full text-left text-sm">
            <thead className="bg-surface">
              <tr>
                <th className="p-3">{t("history.colContent")}</th>
                <th className="p-3">{t("history.colScore")}</th>
                <th className="p-3">{t("history.colClass")}</th>
                <th className="p-3">{t("history.colWhen")}</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((it) => (
                <tr
                  key={it.id}
                  data-testid="history-row"
                  className="border-t border-metallic-silver/20"
                >
                  <td className="max-w-xs truncate p-3" title={it.masked_content ?? ""}>
                    {it.masked_content ?? ""}
                  </td>
                  <td className="p-3 tabular-nums">{it.risk_score ?? "-"}</td>
                  <td className="p-3">{it.classification ?? "-"}</td>
                  <td className="p-3 text-xs text-fg/60">
                    {it.created_at ? new Date(it.created_at).toLocaleString() : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
