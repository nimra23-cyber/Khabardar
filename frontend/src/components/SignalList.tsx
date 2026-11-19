/**
 * SignalList: renders triggered detection signals as professional cards.
 *
 * All attacker-controlled content is rendered as TEXT via JSX interpolation
 * (React escapes it); never via dangerouslySetInnerHTML (Req 19.6).
 */
import { useTranslation } from "react-i18next";

import type { DetectSignal } from "../lib/types";

export function SignalList({ signals }: { signals: DetectSignal[] }) {
  const { t } = useTranslation();
  if (signals.length === 0) return null;

  return (
    <ul data-testid="signal-list" className="space-y-2">
      {signals.map((s) => (
        <li
          key={s.signal_id}
          data-testid={`signal-${s.signal_id}`}
          className="card-hover rounded-lg border border-border-subtle bg-surface p-3 shadow-card"
        >
          <div className="flex items-start gap-2">
            <svg className="mt-0.5 h-4 w-4 shrink-0 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="min-w-0 flex-1">
              <div className="font-medium text-fg">{s.name}</div>
              <p className="mt-0.5 text-sm text-fg/60">{s.explanation}</p>
              {s.evidence.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  <span className="text-xs font-medium text-fg/50">{t("detector.evidence")}:</span>
                  {s.evidence.map((e, i) => (
                    <code
                      key={i}
                      className="rounded border border-border-subtle bg-bg/40 px-1.5 py-0.5 text-xs text-fg/70"
                    >
                      {e}
                    </code>
                  ))}
                </div>
              )}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
