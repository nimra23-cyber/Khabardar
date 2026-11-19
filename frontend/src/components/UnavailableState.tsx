/**
 * UnavailableState: honest "not yet available" panel (Req 22.1 / 22.6).
 * Premium empty-state styling with icon, not fake-functional.
 */
import { useTranslation } from "react-i18next";

interface UnavailableStateProps {
  title: string;
  variant: "scope-b" | "not-implemented";
}

export function UnavailableState({ title, variant }: UnavailableStateProps) {
  const { t } = useTranslation();
  const isScopeB = variant === "scope-b";
  const message = isScopeB ? t("unavailable.scopeB") : t("unavailable.notImplemented");

  return (
    <section
      data-testid={isScopeB ? "scope-b-unavailable" : "not-implemented"}
      className="mx-auto max-w-lg rounded-lg border border-border-subtle bg-surface p-8 text-center shadow-card"
      aria-live="polite"
    >
      <div className="mx-auto mb-4 inline-flex rounded-lg bg-accent/10 p-3 text-accent">
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d={isScopeB
            ? "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            : "M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"} />
        </svg>
      </div>
      <h1 className="mb-2 text-xl font-semibold text-fg">{title}</h1>
      <p className="mb-4 text-sm text-fg/60">{message}</p>
      {isScopeB && (
        <button
          type="button"
          disabled
          aria-disabled="true"
          data-testid="disabled-action"
          className="cursor-not-allowed rounded-lg border border-border-default bg-surface px-4 py-2 text-sm text-fg/40 opacity-60"
        >
          {t("unavailable.disabledAction")}
        </button>
      )}
    </section>
  );
}
