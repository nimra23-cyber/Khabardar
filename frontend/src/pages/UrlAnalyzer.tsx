/**
 * URL Analyzer page (Phase 3): submit a URL -> real backend local heuristic
 * analysis -> risk score, indicators, recommended action, honest "unavailable"
 * integration states, and a security-blocked state for private/metadata hosts.
 *
 * No URL is ever fetched/opened by the frontend; the backend performs local
 * analysis only. Input is preserved on error (Req 22.7). Content is rendered
 * as text.
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
      <h1 className="mb-1 text-2xl font-semibold">{t("nav.url")}</h1>
      <p className="mb-4 text-sm text-fg/80">{t("url.subtitle")}</p>

      <form onSubmit={onSubmit} className="space-y-3">
        <label htmlFor="url-input" className="block text-sm font-medium">
          {t("url.inputLabel")}
        </label>
        <input
          id="url-input"
          data-testid="url-input"
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/login"
          className="w-full rounded-lg border border-metallic-silver/30 bg-surface p-3 text-fg focus:border-accent focus:outline-none"
        />
        <div className="flex justify-end">
          <button
            type="submit"
            data-testid="url-submit"
            disabled={!canSubmit}
            className="rounded-lg bg-accent px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? t("url.analyzing") : t("url.analyze")}
          </button>
        </div>
      </form>

      {error && (
        <div
          data-testid="url-error"
          role="alert"
          className="mt-4 rounded-lg border border-danger/40 bg-danger/10 p-3 text-sm text-danger"
        >
          {error.message}
        </div>
      )}

      {result && (
        <section data-testid="url-result" className="mt-6 space-y-4">
          <RiskBadge score={result.risk_score} classification={result.classification} />

          <div className="text-sm">
            <span className="font-semibold">{t("url.domain")}: </span>
            <span data-testid="url-domain">{result.domain}</span>
          </div>

          {result.blocked && (
            <div
              data-testid="url-blocked"
              role="status"
              className="rounded-lg border border-danger/40 bg-danger/10 p-3 text-sm text-danger"
            >
              {t("url.blocked")}
            </div>
          )}

          <div className="text-sm">
            <span className="font-semibold">{t("url.recommended")}: </span>
            <span data-testid="url-action">{result.recommended_action}</span>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold">{t("url.indicators")}</h2>
            {result.indicators.length > 0 ? (
              <ul data-testid="url-indicators" className="space-y-2">
                {result.indicators.map((ind) => (
                  <li
                    key={ind.id}
                    data-testid={`url-ind-${ind.id}`}
                    className="rounded-lg border border-metallic-silver/30 bg-surface p-3 text-sm"
                  >
                    <span className="font-medium">{ind.name}</span>
                    <code className="ml-2 rounded bg-bg/60 px-1 py-0.5 text-xs">
                      {ind.evidence}
                    </code>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-fg/70" data-testid="url-no-indicators">
                {t("url.noIndicators")}
              </p>
            )}
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold">{t("url.integrations")}</h2>
            <ul className="flex flex-wrap gap-2" data-testid="url-integrations">
              {Object.entries(result.integration_states).map(([name, state]) => (
                <li
                  key={name}
                  className="rounded border border-metallic-silver/30 bg-surface px-2 py-1 text-xs opacity-70"
                >
                  {name}: <span className="font-medium">{state}</span>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-sm text-fg/80">{result.explanation_en}</p>
          <p className="text-xs text-fg/50">
            {t("detector.ruleset")}: {result.ruleset_version}
          </p>
        </section>
      )}
    </div>
  );
}
