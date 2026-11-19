/**
 * RiskBadge: premium score gauge with classification badge.
 * Circular SVG ring shows the score visually; color-coded by risk level.
 */
import type { Classification } from "../lib/types";

const CLASS_COLOR: Record<Classification, string> = {
  SAFE: "var(--color-safe)",
  SUSPICIOUS: "var(--color-warning)",
  "HIGH RISK": "var(--color-danger)",
};

const CLASS_STYLE: Record<Classification, string> = {
  SAFE: "bg-safe/10 text-safe border-safe/30",
  SUSPICIOUS: "bg-warning/10 text-warning border-warning/30",
  "HIGH RISK": "bg-danger/10 text-danger border-danger/30",
};

const RADIUS = 45;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function RiskBadge({
  score,
  classification,
}: {
  score: number;
  classification: Classification;
}) {
  const color = CLASS_COLOR[classification];
  const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE;

  return (
    <div
      data-testid="risk-badge"
      className="inline-flex items-center gap-4 rounded-lg border border-border-subtle bg-surface p-4 shadow-card"
    >
      {/* Circular score gauge */}
      <div className="relative h-20 w-20">
        <svg className="h-20 w-20 -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r={RADIUS}
            fill="none"
            stroke="var(--color-border-default)"
            strokeWidth="6"
          />
          <circle
            cx="50"
            cy="50"
            r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            className="score-ring-fill"
            style={{ strokeDashoffset: offset }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold tabular-nums text-fg" data-testid="risk-score">
            {score}
          </span>
        </div>
      </div>
      <div className="flex flex-col">
        <span className="text-xs text-fg/50">/ 100</span>
        <span
          className={`mt-1 inline-block rounded-md border px-2.5 py-1 text-sm font-semibold ${CLASS_STYLE[classification]}`}
          data-testid="risk-class"
        >
          {classification}
        </span>
      </div>
    </div>
  );
}
