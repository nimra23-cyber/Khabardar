/**
 * Tailwind configuration for KHABARDAR.
 *
 * Colors are NOT hardcoded here. They reference the centralized CSS variables
 * defined once in `src/styles/tokens.css`, so there is a single source of truth
 * for the palette and themes can re-map the same tokens.
 *
 * Breakpoints match the design exactly:
 *   mobile  <= 767px   (base, no min-width prefix)
 *   tablet  768-1023px (`tablet:` -> min-width 768px)
 *   desktop >= 1024px  (`desktop:` -> min-width 1024px)
 */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    // Custom breakpoints per the Task 1.4 spec (replacing Tailwind defaults so
    // only the three specified ranges exist).
    screens: {
      tablet: "768px",
      desktop: "1024px",
    },
    extend: {
      colors: {
        // Brand / surface palette -> CSS variables (single source of truth).
        "deep-navy": "var(--color-deep-navy)",
        "midnight-blue": "var(--color-midnight-blue)",
        "metallic-silver": "var(--color-metallic-silver)",
        "electric-blue": "var(--color-electric-blue)",
        "surface-light": "var(--color-surface-light)",
        "surface-dark": "var(--color-surface-dark)",
        // Risk severity colors.
        danger: "var(--color-danger)",
        warning: "var(--color-warning)",
        safe: "var(--color-safe)",
        // Semantic, theme-aware tokens.
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        fg: "var(--color-fg)",
        accent: "var(--color-accent)",
      },
    },
  },
  plugins: [],
};
