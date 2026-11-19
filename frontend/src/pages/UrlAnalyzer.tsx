/**
 * URL Analyzer: premium input + risk badge + indicator cards + integration badges.
 * Preserves all testids and API integration.
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { RiskBadge } from "../components/RiskBadge";
import { useUrlAnalyze } from "../hooks/useUrlAnalyze";

export default function UrlAnalyzer() {
  const { t } = useTranslation();
  const [url, setUrl] = useState("");
  const { loading, result, error, analyze } = useUrlAnalyze();
  const canSubmit = url.trim().length >= 1 && !loading;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    await analyze(url);
  }

  return (
    <div data-testid="page-url" className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">{t("nav.url")}</h1>
        <p className="mt-1 text-sm text-fg/60">{t("url.subtitle")}</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-3">
        <input
          id="url-input"
          data-testid="url-input"
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/login"
          className="w-full rounded-lg border border-border-default bg-surface p-3 font-mono text-sm text-fg shadow-card transition-base placeholder:text-fg/30 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <div className="flex justify-end">
          <button type="submit" data-testid="url-submit" disabled={!canSubmit}
            className="rounded-lg bg-accent px-6 py-2.5 font-medium text-white shadow-card transition-base hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40">
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.25" />
                  <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                {t("url.analyzing")}
              </span>
            ) : t("url.analyze")}
          </button>
        </div>
      </form>

      {error && (
        <div data-testid="url-error" role="alert"
          className="mt-4 flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error.message}
        </div>
      )}

      {result && (
        <section data-testid="url-result" className="mt-6 space-y-5">
          <RiskBadge score={result.risk_score} classification={result.classification} />

          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold text-fg/50">{t("url.domain")}:</span>
            <span className="rounded-md border border-border-subtle bg-surface px-2.5 py-1 font-mono text-xs text-fg/80" data-testid="url-domain">{result.domain}</span>
            <span className="font-semibold text-fg/50 ml-2">{t("url.recommended")}:</span>
            <span className="rounded-md border border-border-subtle bg-surface px-2.5 py-1 text-xs text-fg/80" data-testid="url-action">{result.recommended_action}</span>
          </div>

          {result.blocked && (
            <div data-testid="url-blocked" role="status"
              className="flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
              <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 0L5.636 18.364" />
              </svg>
              {t("url.blocked")}
            </div>
          )}

          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("url.indicators")}</h2>
            {result.indicators.length > 0 ? (
              <ul data-testid="url-indicators" className="space-y-2">
                {result.indicators.map((ind) => (
                  <li key={ind.id} data-testid={`url-ind-${ind.id}`}
                    className="card-hover flex items-center justify-between rounded-lg border border-border-subtle bg-surface p-3 shadow-card">
                    <span className="font-medium text-fg">{ind.name}</span>
                    <code className="rounded border border-border-subtle bg-bg/40 px-2 py-0.5 text-xs text-fg/60">{ind.evidence}</code>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-fg/50" data-testid="url-no-indicators">{t("url.noIndicators")}</p>
            )}
          </div>

          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("url.integrations")}</h2>
            <div className="flex flex-wrap gap-2" data-testid="url-integrations">
              {Object.entries(result.integration_states).map(([name, state]) => (
                <span key={name} className="inline-flex items-center gap-1.5 rounded-md border border-border-subtle bg-surface px-2.5 py-1 text-xs text-fg/50">
                  <span className="h-1.5 w-1.5 rounded-full bg-fg/30" />
                  {name}: <span className="font-medium text-fg/70">{state}</span>
                </span>
              ))}
            </div>
          </div>

          <p className="text-sm text-fg/60">{result.explanation_en}</p>
          <p className="text-xs text-fg/40">{t("detector.ruleset")}: {result.ruleset_version}</p>
        </section>
      )}
    </div>
  );
}
