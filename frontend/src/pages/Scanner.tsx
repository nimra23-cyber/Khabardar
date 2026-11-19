/**
 * Scanner: premium upload + preview + OCR/QR results.
 * Preserves all testids, API integration, and security properties.
 */
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { RiskBadge } from "../components/RiskBadge";
import { SignalList } from "../components/SignalList";
import { useMediaScan } from "../hooks/useMediaScan";
import type { URLAnalysisResult } from "../lib/types";

const MAX_FILE_BYTES = 10 * 1024 * 1024;
const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/webp"];

function SectionCard({ title, children, testId }: { title: string; children: React.ReactNode; testId?: string }) {
  return (
    <div className="rounded-lg border border-border-subtle bg-surface p-4 shadow-card">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-fg/50">{title}</h2>
      <div data-testid={testId}>{children}</div>
    </div>
  );
}

export default function Scanner() {
  const { t } = useTranslation();
  const { loading, result, error, scan } = useMediaScan();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [clientError, setClientError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setClientError(null);
    if (!ACCEPTED_TYPES.includes(f.type)) { setClientError(t("scanner.invalidFile")); setFile(null); setPreviewUrl(null); return; }
    if (f.size > MAX_FILE_BYTES) { setClientError(t("scanner.fileTooLarge")); setFile(null); setPreviewUrl(null); return; }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || loading) return;
    setClientError(null);
    await scan(file);
  }

  const canSubmit = !!file && !loading;

  return (
    <div data-testid="page-scanner" className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">{t("nav.scanner")}</h1>
        <p className="mt-1 text-sm text-fg/60">{t("scanner.subtitle")}</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label htmlFor="scanner-file" className="block text-sm font-medium text-fg/70">{t("scanner.selectImage")}</label>
          <input ref={fileInputRef} id="scanner-file" data-testid="scanner-file-input" type="file" accept="image/png,image/jpeg,image/webp" onChange={onFileChange}
            className="mt-1 block w-full text-sm text-fg/50 file:mr-3 file:rounded file:border-0 file:bg-accent file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white hover:file:bg-accent/90 cursor-pointer" />
        </div>
        {previewUrl && (
          <div>
            <p className="mb-1 text-xs text-fg/40">{t("scanner.preview")}</p>
            <img src={previewUrl} alt={t("scanner.preview")} data-testid="scanner-preview"
              className="max-h-64 rounded-lg border border-border-subtle object-contain shadow-card" />
          </div>
        )}
        <button type="submit" data-testid="scanner-submit" disabled={!canSubmit}
          className="rounded-lg bg-accent px-6 py-2.5 font-medium text-white shadow-card transition-base hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40">
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.25" /><path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
              {t("scanner.analyzing")}
            </span>
          ) : t("scanner.analyze")}
        </button>
      </form>

      {clientError && (
        <div data-testid="scanner-client-error" role="alert"
          className="mt-4 flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {clientError}
        </div>
      )}
      {error && (
        <div data-testid="scanner-error" role="alert"
          className="mt-4 flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {error.message}
        </div>
      )}

      {result && (
        <section data-testid="scanner-result" className="mt-6 space-y-4">
          <SectionCard title={t("scanner.ocrTitle")}>
            {!result.ocr.available ? <p className="text-sm text-fg/50" data-testid="ocr-unavailable">{t("scanner.ocrUnavailable")}</p>
            : result.ocr.text ? <pre data-testid="ocr-text" className="whitespace-pre-wrap break-words rounded border border-border-subtle bg-bg/40 p-3 font-mono text-sm text-fg/70">{result.ocr.text}</pre>
            : <p className="text-sm text-fg/50" data-testid="ocr-no-text">{t("scanner.noText")}</p>}
          </SectionCard>

          <SectionCard title={t("scanner.qrTitle")}>
            {!result.qr.available ? <p className="text-sm text-fg/50" data-testid="qr-unavailable">{t("scanner.qrUnavailable")}</p>
            : result.qr.values.length > 0 ? (
              <ul data-testid="qr-values" className="space-y-2">
                {result.qr.values.map((v, i) => (
                  <li key={i} className="rounded border border-border-subtle bg-bg/40 px-3 py-2 font-mono text-sm break-all text-fg/70" data-testid={`qr-value-${i}`}>{v}</li>
                ))}
              </ul>
            ) : <p className="text-sm text-fg/50" data-testid="qr-no-values">{t("scanner.noQr")}</p>}
          </SectionCard>

          <SectionCard title={t("scanner.urlsTitle")}>
            {result.urls_found.length > 0 ? (
              <ul data-testid="urls-found" className="space-y-2">
                {result.urls_found.map((url, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="flex-1 break-all font-mono text-sm text-fg/70" data-testid={`url-found-${i}`}>{url}</span>
                    <Link to={`/url?q=${encodeURIComponent(url)}`} className="shrink-0 text-xs text-accent underline hover:no-underline">{t("scanner.openInAnalyzer")}</Link>
                  </li>
                ))}
              </ul>
            ) : <p className="text-sm text-fg/50" data-testid="no-urls">{t("scanner.noUrls")}</p>}
          </SectionCard>

          {result.text_analysis && (
            <div className="rounded-lg border border-border-subtle bg-surface p-4 shadow-card">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("scanner.textAnalysis")}</h2>
              <RiskBadge score={result.text_analysis.risk_score} classification={result.text_analysis.classification} />
              {result.text_analysis.signals.length > 0 && <div className="mt-3"><SignalList signals={result.text_analysis.signals} /></div>}
            </div>
          )}

          {result.url_analyses.length > 0 && (
            <div className="rounded-lg border border-border-subtle bg-surface p-4 shadow-card">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-fg/50">{t("scanner.urlAnalysis")}</h2>
              <div className="space-y-3">
                {result.url_analyses.map((analysis, i) => {
                  if (!("valid" in analysis) || analysis.valid === false) {
                    return <div key={i} className="rounded border border-border-subtle p-3 text-sm text-fg/50">{result.urls_found[i]}: invalid URL</div>;
                  }
                  const a = analysis as unknown as URLAnalysisResult;
                  return (
                    <div key={i} data-testid={`url-analysis-${i}`} className="rounded border border-border-subtle p-3">
                      <p className="mb-2 break-all font-mono text-xs text-fg/50">{a.url}</p>
                      <RiskBadge score={a.risk_score} classification={a.classification} />
                      {a.blocked && <p className="mt-2 text-xs text-danger" data-testid={`url-blocked-${i}`}>{t("url.blocked")}</p>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
