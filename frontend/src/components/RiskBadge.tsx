/** RiskBadge: shows the risk score + classification with risk-state colors. */
import type { Classification } from "../lib/types";

const CLASS_STYLE: Record<Classification, string> = {
  SAFE: "bg-safe/15 text-safe border-safe/40",
  SUSPICIOUS: "bg-warning/15 text-warning border-warning/40",
  "HIGH RISK": "bg-danger/15 text-danger border-danger/40",
};

export function RiskBadge({
  score,
  classification,
}: {
  score: number;
  classification: Classification;
}) {
  return (
    <div
      data-testid="risk-badge"
      className={`inline-flex items-center gap-3 rounded-lg border px-4 py-3 ${CLASS_STYLE[classification]}`}
    >
      <span className="text-3xl font-bold tabular-nums" data-testid="risk-score">
        {score}
      </span>
      <span className="text-sm opacity-70">/ 100</span>
      <span className="ml-2 text-lg font-semibold" data-testid="risk-class">
        {classification}
      </span>
    </div>
  );
}
