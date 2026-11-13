/**
 * Scanner page (Req 12): upload an image → OCR + QR decode + URL extraction
 * → scam analysis + URL analysis.
 *
 * Security/UX:
 * - Input file is preserved on error (not cleared).
 * - QR decoded URLs are NEVER auto-opened or fetched — displayed as text only.
 * - All backend content rendered as TEXT (JSX escaping), never innerHTML.
 * - File validated client-side before upload (type + size).
 */
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { RiskBadge } from "../components/RiskBadge";
import { SignalList } from "../components/SignalList";
import { useMediaScan } from "../hooks/useMediaScan";
import type { URLAnalysisResult } from "../lib/types";

const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10 MB
const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/webp"];

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

    // Client-side validation — type check.
    if (!ACCEPTED_TYPES.includes(f.type)) {
      setClientError(t("scanner.invalidFile"));
      setFile(null);
      setPreviewUrl(null);
      return;
    }

    // Client-side validation — size check.
    if (f.size > MAX_FILE_BYTES) {
      setClientError(t("scanner.fileTooLarge"));
      setFile(null);
      setPreviewUrl(null);
      return;
    }

    // Revoke previous preview URL to avoid memory leak.
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || loading) return;
    setClientError(null);
    await scan(file);
    // Input (file) is NOT cleared — preserved on success or error.
  }

  const canSubmit = !!file && !loading;

  return (
    <div data-testid="page-scanner" className="mx-auto max-w-2xl">
      <h1 className="mb-1 text-2xl font-semibold">{t("nav.scanner")}</h1>
      <p className="mb-4 text-sm text-fg/80">{t("scanner.subtitle")}</p>

      <form onSubmit={onSubmit} className="space-y-4">
        {/* File input */}
        <div>
          <label
            htmlFor="scanner-file"
            className="block text-sm font-medium mb-1"
          >
            {t("scanner.selectImage")}
          </label>
          <input
            ref={fileInputRef}
            id="scanner-file"
            data-testid="scanner-file-input"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={onFileChange}
            className="block w-full text-sm text-fg file:mr-3 file:rounded file:border-0 file:bg-accent file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white hover:file:bg-accent/90 cursor-pointer"
          />
        </div>

        {/* Image preview */}
        {previewUrl && (
          <div>
            <p className="mb-1 text-xs text-fg/60">{t("scanner.preview")}</p>
            <img
              src={previewUrl}
              alt={t("scanner.preview")}
              data-testid="scanner-preview"
              className="max-h-64 rounded-lg border border-metallic-silver/30 object-contain"
            />
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          data-testid="scanner-submit"
          disabled={!canSubmit}
          className="rounded-lg bg-accent px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? t("scanner.analyzing") : t("scanner.analyze")}
        </button>
      </form>

      {/* Client-side validation error */}
      {clientError && (
        <div
          data-testid="scanner-client-error"
          role="alert"
          className="mt-4 rounded-lg border border-danger/40 bg-danger/10 p-3 text-sm text-danger"
        >
          {clientError}
        </div>
      )}

      {/* Server error */}
      {error && (
        <div
          data-testid="scanner-error"
          role="alert"
          className="mt-4 rounded-lg border border-danger/40 bg-danger/10 p-3 text-sm text-danger"
        >
          {error.message}
        </div>
      )}

      {/* Results */}
      {result && (
        <section data-testid="scanner-result" className="mt-6 space-y-6">

          {/* OCR Text */}
          <div className="rounded-lg border border-metallic-silver/30 bg-surface p-4">
            <h2 className="mb-2 text-lg font-semibold">{t("scanner.ocrTitle")}</h2>
            {!result.ocr.available ? (
              <p className="text-sm text-fg/60" data-testid="ocr-unavailable">
                {t("scanner.ocrUnavailable")}
              </p>
            ) : result.ocr.text ? (
              <pre
                data-testid="ocr-text"
                className="whitespace-pre-wrap break-words text-sm font-mono bg-bg rounded p-2"
              >
                {result.ocr.text}
              </pre>
            ) : (
              <p className="text-sm text-fg/60" data-testid="ocr-no-text">
                {t("scanner.noText")}
              </p>
            )}
          </div>

          {/* QR Code Values */}
          <div className="rounded-lg border border-metallic-silver/30 bg-surface p-4">
            <h2 className="mb-2 text-lg font-semibold">{t("scanner.qrTitle")}</h2>
            {!result.qr.available ? (
              <p className="text-sm text-fg/60" data-testid="qr-unavailable">
                {t("scanner.qrUnavailable")}
              </p>
            ) : result.qr.values.length > 0 ? (
              <ul data-testid="qr-values" className="space-y-2">
                {result.qr.values.map((v, i) => (
                  <li
                    key={i}
                    className="rounded border border-metallic-silver/20 bg-bg px-3 py-2 text-sm font-mono break-all"
                    data-testid={`qr-value-${i}`}
                  >
                    {/* Never auto-open — displayed as plain text */}
                    {v}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-fg/60" data-testid="qr-no-values">
                {t("scanner.noQr")}
              </p>
            )}
          </div>

          {/* URLs Found */}
          <div className="rounded-lg border border-metallic-silver/30 bg-surface p-4">
            <h2 className="mb-2 text-lg font-semibold">{t("scanner.urlsTitle")}</h2>
            {result.urls_found.length > 0 ? (
              <ul data-testid="urls-found" className="space-y-2">
                {result.urls_found.map((url, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="text-sm font-mono break-all flex-1" data-testid={`url-found-${i}`}>
                      {url}
                    </span>
                    {/* Link to URL Analyzer — NOT auto-fetch */}
                    <Link
                      to={`/url?q=${encodeURIComponent(url)}`}
                      className="shrink-0 text-xs text-accent underline hover:no-underline"
                      aria-label={`${t("scanner.openInAnalyzer")}: ${url}`}
                    >
                      {t("scanner.openInAnalyzer")}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-fg/60" data-testid="no-urls">
                {t("scanner.noUrls")}
              </p>
            )}
          </div>

          {/* Text Scam Analysis */}
          {result.text_analysis && (
            <div className="rounded-lg border border-metallic-silver/30 bg-surface p-4">
              <h2 className="mb-3 text-lg font-semibold">{t("scanner.textAnalysis")}</h2>
              <RiskBadge
                score={result.text_analysis.risk_score}
                classification={result.text_analysis.classification}
              />
              {result.text_analysis.signals.length > 0 && (
                <div className="mt-3">
                  <SignalList signals={result.text_analysis.signals} />
                </div>
              )}
            </div>
          )}

          {/* URL Analyses */}
          {result.url_analyses.length > 0 && (
            <div className="rounded-lg border border-metallic-silver/30 bg-surface p-4">
              <h2 className="mb-3 text-lg font-semibold">{t("scanner.urlAnalysis")}</h2>
              <div className="space-y-3">
                {result.url_analyses.map((analysis, i) => {
                  if (!("valid" in analysis) || analysis.valid === false) {
                    return (
                      <div
                        key={i}
                        className="rounded border border-metallic-silver/20 p-3 text-sm"
                      >
                        <span className="text-fg/60">
                          {result.urls_found[i]}: invalid URL
                        </span>
                      </div>
                    );
                  }
                  const a = analysis as unknown as URLAnalysisResult;
                  return (
                    <div
                      key={i}
                      data-testid={`url-analysis-${i}`}
                      className="rounded border border-metallic-silver/20 p-3"
                    >
                      <p className="mb-2 text-xs font-mono break-all text-fg/70">{a.url}</p>
                      <RiskBadge score={a.risk_score} classification={a.classification} />
                      {a.blocked && (
                        <p className="mt-2 text-xs text-danger" data-testid={`url-blocked-${i}`}>
                          {t("url.blocked")}
                        </p>
                      )}
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
