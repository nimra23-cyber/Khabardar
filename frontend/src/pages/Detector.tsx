/**
 * Scam Detector page (Task 2.14): submit text -> real backend rule-based
 * detection -> display score/classification/signals/evidence/explanation.
 *
 * Security/UX: user input is preserved on error (never cleared until the user
 * changes it); all backend content is rendered as TEXT (JSX escaping), never
 * injected as HTML (Req 19.6, 22.7).
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

  const trimmedLen = text.trim().length;
  const canSubmit = trimmedLen >= 1 && text.length <= MAX_CHARS && !loading;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    await detect(text); // input is NOT cleared, preserved on success or error
  }

  return (
    <div data-testid="page-detector" className="mx-auto max-w-2xl">
      <h1 className="mb-1 text-2xl font-semibold">{t("nav.detector")}</h1>
      <p className="mb-4 text-sm text-fg/80">{t("detector.subtitle")}</p>

      <form onSubmit={onSubmit} className="space-y-3">
        <label htmlFor="scam-text" className="block text-sm font-medium">
          {t("detector.inputLabel")}
        </label>
        <textarea
          id="scam-text"
          data-testid="detector-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          maxLength={MAX_CHARS}
          dir="auto"
          placeholder={t("detector.placeholder")}
          className="w-full rounded-lg border border-metallic-silver/30 bg-surface p-3 text-fg focus:border-accent focus:outline-none"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-fg/60">
            {text.length} / {MAX_CHARS}
          </span>
          <button
            type="submit"
            data-testid="detector-submit"
            disabled={!canSubmit}
            className="rounded-lg bg-accent px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? t("detector.analyzing") : t("detector.analyze")}
          </button>
        </div>
      </form>

      {error && (
        <div
          data-testid="detector-error"
          role="alert"
          className="mt-4 rounded-lg border border-danger/40 bg-danger/10 p-3 text-sm text-danger"
        >
          {error.message}
        </div>
      )}

      {result && (
        <section data-testid="detector-result" className="mt-6 space-y-4">
          <RiskBadge score={result.risk_score} classification={result.classification} />

          {result.category && (
            <div className="text-sm">
              <span className="font-semibold">{t("detector.category")}: </span>
              <span data-testid="detector-category">{result.category}</span>
            </div>
          )}

          {result.no_signals_detected && result.no_signal_notice && (
            <div
              data-testid="no-signal-notice"
              role="status"
              className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm"
            >
              {result.no_signal_notice}
            </div>
          )}

          {result.save_error && (
            <div
              data-testid="save-error"
              className="rounded-lg border border-warning/40 bg-warning/10 p-2 text-xs"
            >
              {t("detector.saveError")}
            </div>
          )}

          <div>
            <h2 className="mb-2 text-lg font-semibold">
              {t("detector.signalsTitle")}
            </h2>
            {result.signals.length > 0 ? (
              <SignalList signals={result.signals} />
            ) : (
              <p className="text-sm text-fg/70" data-testid="no-signals">
                {t("detector.noSignals")}
              </p>
            )}
          </div>

          <div className="grid gap-4 tablet:grid-cols-2">
            <div className="rounded-lg border border-metallic-silver/30 bg-surface p-3">
              <h3 className="mb-1 text-sm font-semibold">
                {t("detector.explanationEn")}
              </h3>
              <p className="text-sm" data-testid="explanation-en">
                {result.explanation_en}
              </p>
            </div>
            <div className="rounded-lg border border-metallic-silver/30 bg-surface p-3">
              <h3 className="mb-1 text-sm font-semibold">
                {t("detector.explanationUr")}
              </h3>
              <p className="text-sm" dir="rtl" lang="ur" data-testid="explanation-ur">
                {result.explanation_ur}
              </p>
            </div>
          </div>

          <p className="text-xs text-fg/50">
            {t("detector.ruleset")}: {result.ruleset_version}
          </p>
        </section>
      )}
    </div>
  );
}
