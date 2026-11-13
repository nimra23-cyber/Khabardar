/**
 * SignalList: renders triggered detection signals with their evidence.
 *
 * All attacker-controlled content (signal name, evidence) is rendered as TEXT
 * via JSX interpolation (React escapes it); never via dangerouslySetInnerHTML
 * (Req 19.6 / frontend security notes).
 */
import { useTranslation } from "react-i18next";

import type { DetectSignal } from "../lib/types";

export function SignalList({ signals }: { signals: DetectSignal[] }) {
  const { t } = useTranslation();
  if (signals.length === 0) return null;

  return (
    <ul data-testid="signal-list" className="space-y-3">
      {signals.map((s) => (
        <li
          key={s.signal_id}
          data-testid={`signal-${s.signal_id}`}
          className="rounded-lg border border-metallic-silver/30 bg-surface p-3"
        >
          <div className="font-medium">{s.name}</div>
          <p className="mt-1 text-sm text-fg/80">{s.explanation}</p>
          {s.evidence.length > 0 && (
            <p className="mt-2 text-xs text-fg/70">
              <span className="font-semibold">{t("detector.evidence")}: </span>
              {s.evidence.map((e, i) => (
                <code
                  key={i}
                  className="mx-0.5 rounded bg-bg/60 px-1 py-0.5"
                >
                  {e}
                </code>
              ))}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}
