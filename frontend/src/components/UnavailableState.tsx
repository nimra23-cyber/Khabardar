/**
 * UnavailableState: honest "not yet available" panel (Req 22.1 / 22.6).
 *
 * Two honest variants, neither ever fake-functional:
 * - variant="scope-b": an advanced (Scope B) capability that is intentionally
 *   not part of the MVP. Renders a genuinely DISABLED action control.
 * - variant="not-implemented": a page whose backend/functionality has not been
 *   built yet in this task; clearly states so.
 *
 * Uses semantic token utilities only (no hardcoded colors).
 */
import { useTranslation } from "react-i18next";

interface UnavailableStateProps {
  /** Translated title of the page/feature. */
  title: string;
  variant: "scope-b" | "not-implemented";
}

export function UnavailableState({ title, variant }: UnavailableStateProps) {
  const { t } = useTranslation();
  const isScopeB = variant === "scope-b";
  const message = isScopeB
    ? t("unavailable.scopeB")
    : t("unavailable.notImplemented");

  return (
    <section
      data-testid={isScopeB ? "scope-b-unavailable" : "not-implemented"}
      className="rounded-lg border border-metallic-silver/30 bg-surface p-6"
      aria-live="polite"
    >
      <h1 className="mb-2 text-xl font-semibold">{title}</h1>
      <p className="mb-4 text-sm">{message}</p>
      {isScopeB && (
        // A genuinely disabled control: it exists to show the capability is
        // planned, but cannot be invoked (Req 22.6).
        <button
          type="button"
          disabled
          aria-disabled="true"
          data-testid="disabled-action"
          className="cursor-not-allowed rounded border border-metallic-silver/30 bg-surface px-3 py-2 text-fg opacity-50"
        >
          {t("unavailable.disabledAction")}
        </button>
      )}
    </section>
  );
}
