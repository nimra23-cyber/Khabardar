/**
 * Reports page (Phase 6): analyze a message, then generate a downloadable
 * report from the REAL detection result (/api/reports/generate). The report
 * download is a real file built from the backend response — no fake success.
 * Privacy-safe: reformats data the user already received; persists nothing.
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
      <h1 className="mb-1 text-2xl font-semibold">{t("nav.reports")}</h1>
      <p className="mb-4 text-sm text-fg/80">{t("reports.subtitle")}</p>

      <form onSubmit={onAnalyze} className="space-y-3">
        <textarea
          data-testid="reports-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
          dir="auto"
          className="w-full rounded-lg border border-metallic-silver/30 bg-surface p-3 text-fg focus:border-accent focus:outline-none"
          placeholder={t("reports.placeholder")}
        />
        <div className="flex justify-end">
          <button
            type="submit"
            data-testid="reports-analyze"
            disabled={text.trim().length < 1 || loading}
            className="rounded-lg bg-accent px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? t("reports.analyzing") : t("reports.analyze")}
          </button>
        </div>
      </form>

      {error && (
        <div role="alert" className="mt-4 text-sm text-danger" data-testid="reports-error">
          {error.message}
        </div>
      )}

      {result && (
        <div data-testid="reports-result" className="mt-6 space-y-3">
          <p className="text-sm">
            {t("reports.analyzed")}: <strong>{result.classification}</strong> ({result.risk_score}/100)
          </p>
          <button
            type="button"
            data-testid="reports-generate"
            onClick={onGenerate}
            disabled={generating}
            className="rounded-lg border border-accent px-4 py-2 font-medium text-accent disabled:opacity-50"
          >
            {generating ? t("reports.generating") : t("reports.generate")}
          </button>
          {reportError && (
            <div role="alert" className="text-sm text-danger">{reportError}</div>
          )}
          {report && (
            <div data-testid="reports-download-block" className="space-y-2">
              <button
                type="button"
                data-testid="reports-download"
                onClick={onDownload}
                className="rounded-lg bg-safe px-4 py-2 font-medium text-white"
              >
                {t("reports.download")}
              </button>
              <pre
                data-testid="reports-preview"
                className="max-h-64 overflow-auto rounded-lg border border-metallic-silver/30 bg-surface p-3 text-xs"
              >
                {report.markdown}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
