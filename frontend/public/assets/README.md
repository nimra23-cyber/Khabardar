# Brand assets

Place the **official KHABARDAR logo** here as:

    frontend/public/assets/logo.png

Requirements (do not alter the supplied artwork):
- Use the exact supplied asset — do not regenerate, redesign, recolor, or distort it.
- The splash screen loads it from the web path `/assets/logo.png` (Vite serves
  everything under `public/` at the site root).
- If this file is absent or fails to load, the splash falls back to the name
  "KHABARDAR" + tagline on the Deep Navy background (Req 1.8) and still
  auto-advances after ~2 seconds. The real logo appears automatically once the
  file is present — no code change needed.

If the supplied asset is an SVG instead of PNG, save it as `logo.svg` and update
the single `LOGO_SRC` constant in `frontend/src/components/SplashLogo.tsx`.
