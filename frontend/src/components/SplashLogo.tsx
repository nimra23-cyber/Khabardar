/**
 * SplashLogo: renders the official KHABARDAR logo with a load-failure fallback.
 *
 * - Loads the EXACT supplied asset from `/assets/logo.png` (served from
 *   `public/assets/`). The artwork is never regenerated, recolored, or
 *   distorted; it is displayed as-is with its aspect ratio preserved.
 * - If the asset is absent or fails to load, `onError` flips to a text-only
 *   fallback (Req 1.8). The caller's transition timer is unaffected.
 */
import { useState } from "react";

// Single source of truth for the logo path. If the supplied asset is an SVG,
// change this to "/assets/logo.svg".
export const LOGO_SRC = "/assets/Khabardar_Logo.png";

interface SplashLogoProps {
  /** Accessible name for the logo image. */
  alt: string;
  /** Called if the logo asset fails to load (for tests/observability). */
  onLogoError?: () => void;
}

export function SplashLogo({ alt, onLogoError }: SplashLogoProps) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    // Text-only fallback: no image. The name + tagline are rendered by the
    // Splash page itself, so here we render nothing (avoids a broken-image
    // icon) while still occupying the centered layout slot.
    return <div data-testid="splash-logo-fallback" aria-hidden="true" />;
  }

  return (
    <img
      src={LOGO_SRC}
      alt={alt}
      data-testid="splash-logo-img"
      // Preserve aspect ratio; never clip. Bound by viewport so it stays fully
      // visible from 320px to very large screens.
      className="block h-auto w-auto max-h-[40vh] max-w-[80vw] object-contain"
      onError={() => {
        setFailed(true);
        onLogoError?.();
      }}
    />
  );
}
