/**
 * Scam Detector: premium textarea + animated risk badge + signal cards.
 * Preserves all testids and API integration.
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { RiskBadge } from "../components/RiskBadge";
import { SignalList } from "../components/SignalList";
import { useScanDetect } from "../hooks/useScanDetect";

const MAX_CHARS = 10000;

export default function Detector() {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const { loading, result, error, detect } = useScanDetect();

  const canSubmit = text.trim().length >= 1 && text.length <= MAX_CHARS && !loading;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    await detect(text);
  }

  return (
    <div data-testid="page-detector" className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">{t("nav.detector")}</h1>
        <p className="mt-1 text-sm text-fg/60">{t("detector.subtitle")}</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-3">
        <textarea
          id="scam-text"
          data-testid="detector-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          maxLength={MAX_CHARS}
          dir="auto"
          placeholder={t("detector.placeholder")}
          className="w-full rounded-lg border border-border-default bg-surface p-4 text-fg shadow-card transition-base placeholder:text-fg/30 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-fg/40">{text.length} / {MAX_CHARS}</span>
          <button
            type="submit"
            data-testid="detector-submit"
            disabled={!canSubmit}
            className="rounded-lg bg-accent px-6 py-2.5 font-medium text-white shadow-card transition-base hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.25" />
                  <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                {t("detector.analyzing")}
              </span>
            ) : t("detector.analyze")}
          </button>
        </div>
      </form>

      {error && (
        <div data-testid="detector-error" role="alert"
          className="mt-4 flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error.message}
        </div>
      )}

      {result && (
        <section data-testid="detector-result" className="mt-6 space-y-5">
          <RiskBadge score={result.risk_score} classification={result.classification} />

          {result.category && (
            <div className="flex items-center gap-2 text-sm">
              <span className="rounded-md border border-border-subtle bg-surface px-2.5 py-1 text-xs font-medium">
                {t("detector.category")}: <span data-testid="detector-category" className="text-accent">{result.category}</span>
              </span>
            </div>
          )}

          {result.no_signals_detected && result.no_signal_notice && (
            <div data-testid="no-signal-notice" role="status"
              className="flex items-center gap-2 rounded-lg border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
              <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {result.no_signal_notice}
            </div>
          )}

          {result.save_error && (
            <div data-testid="save-error" className="rounded-lg border border-warning/30 bg-warning/10 p-2 text-xs text-warning">
              {t("detector.saveError")}
            </div>
          )}

          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("detector.signalsTitle")}</h2>
            {result.signals.length > 0 ? (
              <SignalList signals={result.signals} />
            ) : (
              <p className="text-sm text-fg/50" data-testid="no-signals">{t("detector.noSignals")}</p>
            )}
          </div>

          <div className="grid gap-4 tablet:grid-cols-2">
            <div className="rounded-lg border border-border-subtle bg-surface p-4 shadow-card">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-fg/50">{t("detector.explanationEn")}</h3>
              <p className="text-sm text-fg/80" data-testid="explanation-en">{result.explanation_en}</p>
            </div>
            <div className="rounded-lg border border-border-subtle bg-surface p-4 shadow-card">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-fg/50">{t("detector.explanationUr")}</h3>
              <p className="text-sm text-fg/80" dir="rtl" lang="ur" data-testid="explanation-ur">{result.explanation_ur}</p>
            </div>
          </div>

          <p className="text-xs text-fg/40">{t("detector.ruleset")}: {result.ruleset_version}</p>
        </section>
      )}
    </div>
  );
}
