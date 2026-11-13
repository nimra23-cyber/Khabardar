/**
 * Splash: the dedicated branded entry screen (Req 1).
 *
 * Shows ONLY the official logo, the name "KHABARDAR", and the tagline
 * "Think Before You Trust" on a full-screen Deep Navy background, centered.
 * Plays a subtle entrance animation (300-800ms) and auto-advances to the main
 * application after ~2 seconds via `onDone`. No navigation, buttons, forms, or
 * footer. The logo-load-error fallback (Req 1.8) renders name + tagline only
 * and does NOT affect the transition timer.
 *
 * Accessibility: respects `prefers-reduced-motion` (the entrance animation is
 * disabled, but the 2-second transition still occurs).
 */
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { SplashLogo } from "../components/SplashLogo";

/** How long the splash is shown before transitioning (Req 1.5). */
export const SPLASH_DURATION_MS = 2000;

interface SplashProps {
  /** Called once after SPLASH_DURATION_MS to advance to the main app. */
  onDone: () => void;
}

export default function Splash({ onDone }: SplashProps) {
  const { t } = useTranslation();

  useEffect(() => {
    const timer = window.setTimeout(onDone, SPLASH_DURATION_MS);
    // Timer cleanup on unmount to avoid state updates after unmount.
    return () => window.clearTimeout(timer);
  }, [onDone]);

  return (
    <div
      data-testid="splash-screen"
      // Full-screen Deep Navy background via the existing design token; content
      // centered horizontally and vertically. The splash forces its own dark
      // brand backdrop regardless of the active theme.
      className="fixed inset-0 flex flex-col items-center justify-center gap-6 bg-deep-navy text-metallic-silver"
    >
      <div className="splash-enter flex flex-col items-center gap-4 px-4 text-center">
        <SplashLogo alt={t("app.name")} />
        {/* Brand name is a fixed token (never translated); bdi keeps the Latin
            brand rendering correct inside an RTL document. */}
        <bdi dir="ltr" className="text-3xl font-semibold tracking-wide">
          {t("app.name")}
        </bdi>
        <p className="text-base text-metallic-silver/80">{t("app.tagline")}</p>
      </div>
    </div>
  );
}
