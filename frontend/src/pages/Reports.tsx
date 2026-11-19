/**
 * Reports: premium report generation + download interface.
 * Preserves all testids and API integration.
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { apiPost } from "../lib/apiClient";
import { useScanDetect } from "../hooks/useScanDetect";
import type { ReportResult } from "../lib/types";

export default function Reports() {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const { loading, result, error, detect } = useScanDetect();
  const [report, setReport] = useState<ReportResult | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  async function onAnalyze(e: React.FormEvent) {
    e.preventDefault();
    setReport(null);
    setReportError(null);
    if (text.trim().length < 1) return;
    await detect(text);
  }

  async function onGenerate() {
    if (!result) return;
    setGenerating(true);
    setReportError(null);
    const res = await apiPost<ReportResult>("/api/reports/generate", {
      risk_score: result.risk_score,
      classification: result.classification,
      category: result.category,
      signals: result.signals,
      explanation_en: result.explanation_en,
      explanation_ur: result.explanation_ur,
      ruleset_version: result.ruleset_version,
    });
    setGenerating(false);
    if (res.ok) setReport(res.data);
    else setReportError(res.error.message);
  }

  function onDownload() {
    if (!report) return;
    const blob = new Blob([report.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = report.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <div data-testid="page-reports" className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">{t("nav.reports")}</h1>
        <p className="mt-1 text-sm text-fg/60">{t("reports.subtitle")}</p>
      </div>

      <form onSubmit={onAnalyze} className="space-y-3">
        <textarea
          data-testid="reports-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
          dir="auto"
          className="w-full rounded-lg border border-border-default bg-surface p-4 text-fg shadow-card transition-base placeholder:text-fg/30 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          placeholder={t("reports.placeholder")}
        />
        <div className="flex justify-end">
          <button type="submit" data-testid="reports-analyze" disabled={text.trim().length < 1 || loading}
            className="rounded-lg bg-accent px-6 py-2.5 font-medium text-white shadow-card transition-base hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40">
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.25" /><path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
                {t("reports.analyzing")}
              </span>
            ) : t("reports.analyze")}
          </button>
        </div>
      </form>

      {error && (
        <div role="alert" data-testid="reports-error" className="mt-4 flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {error.message}
        </div>
      )}

      {result && (
        <div data-testid="reports-result" className="mt-6 space-y-4">
          <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-surface p-4 shadow-card">
            <div>
              <p className="text-sm text-fg/60">{t("reports.analyzed")}</p>
              <p className="text-lg font-semibold text-fg"><strong>{result.classification}</strong> ({result.risk_score}/100)</p>
            </div>
            <button type="button" data-testid="reports-generate" onClick={onGenerate} disabled={generating}
              className="rounded-lg border border-accent px-4 py-2 text-sm font-medium text-accent transition-base hover:bg-accent/10 disabled:opacity-50">
              {generating ? t("reports.generating") : t("reports.generate")}
            </button>
          </div>
          {reportError && <div role="alert" className="rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">{reportError}</div>}
          {report && (
            <div data-testid="reports-download-block" className="space-y-3">
              <button type="button" data-testid="reports-download" onClick={onDownload}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-safe px-4 py-2.5 font-medium text-white shadow-card transition-base hover:brightness-110">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                {t("reports.download")}
              </button>
              <pre data-testid="reports-preview" className="max-h-64 overflow-auto rounded-lg border border-border-subtle bg-surface p-4 text-xs text-fg/70 shadow-card">
                {report.markdown}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
